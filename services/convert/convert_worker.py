from celery import Celery, current_task
from PIL import Image, UnidentifiedImageError
from utils.s3_client import upload_file_to_s3
from database.models import TaskRecord, db
from gateway.app_factory import create_app
import os

app = Celery('convert', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

flask_app = create_app()

@app.task(name="convert_worker.convert_image")
def convert_image(input_path, output_path, convert_type, quality=60):
    """
    Compress and convert an image to reduce its file size and  change outcome format.
    
    :param input_path: Path to the input image file.
    :param output_path: Path where the compressed image will be saved.
    os.path.splitext(file.filename)[0]
    :param quality: Quality of the compressed image (1-100).
    """
    try: 
        # Check if the input file exists
        try:
            img = Image.open(input_path)
        except UnidentifiedImageError:
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
        img.save(
            output_path, 
            format=convert_type.strip('.').upper(), 
            optimize=True, 
            quality=quality
        )

        # Upload the converted file to S3
        url = upload_file_to_s3(output_path, f"convert/{os.path.basename(output_path)}")

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
            "message": "Converted and uploaded",
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
        return f"Cnversion failed: {str(e)}"
