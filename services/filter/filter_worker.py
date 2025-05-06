from celery import Celery
from PIL import Image, ImageFilter
import os

app = Celery('filter', broker='redis://localhost:6379/0')

@app.task(name="filter_worker.apply_filter")
def apply_filter(input_path, output_path, filter_type='BLUR'):
    """
    Apply a filter to an image and save the result.
    
    :param input_path: Path to the input image file.
    :param output_path: Path where the filtered image will be saved.
    :param filter_type: Type of filter to apply (e.g., 'BLUR', 'CONTOUR').
    """
    try:
        img = Image.open(input_path)
        img = img.convert("RGB")

        if filter_type == 'BLUR':
            img = img.filter(ImageFilter.BLUR)
        elif filter_type == 'CONTOUR':
            img = img.filter(ImageFilter.CONTOUR)
        elif filter_type == 'DETAIL':
            img = img.filter(ImageFilter.DETAIL)
        elif filter_type == 'SHARPEN':
            img = img.filter(ImageFilter.SHARPEN)
        else:
            raise ValueError(f"Unknown filter type: {filter_type}")

        img.save(output_path, "JPEG", optimize=True, quality=95)
        return f"{filter_type} applied and saved to {output_path}"
    except Exception as e:
        return f"Filter failed: {str(e)}"