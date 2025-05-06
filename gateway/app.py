# app.py: This is the main entry point for the Flask application.

from flask import Flask, request, jsonify, send_from_directory
import os, sys, time

# Add the path to the services directory to the system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../services/convert")))

from worker import compress_image

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

    # output path for the compressed image
    compressed_filename = f"compressed_{file.filename}"
    compressed_path = os.path.join(UPLOAD_FOLDER, compressed_filename)
    time.sleep(0.1)  # ensure save image then compress
    # submit the async task to Celery
    compress_image.delay(
        input_path=save_path,
        output_path=compressed_path,
        quality=60
    )


    return jsonify({
        'message': 'File uploaded successfully, processing compression requested',
        "original": file.filename, 
        'compressed': compressed_filename
    }), 200


@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404

    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)