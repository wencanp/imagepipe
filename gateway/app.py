# app.py: This is the main entry point for the Flask application.

from flask import Flask, request, jsonify, send_from_directory
import os, sys, time

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

@app.route('/upload', methods=['POST'])
def upload_file():
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

        # extract_text.delay(save_path, txt_path)
        extract_text.apply_async(args=[save_path, txt_path], queue="ocr_queue")

        response.update({
            "message": "OCR task submitted",
            "text_file": txt_filename
        })

    elif process_type == 'filter':
        filter_type = request.form.get('filter_type', 'BLUR')
        filtered_filename = f"filtered_{file.filename}"
        filtered_path = os.path.join(UPLOAD_FOLDER, filtered_filename)

        # apply_filter.delay(
        #     input_path=save_path,
        #     output_path=filtered_path,
        #     filter_type=filter_type
        # )
        apply_filter.apply_async(
            args=[save_path, filtered_path, filter_type],
            queue="filter_queue"
        )
        response.update({
            'message': f"Filter '{filter_type}' task submitted",
            'filtered': filtered_filename
        })
        
    else:
        # output path for the compressed image
        compressed_filename = f"compressed_{file.filename}"
        compressed_path = os.path.join(UPLOAD_FOLDER, compressed_filename)
        time.sleep(0.1)  # ensure save image then compress
        # submit the async task to Celery
        # compress_image.delay(
        #     input_path=save_path,
        #     output_path=compressed_path,
        #     quality=60
        # )
        compress_image.apply_async(
            kwargs={"input_path": save_path, "output_path": compressed_path, "quality": 60},
            queue="convert_queue"
        )   
        response.update({
            'message': "Compression task submitted",
            'compressed': compressed_filename
        })


    return jsonify(response), 200


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)