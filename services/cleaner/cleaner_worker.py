from celery import Celery
from utils.s3_client import s3, BUCKET_NAME
from datetime import datetime, timedelta, timezone
from celery.schedules import crontab
import os

app = Celery('cleaner', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

EXPIRATION_HOURS = 0.0167  # 1分钟 = 1/60小时 ≈ 0.0167 for testing
# EXPIRATION_HOURS = 12

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
                print(f"Deleting expired file: {key}")
                try:
                    # Delete the file from S3
                    s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                    print(f"Deleted expired file: {key}")
                    # delete the local copy if it exists
                    local_path = os.path.join('/app/uploads', os.path.basename(key))
                    if os.path.exists(local_path):
                        os.remove(local_path)
                        print(f"Deleted local file: {local_path}")
                    remove_files.append(key)
                except Exception as e:
                    print(f"Error deleting file {key}: {e}")
                    
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }

# auto scheduling for cleaner
app.conf.beat_schedule = {
    'run-cleaner-every-hour': {
        'task': 'cleaner_worker.clean_expired_files',
        # 'schedule': crontab(minute=0, hour='*'),  # every hour
        'schedule': crontab(),  # min for testing
        'options': {'queue': 'cleaner_queue'}
    }
}
app.conf.timezone = 'UTC'

if __name__ == "__main__":
    print("Cleaner worker launched, executing task...")
    # Execute the task immediately each runtime
    clean_expired_files()