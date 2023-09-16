import os
import json
import boto3

# Initialize the S3 client
s3_client = boto3.client('s3')

# Read the EXPIRES_IN value from environment variables; default to 3600 seconds (1 hour) if not set
EXPIRES_IN = int(os.environ.get('EXPIRES_IN', 3600))


# Function to generate a presigned URL for uploading a file to S3
def generate_presigned_upload_url(bucket, folder, file_name):
    try:
        key = f"{folder}/{file_name}"
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': bucket,
                'Key': key
            },
            ExpiresIn=EXPIRES_IN
        )
        return presigned_url, None
    except Exception as e:
        return None, str(e)


# The main Lambda function handler
def lambda_handler(event, context):
    try:
        # Parse the 'body' from the event payload and load it as JSON
        body = json.loads(event['body'])

        # Extract the 'files' list from the parsed JSON body
        files = body.get('files', [])

        response = []

        for file in files:
            bucket = file['bucket']
            folder = file['folder']
            file_name = file['file_name']

            presigned_url, error = generate_presigned_upload_url(bucket, folder, file_name)

            if presigned_url:
                response.append({
                    'bucket': bucket,
                    'folder': folder,
                    'file_name': file_name,
                    'presigned_url': presigned_url
                })
            else:
                response.append({
                    'bucket': bucket,
                    'folder': folder,
                    'file_name': file_name,
                    'error': error
                })

        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
