# app.py: This is the main entry point for the Flask application.

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from celery.result import AsyncResult
from celery import Celery
import os, sys, time

app = Flask(__name__)

cors = CORS(app)
app.config['CORS_HEADERS'] = 'Access-Control-Allow-Origin'
# # 配置 CORS 选项
# cors_options = {
#     "origins": "http://localhost:3000",  # 允许的前端地址
#     "supports_credentials": True,       # 允许发送 cookies 或其他凭据
#     "methods": ["GET", "POST", "OPTIONS"],  # 允许的 HTTP 方法
#     "allow_headers": ["Content-Type", "Authorization"],  # 允许的请求头
# }

# # 启用 CORS 并应用选项
# CORS(app, resources={r"/*": cors_options})

celery_app = Celery('gateway', broker='redis://redis:6379/0', backend="redis://redis:6379/0")

# Add the path to the services directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/convert")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/filter")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/ocr")))

from convert_worker import compress_image
from filter_worker import apply_filter
from ocr_worker import extract_text

app = Flask(__name__)
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads"))
# UPLOAD_FOLDER = '../uploads'
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
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    process_type = request.form.get('process_type', 'compress')
    response = {
        'original': file.filename
    }

    if process_type == 'ocr':
        txt_filename = f"{os.path.splitext(file.filename)[0]}.txt"
        txt_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, txt_filename))

        task = extract_text.apply_async(args=[save_path, txt_path], queue="ocr_queue")

        response.update({
            "message": "OCR task submitted",
            "text_file": txt_filename, 
            "task_id": task.id
        })

    elif process_type == 'filter':
        filter_type = request.form.get('filter_type', 'BLUR')
        filtered_filename = f"filtered_{file.filename}"
        filtered_path = os.path.join(UPLOAD_FOLDER, filtered_filename)

        task = apply_filter.apply_async(
            args=[save_path, filtered_path, filter_type],
            queue="filter_queue"
        )

        response.update({
            'message': f"Filter '{filter_type}' task submitted",
            'filtered': filtered_filename,
            'task_id': task.id
        })
        
    elif process_type == 'compress':
        # output path for the compressed image
        compressed_filename = f"compressed_{file.filename}"
        compressed_path = os.path.join(UPLOAD_FOLDER, compressed_filename)
        time.sleep(0.1)  # ensure save image then compress
        # submit the async task to Celery
        task = compress_image.apply_async(
            args=[save_path,compressed_path, 60],
            queue="convert_queue"
        )   
        response.update({
            'message': "Compression task submitted",
            'compressed': compressed_filename,
            'task_id': task.id
        })


    return jsonify(response), 200


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


@app.route('/status/<task_id>', methods=['GET'])
def check_task_status(task_id):
    result = AsyncResult(task_id, app=celery_app)

    response = {
        'task_id': task_id,
        'state': result.state
    }

    if result.state == 'SUCCESS':
        response['result'] = result.result
    elif result.state == 'FAILURE':
        response['error'] = str(result.result)  

    return jsonify(response), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
