import boto3
from botocore.exceptions import NoCredentialsError

s3 = boto3.client(
    's3',
    endpoint_url='http://minio:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin'
)

BUCKET_NAME = 'imagepipe'

def upload_file_to_s3(file_path, s3_key):
    try:
        s3.upload_file(file_path, BUCKET_NAME, s3_key)

        # generate a presigned URL for the uploaded file
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )  # URL valid for 1 hour

        return url
    
    except NoCredentialsError:
        return None
