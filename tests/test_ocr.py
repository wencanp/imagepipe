'''
Tests for OCR service.

Test 1: successful OCR returns completed message
Test 2: extracted text is written to temp file
Test 3: exception during processing returns failure message

ocr logic & dependency: 
1. download_file_from_s3            network
2. pytesseract.image_to_string      loccal ocr engine
3. upload_file_to_s3                network
4. flask_app / TaskRecord           db
5. current_task                     Celery
'''


import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
from PIL import Image


def make_fake_image(mode="RGB", size=(100, 100), fmt="JPEG"):
    """Helper: create a fake in-memory image stream"""
    buf = BytesIO()
    Image.new(mode, size).save(buf, format=fmt)
    buf.seek(0)
    return buf


# --- Test 1: successful OCR returns completed message ---
@patch("services.ocr.ocr_worker.current_task")
@patch("services.ocr.ocr_worker.upload_file_to_s3")
@patch("services.ocr.ocr_worker.download_file_from_s3")
@patch("services.ocr.ocr_worker.flask_app")
def test_successful_ocr_returns_message(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_upload.return_value = "https://fake-s3-url/output.txt"
    mock_task.request.id = "fake-task-id"
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.ocr.ocr_worker.TaskRecord"):
        with patch("pytesseract.image_to_string", return_value="Hello World"):
            with patch("builtins.open", mock_open()):
                with patch("os.remove"):
                    from services.ocr.ocr_worker import extract_text
                    result = extract_text.run("input.jpg", "output.txt")

    assert result == {"message": "OCR completed and uploaded"}


# --- Test 2: extracted text is written to temp file ---
@patch("services.ocr.ocr_worker.current_task")
@patch("services.ocr.ocr_worker.upload_file_to_s3")
@patch("services.ocr.ocr_worker.download_file_from_s3")
@patch("services.ocr.ocr_worker.flask_app")
def test_ocr_text_written_to_file(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_upload.return_value = "https://fake-s3-url/output.txt"
    mock_task.request.id = "fake-task-id"
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.ocr.ocr_worker.TaskRecord"):
        with patch("pytesseract.image_to_string", return_value="Hello World"):
            with patch("builtins.open", mock_open()) as mock_file:
                with patch("os.remove"):
                    from services.ocr.ocr_worker import extract_text
                    extract_text.run("input.jpg", "output.txt")

    # 验证 "Hello World" 有没有被写入文件
    mock_file().write.assert_called_with("Hello World")


# --- Test 3: exception during processing returns failure message ---
@patch("services.ocr.ocr_worker.current_task")
@patch("services.ocr.ocr_worker.download_file_from_s3")
@patch("services.ocr.ocr_worker.flask_app")
def test_ocr_failure_returns_error_string(mock_flask_app, mock_download, mock_task):
    mock_download.side_effect = Exception("S3 connection failed")
    mock_task.request.id = "fake-task-id"
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.ocr.ocr_worker.TaskRecord"):
        from services.ocr.ocr_worker import extract_text
        result = extract_text.run("input.jpg", "output.txt")

    assert "OCR failed" in result