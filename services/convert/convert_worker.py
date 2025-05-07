from celery import Celery
from PIL import Image
from utils.s3_client import upload_file_to_s3
import os

app = Celery('convert', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

@app.task(name="convert_worker.compress_image")
def compress_image(input_path, output_path, quality=60):
    """
    Compress an image to reduce its file size and outcome format to JPEG.
    
    :param input_path: Path to the input image file.
    :param output_path: Path where the compressed image will be saved.
    :param quality: Quality of the compressed image (1-100).
    """
    try:
        img = Image.open(input_path)
        img = img.convert("RGB")
        img.save(output_path, "JPEG", optimize=True, quality=quality)
        url = upload_file_to_s3(output_path, f"compressed/{os.path.basename(output_path)}")
        return {
            "message": "Compressed and uploaded",
            "url": url
        }
    except Exception as e:
        return f"Compression failed: {str(e)}"
