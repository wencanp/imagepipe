# app.py: This is the main entry point for the Flask application.

from flask import request, jsonify, send_from_directory, send_file
from database.models import db, TaskRecord
from celery.result import AsyncResult
from celery import Celery
import os, sys, time, io, requests
from gateway.app_factory import create_app
import uuid
import logging 
from urllib.parse import urlparse, parse_qs
from gateway.support import is_minio_url_expired

app = create_app()

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

@app.route('/upload', methods=['POST'])
def upload_file():
    logger.info(f"[UPLOAD] Received upload request from {request.remote_addr}, Type: {request.content_type}")

    if 'file' not in request.files:
        logger.warning(f"[UPLOAD] File not found in request from {request.remote_addr}")
        return jsonify({
            'success': False,
            'message': '[FAILURE] File not found'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        logger.warning(f"[UPLOAD] No selected file from {request.remote_addr}")
        return jsonify({
            'success': False,
            'message': '[FAILURE] No selected file'
        }), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    process_type = request.form.get('process_type', 'convert')

    if process_type == 'ocr':
        task_id = str(uuid.uuid4())
        txt_filename = f"{task_id}.txt"
        txt_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, txt_filename))

        # submit the async task to Celery
        task = extract_text.apply_async(args=[save_path, txt_path], queue="ocr_queue", task_id=task_id)
        task_record = TaskRecord(
            id=task_id,
            filename=txt_filename,
            process_type=process_type,
            status='PENDING'
        )
        db.session.add(task_record)
        db.session.commit()

        logger.info(f"[UPLOAD] OCR task submitted with ID: {task_id} from {request.remote_addr}")
        return jsonify({
            'success': True,
            'message': '[SUCCESS] OCR task submitted',
            'task_id': task_id
        }), 200

    elif process_type == 'filter':
        filter_type = request.form.get('filter_type', 'BLUR')

        task_id = str(uuid.uuid4())
        filtered_filename = f"{task_id}{os.path.splitext(file.filename)[-1]}"
        filtered_path = os.path.join(UPLOAD_FOLDER, filtered_filename)
        task = apply_filter.apply_async(
            args=[save_path, filtered_path, filter_type], queue="filter_queue", task_id=task_id
        )
        task_record = TaskRecord(
            id=task_id,
            filename=filtered_filename,
            process_type=process_type,
            status='PENDING'
        )
        db.session.add(task_record)
        db.session.commit()

        logger.info(f"[UPLOAD] Filter task submitted with ID: {task_id} from {request.remote_addr}")
        return jsonify({
            'success': True,
            'message': f"[SUCCESS] Filter '{filter_type}' task submitted",
            'task_id': task_id
        }), 200
        
    elif process_type == 'convert': 
        convert_type = request.form.get('convert_type', os.path.splitext(file.filename)[-1])
        quality = request.form.get('quality', 60)

        task_id = str(uuid.uuid4())
        converted_filename = f"{task_id}{convert_type}"
        converted_path = os.path.join(UPLOAD_FOLDER, converted_filename)
        time.sleep(0.1)  # ensure save image then convert

        task = convert_image.apply_async(
            args=[save_path, converted_path, convert_type, quality], queue="convert_queue", task_id=task_id
        )
        task_record = TaskRecord(
            id=task_id,
            filename=converted_filename,
            process_type=process_type,
            status='PENDING'
        )
        db.session.add(task_record)
        db.session.commit()


        logger.info(f"[UPLOAD] Conversion task submitted with ID: {task_id} from {request.remote_addr}")
        return jsonify({
            'success': True,
            'message': '[SUCCESS] Conversion task submitted',
            'task_id': task_id
        }), 200

    logger.warning(f"[UPLOAD] Unknown process type '{process_type}' from {request.remote_addr}")
    return jsonify({
        'success': False,
        'message': '[FAILURE] Unknown process type'
    }), 400


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    logger.info(f"[DOWNLOAD_FILENAME] Download request for file '{filename}' from {request.remote_addr}")
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        logger.warning(f"[DOWNLOAD_FILENAME] File '{filename}' not found for download from {request.remote_addr}")
        return jsonify({
            'success': False,
            'message': '[FAILURE] File not found'
        }), 404

    logger.info(f"[DOWNLOAD_FILENAME] File '{filename}' downloaded successful for {request.remote_addr}")
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route('/download/task/<task_id>', methods=['GET'])
def download_by_task_id(task_id):
    logger.info(f"[DOWNLOAD] Download request for task ID: {task_id} from {request.remote_addr}")
    record = TaskRecord.query.get(task_id)
    if not record:
        logger.warning(f"[DOWNLOAD] TaskRecord '{task_id}' not found for download from {request.remote_addr}")
        return jsonify({
            'success': False,
            'message': '[FAILURE] TaskRecord not found'
        }), 404
    
    if not record.result_url:
        logger.warning(f"[DOWNLOAD] No result_url for task ID {task_id}")
        return jsonify({
            'success': False,
            'message': '[FAILURE] No result file found for this task'
        }), 404

    if is_minio_url_expired(record.result_url):
        logger.warning(f"[DOWNLOAD] Expired download URL for task ID {task_id}")
        return jsonify({
            'success': False,
            'message': '[FAILURE] Download link expired'
        }), 410
    
    try:
        response = requests.get(
            record.result_url,
            stream=True,
            headers={'User-Agent': 'ImagePipe'}
        )
        response.raise_for_status()
    except Exception as e:
        logger.error(f"[DOWNLOAD] Error fetching file from MinIO: {e}")
        return jsonify({
            'success': False,
            'message': '[FAILURE] Error retrieving file'
        }), 500
    
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
        return jsonify({
            'success': False,
            'message': '[FAILURE] Task not found'
        }), 404
    
    status = record.status

    logger.info(f"[STATUS] Task ID: {task_id}, Status: {status} from {request.remote_addr}")
    return jsonify({
        'success': True,
        'message': f'{status}',
        'task_id': task_id,
        'url': record.result_url if status == 'SUCCESS' else None
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
