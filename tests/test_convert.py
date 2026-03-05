import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO
from PIL import Image


def make_fake_image(mode="RGB", size=(100, 100), fmt="JPEG"):
    """Helper: create a fake in-memory image stream"""
    buf = BytesIO()
    Image.new(mode, size).save(buf, format=fmt)
    buf.seek(0)
    return buf


# ── Test 1: jpg should be normalized to .jpeg ──────────────────────────────
@patch("services.convert.convert_worker.current_task")
@patch("services.convert.convert_worker.upload_file_to_s3")
@patch("services.convert.convert_worker.download_file_from_s3")
@patch("services.convert.convert_worker.flask_app")
def test_jpg_normalized_to_jpeg(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_upload.return_value = "https://fake-s3-url/output.jpeg"
    mock_task.request.id = "fake-task-id"
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.convert.convert_worker.TaskRecord"):
        from services.convert.convert_worker import convert_image
        result = convert_image.run("input.jpg", "output.jpeg", ".jpg")

    assert result == {"message": "Converted and uploaded"}


# ── Test 2: unsupported format returns error ────────────────────────────────
@patch("services.convert.convert_worker.current_task")
@patch("services.convert.convert_worker.upload_file_to_s3")
@patch("services.convert.convert_worker.download_file_from_s3")
@patch("services.convert.convert_worker.flask_app")
def test_unsupported_format_returns_error(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_task.request.id = "fake-task-id"

    with patch("services.convert.convert_worker.TaskRecord"):
        from services.convert.convert_worker import convert_image
        result = convert_image.run("input.jpg", "output.tiff", ".tiff")

    assert "error" in result
    assert result["error"] == "Unsupported conversion type"


# ── Test 3: corrupted image returns error ───────────────────────────────────
@patch("services.convert.convert_worker.current_task")
@patch("services.convert.convert_worker.download_file_from_s3")
@patch("services.convert.convert_worker.flask_app")
def test_corrupted_image_returns_error(mock_flask_app, mock_download, mock_task):
    mock_download.return_value = BytesIO(b"this is not an image")
    mock_task.request.id = "fake-task-id"

    with patch("services.convert.convert_worker.TaskRecord"):
        from services.convert.convert_worker import convert_image
        result = convert_image.run("bad.jpg", "output.jpeg", ".jpeg")

    assert "error" in result


# ── Test 4: PNG conversion uses RGBA mode ───────────────────────────────────
@patch("services.convert.convert_worker.current_task")
@patch("services.convert.convert_worker.upload_file_to_s3")
@patch("services.convert.convert_worker.download_file_from_s3")
@patch("services.convert.convert_worker.flask_app")
def test_png_conversion_uses_rgba(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_upload.return_value = "https://fake-s3-url/output.png"
    mock_task.request.id = "fake-task-id"
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.convert.convert_worker.TaskRecord"):
        with patch("PIL.Image.Image.convert", wraps=None) as mock_convert:
            mock_convert.return_value = MagicMock(save=MagicMock())
            from services.convert.convert_worker import convert_image
            convert_image.run("input.jpg", "output.png", ".png")

    mock_convert.assert_called_with("RGBA")