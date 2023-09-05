import sys
import os
import urllib.request
import boto3
import yaml
import cfnresponse

from pip._internal import main

# Install required package
main(['install', '-I', '-q', 'pyyaml', '--target', '/tmp/', '--no-cache-dir', '--disable-pip-version-check'])
sys.path.insert(0, '/tmp/')


def lambda_handler(event, context):
    CONFIG_BUCKET = os.getenv('CONFIG_BUCKET_NAME')
    CONFIG_FILE = os.getenv('CONFIG_FILENAME')
    ENV = os.getenv('DEPLOYED_ENV')

    print(event)

    s3 = boto3.client('s3')
    s3_res = boto3.resource('s3')

    def upload_folder_structure(bucket_name, folder_structure):
        try:
            # Check if the bucket exists
            s3.head_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} already exists.")
        except Exception as e:
            # Create the bucket
            s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} created successfully.")

        # Create the folder structure inside the bucket
        for folder_name, folder_path in folder_structure[0].items():
            s3.put_object(Bucket=bucket_name, Key=folder_path + '/')

    def bucket_upload():
        try:
            obj = s3_res.Object(CONFIG_BUCKET, CONFIG_FILE)
            response = obj.get()
            file_contents = response['Body'].read().decode('utf-8')
            data = yaml.safe_load(file_contents)

            for entry in data.get(ENV, []):
                for bucket_name, folder_structure in entry.items():
                    upload_folder_structure(bucket_name, folder_structure)
        except Exception as e:
            error_message = str(e)
            print(f"Error creating bucket: {error_message}")
            response_data = {'Data': 120}
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, 'LambdaFunctionInvoke')
            return error_message

    if event:
        try:
            bucket_upload()
            response_data = {'Data': 120}
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, 'LambdaFunctionInvoke')
            return {
                'statusCode': 200,
                'body': 'Buckets Created & Folders Uploaded successfully'
            }
        except Exception as e:
            error_message = str(e)
            response_data = {'Data': 120}
            cfnresponse.send(event, context, cfnresponse.SUCCESS, response_data, 'LambdaFunctionInvoke')
            return error_message

    if not event:
        try:
            print('No Event Passed. Invoked by pipeline')
            bucket_upload()
        except Exception as e:
            error_message = str(e)
            return error_message
