from celery import Celery
from PIL import Image
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = r'D:\Software\Tesseract-OCR\tesseract.exe'  

app = Celery('ocr', broker='redis://localhost:6379/0')

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

        return f"OCR completed. Output: {output_path}"
    except Exception as e:
        return f"OCR failed: {e}"