import os 
import time

from celery import Celery, current_task
from celery.utils.log import get_task_logger
from PIL import Image, ImageFilter, UnidentifiedImageError

from database.models import TaskRecord, db
from gateway.app_factory import create_app
from utils.s3_client import upload_file_to_s3, download_file_from_s3

start_time = time.time()
logger = get_task_logger(__name__)

app = Celery('filter', broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

flask_app = create_app()

@app.task(name="filter_worker.apply_filter", queue='filter_queue')
def apply_filter(input_path, output_path, filter_type='BLUR'):
    try:
        # Check if the input file exists
        try:
            input_stream = download_file_from_s3(input_path)
            img = Image.open(input_stream)
        except UnidentifiedImageError:
            logger.error(f"Unsupported image format or corrupted file. Task ID: {current_task.request.id}. Start time [{start_time}] End time [{time.time()}]")
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
            logger.error(f"Unsupported filter type: {filter_type}. Task ID: {current_task.request.id}. Start time [{start_time}] End time [{time.time()}]")
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
        local_tmp_path = f"/tmp/{os.path.basename(output_path)}"
        img.save(
            local_tmp_path, 
            format=original_format, 
            optimize=True, 
            quality=95
        )

        # Upload the filtered file to S3
        url = upload_file_to_s3(local_tmp_path, output_path)
        os.remove(local_tmp_path) 

        with flask_app.app_context():
            task_id = current_task.request.id
            task_record = TaskRecord.query.get(task_id)
            if task_record:
                task_record.status = 'SUCCESS'
                task_record.result_url = url
                task_record.error_message = None
                db.session.commit()
            else:
                return {"error": "Task record not found"}

        logger.info(f"Filter success - Task: {current_task.request.id} - Output: {output_path}. Start time [{start_time}] End time [{time.time()}]")
        return {
            "message": f"'{filter_type}' applied and image uploaded",
            "url": url
        }
    except Exception as e:
        logger.error(f"Filter failed - Task: {current_task.request.id} - Error: {str(e)}. Start time [{start_time}] End time [{time.time()}]")
        task_record = None
        try:
            with flask_app.app_context():
                task_id = current_task.request.id
                task_record = TaskRecord.query.get(task_id)
                if task_record:
                    task_record.status = 'FAILURE'
                    task_record.error_message = str(e)
                    db.session.commit()
        except Exception:
            pass
        return f"Filter failed: {str(e)}"