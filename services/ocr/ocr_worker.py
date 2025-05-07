from celery import Celery
from PIL import Image
import pytesseract
from utils.s3_client import upload_file_to_s3
import os

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  

app = Celery('ocr', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

@app.task(name="ocr_worker.extract_text")
def extract_text(input_path, output_path):
    """
    Extract text from an image using Tesseract OCR.
    
    :param input_path: Path to the input image file.
    :param output_path: Path to save the extracted text file.
    """
    try:
        img = Image.open(input_path)
        img = img.convert("RGB")
        text = pytesseract.image_to_string(img)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        url = upload_file_to_s3(output_path, f"OCR/{os.path.basename(output_path)}")
        return {
            "message": "OCR completed and uploaded",
            "url": url
        }
    except Exception as e:
        return f"OCR failed: {str(e)}"
    