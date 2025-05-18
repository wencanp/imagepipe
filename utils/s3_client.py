import boto3, os, logging
from botocore.exceptions import NoCredentialsError
from urllib.parse import urlparse, urlunparse

BUCKET_NAME = 'imagepipe'
PUBLIC_HOST = os.environ.get('MINIO_PUBLIC_HOST', 'localhost:9000')

s3 = boto3.client(
    's3',
    endpoint_url=os.environ.get('S3_ENDPOINT_URL'),
    aws_access_key_id=os.environ.get('MINIO_ROOT_USER'),
    aws_secret_access_key=os.environ.get('MINIO_ROOT_PASSWORD')
)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def upload_file_to_s3(file_path, s3_key):
    try:
        s3.upload_file(file_path, BUCKET_NAME, s3_key)

        # generate a presigned URL for the uploaded file
        url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )  # URL valid for 1 hour

        logging.info(f"[3S UPLOAD SUCCESS] {file_path} → {s3_key}, presigned_url: {url}")

        # Modify the URL to use the custom domain
        parsed_url = urlparse(url)
        new_netloc = PUBLIC_HOST
        url = urlunparse(parsed_url._replace(netloc=new_netloc))

        return url
    
    except NoCredentialsError as e:
        logging.error(f"[3S UPLOAD FAILED] {file_path} → {s3_key} | Error: {str(e)}")
        return None
