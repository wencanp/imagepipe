# app.py: This is the main entry point for the Flask application.

from flask import request, jsonify, send_from_directory
from database.models import db, TaskRecord
from celery.result import AsyncResult
from celery import Celery
import os, sys, time
from gateway.app_factory import create_app
import uuid

app = create_app()

celery_app = Celery('gateway', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

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

@app.route('/upload', methods=['POST', 'OPTIONS'])
def upload_file():
    if request.method == 'OPTIONS':
        # 处理预检请求
        response = jsonify({'message': 'CORS preflight'})
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        return response, 200
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': '[FAILURE] File not found'
        }), 400
    
    file = request.files['file']
    if file.filename == '':
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

        return jsonify({
            'success': True,
            'message': '[SUCCESS] Conversion task submitted',
            'task_id': task_id
        }), 200

    return jsonify({
        'success': False,
        'message': '[FAILURE] Unknown process type'
    }), 400


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'message': '[FAILURE] File not found'
        }), 404

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route('/download/task/<task_id>', methods=['GET'])
def download_by_task_id(task_id):
    record = TaskRecord.query.get(task_id)
    if not record:
        return jsonify({
            'success': False,
            'message': '[FAILURE] Task not found'
        }), 404
    file_path = os.path.join(UPLOAD_FOLDER, record.filename)
    if not os.path.exists(file_path):
        return jsonify({
            'success': False,
            'message': '[FAILURE] File not found'
        }), 404
    return send_from_directory(UPLOAD_FOLDER, record.filename, as_attachment=True)


@app.route('/status/<task_id>', methods=['GET'])
def check_task_status(task_id):
    record = TaskRecord.query.get(task_id)
    if not record:
        return jsonify({
            'success': False,
            'message': '[FAILURE] Task not found'
        }), 404
    status = record.status
    return jsonify({
        'success': True,
        'message': f'[SUCCESS] Task status fetched: {status}',
        'task_id': task_id
    }), 200


@app.route('/cleanup', methods=['POST'])
def trigger_cleanup():
    # Trigger the Celery task to clean up expired files
    task = clean_expired_files.apply_async(queue="cleaner_queue")
    return jsonify({
        'success': True,
        'message': '[SUCCESS] Cleanup task triggered',
        'task_id': task.id
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
