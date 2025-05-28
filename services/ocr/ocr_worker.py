import os 
import time

from celery import Celery, current_task
from celery.utils.log import get_task_logger
from PIL import Image
import pytesseract

from database.models import TaskRecord, db
from gateway.app_factory import create_app
from utils.s3_client import upload_file_to_s3, download_file_from_s3

start_time = time.time()
logger = get_task_logger(__name__)

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  

app = Celery('ocr', broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

flask_app = create_app()

@app.task(name="ocr_worker.extract_text", queue='ocr_queue')
def extract_text(input_path, output_path):
    try:
        input_stream = download_file_from_s3(input_path)
        img = Image.open(input_stream)
        img = img.convert("RGB")
        text = pytesseract.image_to_string(img)

        local_tmp_path = f"/tmp/{os.path.basename(output_path)}"
        with open(local_tmp_path, "w", encoding="utf-8") as f:
            f.write(text)

        url = upload_file_to_s3(local_tmp_path, output_path)
        os.remove(local_tmp_path) 

        with flask_app.app_context():
            TaskRecord.update_record(
                current_task.request.id, 
                status='SUCCESS', 
                result_url=url,
                error_message=None
            )

        logger.info(f"OCR success - Task: {current_task.request.id} - Output: {output_path}. Start time [{start_time}] End time [{time.time()}]")
        return {
            "message": "OCR completed and uploaded",
            "url": url
        }
    except Exception as e:
        logger.error(f"OCR failed - Task: {current_task.request.id} - Error: {str(e)}. Start time [{start_time}] End time [{time.time()}]")
        task_record = None
        with flask_app.app_context():
            TaskRecord.update_record(
                current_task.request.id, 
                status='FAILURE', 
                error_message=str(e)
            )
        return f"OCR failed: {str(e)}"
