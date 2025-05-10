from celery import Celery, current_task
from PIL import Image, ImageFilter, UnidentifiedImageError
from utils.s3_client import upload_file_to_s3
from database.models import TaskRecord, db
import os
from gateway.app_factory import create_app

flask_app = create_app()

app = Celery('filter', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

@app.task(name="filter_worker.apply_filter")
def apply_filter(input_path, output_path, filter_type='BLUR'):
    """
    Apply a filter to an image and save the result.
    
    :param input_path: Path to the input image file.
    :param output_path: Path where the filtered image will be saved.
    :param filter_type: Type of filter to apply (e.g., 'BLUR', 'CONTOUR').
    """
    try:
        # Check if the input file exists
        try:
            img = Image.open(input_path)
        except UnidentifiedImageError:
            return {
                "error": "Unsupported image format or corrupted file."
            }

        # Check supported filter types
        filter_mapping = {
            'BLUR': ImageFilter.BLUR,
            'CONTOUR': ImageFilter.CONTOUR,
            'DETAIL': ImageFilter.DETAIL,
            'SHARPEN': ImageFilter.SHARPEN
        }
        if filter_type not in filter_mapping:
            return {
                "error": "Unsupported filter type"
            }
        
        # Apply the filter
        original_format = os.path.splitext(input_path)[-1].strip('.').upper()
        # Pillow recognizes JPEG not JPG
        if original_format == "JPG":
            original_format = "JPEG"
        img = img.convert("RGBA") if original_format == "PNG" else img.convert("RGB")
        
        img = img.filter(filter_mapping[filter_type])

        # Save image
        img.save(
            output_path, 
            format=original_format, 
            optimize=True, 
            quality=95
        )

        # Upload the filtered file to S3
        url = upload_file_to_s3(output_path, f"filter/{os.path.basename(output_path)}")

        with flask_app.app_context():
            task_id = current_task.request.id
            task_record = TaskRecord.query.get(task_id)
            if task_record:
                task_record.status = 'SUCCESS'
                task_record.result_url = url
                db.session.commit()
            else:
                return {"error": "Task record not found"}

        return {
            "message": f"'{filter_type}' applied and image uploaded",
            "url": url
        }
    except Exception as e:
        task_record = None
        try:
            with flask_app.app_context():
                task_id = current_task.request.id
                task_record = TaskRecord.query.get(task_id)
                if task_record:
                    task_record.status = 'FAILURE'
                    db.session.commit()
        except Exception:
            pass
        return f"Filter failed: {str(e)}"