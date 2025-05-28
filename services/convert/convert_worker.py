import os 
import time

from celery import Celery, current_task
from celery.utils.log import get_task_logger
from PIL import Image, UnidentifiedImageError

from database.models import TaskRecord, db
from gateway.app_factory import create_app
from utils.s3_client import upload_file_to_s3, download_file_from_s3

start_time = time.time()
logger = get_task_logger(__name__)

app = Celery('convert', broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

flask_app = create_app()

@app.task(name="convert_worker.convert_image", queue='convert_queue')
def convert_image(input_path, output_path, convert_type, quality=60):
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
        
        # Pillow recognizes JPEG not JPG
        if convert_type == '.jpg':
            convert_type = '.jpeg'
            
        # Check supported formats to convert to
        supported_formats = ['.jpeg', '.png', '.gif', '.bmp']
        if convert_type not in supported_formats:
            return {
                "error": "Unsupported conversion type"
            }

        # Convert, compress, and save the image
        img = img.convert("RGBA") if convert_type == ".png" else img.convert("RGB")
        local_tmp_path = f"/tmp/{os.path.basename(output_path)}"
        img.save(
            local_tmp_path, 
            format=convert_type.strip('.').upper(), 
            optimize=True, 
            quality=quality
        )

        # Upload the converted file to S3
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

        logger.info(f"Conversion success - Task: {current_task.request.id} - Output: {output_path}. Start time [{start_time}] End time [{time.time()}]")
        return {
            "message": "Converted and uploaded",
            "url": url
        }
    except Exception as e:
        logger.error(f"Conversion failed - Task: {current_task.request.id} - Error: {str(e)}. Start time [{start_time}] End time [{time.time()}]")
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
        return f"Cnversion failed: {str(e)}"
