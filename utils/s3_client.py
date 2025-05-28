import boto3, os, logging
from botocore.exceptions import NoCredentialsError
from urllib.parse import urlparse, urlunparse
import io

BUCKET_NAME = 'imagepipe'
INTERNAL_ENDPOINT = os.environ.get('S3_ENDPOINT_URL')  # Railway internal endpoint
PUBLIC_ENDPOINT = os.environ.get('MINIO_PUBLIC_URL')   # public endpoint

s3 = boto3.client(
    's3',
    endpoint_url=INTERNAL_ENDPOINT,
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
        public_s3 = boto3.client(
            's3',
            endpoint_url=PUBLIC_ENDPOINT,
            aws_access_key_id=os.environ.get('MINIO_ROOT_USER'),
            aws_secret_access_key=os.environ.get('MINIO_ROOT_PASSWORD')
        )
        
        url = public_s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600
        )  # URL valid for 1 hour

        logging.info(f"[S3 UPLOAD SUCCESS] {file_path} → {s3_key}.")
        
        return url
    
    except NoCredentialsError as e:
        logging.error(f"[S3 UPLOAD FAILED] {file_path} → {s3_key} | Error: {str(e)}")
        return None


def download_file_from_s3(key):
    try:
        file_stream = io.BytesIO()
        s3.download_fileobj(BUCKET_NAME, key, file_stream)
        file_stream.seek(0)  
        logging.info(f"[S3 DOWNLOAD SUCCESS] Downloading from bucket={BUCKET_NAME}, key={key}")
        return file_stream
    except NoCredentialsError as e:
        logging.error(f"[S3 DOWNLOAD FAILED] Credentials not found: {e}")
        raise
    except Exception as e:
        logging.error(f"[S3 DOWNLOAD FAILED] Failed to download {key}: {e}")
        raise