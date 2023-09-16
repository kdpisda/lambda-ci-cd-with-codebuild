import json
import os
import boto3


def check_and_create_path(s3_client, bucket_name, path):
    """
    This function checks if the path exists in the bucket and creates it if it doesn't.
    :param s3_client:
    :param bucket_name:
    :param path:
    :return:
    """
    try:
        s3_client.head_object(Bucket=bucket_name, Key=path)
    except Exception as e:
        if e.response['Error']['Code'] == '404':
            s3_client.put_object(Bucket=bucket_name, Key=path)
        else:
            raise


def lambda_handler(event, context):
    """
    This function generates pre-signed URLs for the files that are going to be uploaded to S3.
    The reqeust validations are done on the APIGateway level so we don't need to do them here.
    Also, in case of error we just append None to the list of pre-signed URLs for that file.
    :param event:
    :param context:
    :return dict:
    """

    s3 = boto3.client('s3')

    body = json.loads(event['body'])

    expires_in = int(os.getenv('EXPIRES_IN', 3600))

    files = body.get('files', [])
    presigned_urls = []

    for file in files:
        # Since we already have the schema in place we don't need to do the request validations here anymore
        bucket_name = file.get('bucket')
        file_name = file.get('file_name')
        folder = file.get('folder')

        try:
            # Check if the folder exists and create it if it doesn't
            path = f"{folder}/{file_name}"
            check_and_create_path(s3, bucket_name, path)

            # Generate a pre-signed URL for object upload
            presigned_url = s3.generate_presigned_url(
                'put_object',
                Params={'Bucket': bucket_name, 'Key': path},
                ExpiresIn=expires_in  # URL expiration time in seconds
            )
            presigned_urls.append({
                "file": f"s3://{bucket_name}/{folder}/{file_name}",
                "presigned_url": presigned_url
            })
        except boto3.exceptions.botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"Error Code: {error_code}, Error Message: {error_message}")
        except Exception as e:
            # In case of any error we append None to the list for that file
            print(f"Error generating pre-signed URL for {folder}/{file_name}: {e}")
            presigned_urls.append({
                "file": f"s3://{bucket_name}/{folder}/{file_name}",
                "presigned_url": None
            })

    return {
        'statusCode': 200,
        'body': json.dumps({'presigned_urls': presigned_urls})
    }
