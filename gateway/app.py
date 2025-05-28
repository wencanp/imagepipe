"""
gateway/app.py

This is the main entry point for the Flask application.
Handles API routes, request/response logic, and integration with other services.
"""
# Python standard libraries
import io
import logging
import os
import sys
import uuid
# Third-party libraries
from celery import Celery
from flask import request, jsonify, send_file
import requests
# Local application imports
from database.models import db, TaskRecord
from gateway.app_factory import create_app
from gateway.support import is_minio_url_expired
from utils.cleaner_code import _json_fail
from utils.s3_client import upload_file_to_s3

app = create_app()
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

celery_app = Celery('gateway', broker=os.getenv("REDIS_URL"), backend=os.getenv("REDIS_URL"))

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gateway')

# Add the path to the services directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/convert")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/filter")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ocr")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/cleaner")))

from convert_worker import convert_image
from filter_worker import apply_filter
from ocr_worker import extract_text
from cleaner_worker import clean_expired_files

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads"))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST', 'OPTION'])
def upload_file():
    logger.info(f"[UPLOAD] Received upload request from {request.remote_addr}, Type: {request.content_type}")

    if 'file' not in request.files:
        logger.warning(f"[UPLOAD] File not found in request from {request.remote_addr}")
        return _json_fail('[FAILURE] File not found', 400)
    
    file = request.files['file']
    if file.filename == '':
        logger.warning(f"[UPLOAD] No selected file from {request.remote_addr}")
        return _json_fail('[FAILURE] No selected file', 400) 

    task_id = str(uuid.uuid4())
    filename = f"{task_id}_{file.filename}"
    processed_filename = filename
    local_tmp_path = f"/tmp/{filename}"
    file.save(local_tmp_path)
    # Upload file to MinIO
    s3_key = f"uploads/{filename}"
    upload_file_to_s3(local_tmp_path, s3_key)
    os.remove(local_tmp_path)

    process_type = request.form.get('process_type', 'convert')

    if process_type == 'ocr':
        processed_filename = f"{task_id}.txt"

        # submit the async task to Celery
        task = extract_text.apply_async(
            args=[s3_key, f"ocr/{processed_filename}"], queue="ocr_queue", task_id=task_id)
        TaskRecord.create_record(
            task_id=task_id,
            filename=processed_filename,
            process_type=process_type
        )

        logger.info(f"[UPLOAD] OCR task submitted with ID: {task_id} from {request.remote_addr}")
        return jsonify({
            'success': True,
            'message': '[SUCCESS] OCR task submitted',
            'task_id': task_id
        }), 200

    elif process_type == 'filter':
        filter_type = request.form.get('filter_type', 'BLUR')
        processed_filename = f"{task_id}{os.path.splitext(file.filename)[-1]}"

        task = apply_filter.apply_async(
            args=[s3_key, f"filter/{processed_filename}", filter_type], queue="filter_queue", task_id=task_id
        )
        TaskRecord.create_record(
            id=task_id,
            filename=processed_filename,
            process_type=process_type
        )

        logger.info(f"[UPLOAD] Filter task submitted with ID: {task_id} from {request.remote_addr}")
        return jsonify({
            'success': True,
            'message': f"[SUCCESS] Filter '{filter_type}' task submitted",
            'task_id': task_id
        }), 200
        
    elif process_type == 'convert': 
        convert_type = request.form.get('convert_type', os.path.splitext(file.filename)[-1])
        quality = request.form.get('quality', 60)
        processed_filename = f"{task_id}{convert_type}"

        task = convert_image.apply_async(
            args=[s3_key, f"convert/{processed_filename}", convert_type, quality], queue="convert_queue", task_id=task_id
        )
        TaskRecord.create_record(
            task_id=task_id,
            filename=processed_filename,
            process_type=process_type
        )

        logger.info(f"[UPLOAD] Conversion task submitted with ID: {task_id} from {request.remote_addr}")
        return jsonify({
            'success': True,
            'message': '[SUCCESS] Conversion task submitted',
            'task_id': task_id
        }), 200

    logger.warning(f"[UPLOAD] Unknown process type '{process_type}' from {request.remote_addr}")
    return _json_fail('[FAILURE] Unknown process type', 400)


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    return jsonify({
        "error": "This API is deprecated and no longer available.",
        "message": "Please use the new endpoint instead.",
        "status": 410
    }), 410


@app.route('/download/task/<task_id>', methods=['GET'])
def download_by_task_id(task_id):
    logger.info(f"[DOWNLOAD] Download request for task ID: {task_id} from {request.remote_addr}")
    record = TaskRecord.query.get(task_id)
    if not record:
        logger.warning(f"[DOWNLOAD] TaskRecord '{task_id}' not found for download from {request.remote_addr}")
        return _json_fail('[FAILURE] TaskRecord not found', 404)
    
    if not record.result_url:
        logger.warning(f"[DOWNLOAD] No result_url for task ID {task_id}")
        return _json_fail('[FAILURE] No result file found for this task', 404)

    if is_minio_url_expired(record.result_url):
        logger.warning(f"[DOWNLOAD] Expired download URL for task ID {task_id}")
        return _json_fail('[FAILURE] Download link expired', 410)
    
    try:
        response = requests.get(
            record.result_url,
            stream=True,
            headers={'User-Agent': 'ImagePipe'}
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"[DOWNLOAD] Error fetching file from MinIO: {e}")
        return _json_fail('[FAILURE] Error retrieving file', 500)
    
    logger.info(f"[DOWNLOAD] File '{record.filename}' downloaded successful for {request.remote_addr}")
    return send_file(
        io.BytesIO(response.content),
        as_attachment=True,
        download_name=record.filename or 'downloaded_file'
    )


@app.route('/status/<task_id>', methods=['GET'])
def check_task_status(task_id):
    logger.info(f"[STATUS] Checking status for task ID: {task_id} from {request.remote_addr}")
    record = TaskRecord.query.get(task_id)
    if not record:
        logger.warning(f"[STATUS] TaskRecord '{task_id}' not found from {request.remote_addr}")
        return _json_fail('[FAILURE] Task not found', 404)
    
    status = record.status

    logger.info(f"[STATUS] Task ID: {task_id}, Status: {status} from {request.remote_addr}")
    return jsonify({
        'success': True,
        'message': f'{status}',
        'task_id': task_id
    }), 200


@app.route('/cleanup', methods=['POST'])
def trigger_cleanup():
    logger.info(f"[CLEANUP] Triggering cleanup task")
    task = clean_expired_files.apply_async(queue="cleaner_queue")
    return jsonify({
        'success': True,
        'message': '[SUCCESS] Cleanup task triggered',
        'task_id': task.id
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
