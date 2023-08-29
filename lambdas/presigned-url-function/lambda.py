import json
import boto3


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

    files = body.get('files', [])
    presigned_urls = []

    for file in files:
        # Since we already have the schema in place we don't need to do the request validations here anymore
        bucket_name = file.get('bucket')
        file_name = file.get('file_name')
        folder = file.get('folder')

        try:
            # Check if the bucket exists
            s3.head_bucket(Bucket=bucket_name)

            # Generate a pre-signed URL for object upload
            presigned_url = s3.generate_presigned_url(
                'put_object',
                Params={'Bucket': bucket_name, 'Key': f'{folder}/{file_name}'},
                ExpiresIn=3600  # URL expiration time in seconds
            )
            presigned_urls.append({
                "file": f"s3://{bucket_name}/{folder}/{file_name}",
                "presigned_url": presigned_url
            })
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
