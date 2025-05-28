import os 
import time
from datetime import datetime, timedelta, timezone

from celery import Celery, current_task
from celery.schedules import crontab
from celery.utils.log import get_task_logger

from database.models import TaskRecord, db
from gateway.app_factory import create_app
from utils.s3_client import s3, BUCKET_NAME

start_time = time.time()
logger = get_task_logger(__name__)

app = Celery('cleaner', broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

EXPIRATION_HOURS = 12

@app.task(name="cleaner_worker.clean_expired_files", queue='cleaner_queue')
def clean_expired_files():
    remove_files = []
    db_removed = []
    flask_app = create_app()
    try:
        s3_objs = s3.list_objects_v2(Bucket=BUCKET_NAME).get('Contents', [])
        now = datetime.now(timezone.utc)
        expired_objs = [
            obj['Key'] for obj in s3_objs 
            if now - obj['LastModified'] > timedelta(hours=EXPIRATION_HOURS)
        ]

        if not expired_objs:
            logger.info(f"No expired files found. Start time.")
            return {"message": "No expired files to clean up"}
        
        for key in expired_objs:
            filename = os.path.basename(key)
            try:
                # delete s3 files
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                remove_files.append(key)
                # delete TaskRecord in the database
                with flask_app.app_context():
                    if TaskRecord.delete_by_filename(filename):
                        db_removed.append(filename)
            except Exception as e:
                logger.error(f"Error deleting file {key}: {e}. ")
                continue

        logger.info(
            f"Cleanup completed. "
            f"Deleted files: {remove_files}, DB records: {db_removed}. "
            f"Start time [{start_time}] End time [{time.time()}]")
        return {
            "message": "Cleanup completed",
            "deleted_files": remove_files,
            "deleted_db_records": db_removed
        }              
    except Exception as e:
        logger.error(f"Error during cleanup: {e}. task_id: {current_task.request.id}. Start time [{start_time}] End time [{time.time()}]")
        return {
            "status": "failed",
            "error": str(e)
        }

# auto scheduling for cleaner
app.conf.beat_schedule = {
    'run-cleaner-every-hour': {
        'task': 'cleaner_worker.clean_expired_files',
        'schedule': crontab(minute=0, hour='*'),  # every hour
        'options': {'queue': 'cleaner_queue'}
    }
}
app.conf.timezone = 'UTC'

if __name__ == "__main__":
    logger.info("Cleaner worker launched, executing task ... start time [{start_time}]")
    # Execute the task immediately each runtime
    clean_expired_files()