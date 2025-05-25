from celery import Celery, current_task
from PIL import Image
import pytesseract
from utils.s3_client import upload_file_to_s3
from database.models import TaskRecord, db
import os, time
from gateway.app_factory import create_app
from celery.utils.log import get_task_logger

start_time = time.time()
logger = get_task_logger(__name__)

pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'  

app = Celery('ocr', broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

flask_app = create_app()

@app.task(name="ocr_worker.extract_text", queue='ocr_queue')
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

        logger.info(f"OCR success - Task: {current_task.request.id} - Output: {output_path}. Start time [{start_time}] End time [{time.time()}]")
        return {
            "message": "OCR completed and uploaded",
            "url": url
        }
    except Exception as e:
        logger.error(f"OCR failed - Task: {current_task.request.id} - Error: {str(e)}. Start time [{start_time}] End time [{time.time()}]")
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
        return f"OCR failed: {str(e)}"
