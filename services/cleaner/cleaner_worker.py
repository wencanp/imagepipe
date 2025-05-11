from celery import Celery
from utils.s3_client import s3, BUCKET_NAME
from datetime import datetime, timedelta, timezone
from celery.schedules import crontab

app = Celery('cleaner', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

EXPIRATION_HOURS = 12

@app.task(name="cleaner_worker.clean_expired_files")
def clean_expired_files():
    remove_files = []
    try:
        response = s3.list_objects_v2(Bucket=BUCKET_NAME)
        now = datetime.now(timezone.utc)

        for obj in response.get('Contents', []):
            key = obj['Key']
            last_modified = obj['LastModified']

            # Check if the file is older than the expiration time
            if now - last_modified > timedelta(hours=EXPIRATION_HOURS):
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                remove_files.append(key)
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

# auto scheduling for cleaner
app.conf.beat_schedule = {
    'run-cleaner-every-hour': {
        'task': 'cleaner_worker.clean_expired_files',
        'schedule': crontab(minute=0, hour='*'),  # every hour
    }
}
app.conf.timezone = 'UTC'
