from celery import Celery
from PIL import Image
import os

app = Celery('convert', broker='redis://localhost:6379/0')

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
        return f"Compressed and saved to {output_path}"
    except Exception as e:
        return f"Compression failed: {str(e)}"
    
# if __name__ == '__main__':
#     result = compress_image(
#         input_path='../../uploads/test.jpg',
#         output_path='test_compressed.jpg'
#     )
#     print(result)