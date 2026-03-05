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


# --- Test 1: unsupported format returns error ---
@patch("services.filter.filter_worker.current_task")
@patch("services.filter.filter_worker.upload_file_to_s3")
@patch("services.filter.filter_worker.download_file_from_s3")
@patch("services.filter.filter_worker.flask_app")
def test_unsupported_filter_returns_error(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_task.request.id = "fake-task-id"

    with patch("services.filter.filter_worker.TaskRecord"):
        from services.filter.filter_worker import apply_filter
        filter_type="INVALIDTYPE"
        result = apply_filter.run("input.jpg", "output.tiff", filter_type)

    assert "error" in result
    assert result["error"] == "Unsupported filter type"


# --- Test 2: corrupted image returns error ---
@patch("services.filter.filter_worker.current_task")
@patch("services.filter.filter_worker.download_file_from_s3")
@patch("services.filter.filter_worker.flask_app")
def test_corrupted_image_returns_error(mock_flask_app, mock_download, mock_task):
    mock_download.return_value = BytesIO(b"this is not an image")
    mock_task.request.id = "fake-task-id"

    with patch("services.filter.filter_worker.TaskRecord"):
        from services.filter.filter_worker import apply_filter
        filter_type="BLUR"
        result = apply_filter.run("bad.jpg", "output.jpeg",filter_type)

    assert "error" in result


# --- Test 3: successful filtering returns applied message ---
@patch("services.filter.filter_worker.current_task")
@patch("services.filter.filter_worker.upload_file_to_s3")
@patch("services.filter.filter_worker.download_file_from_s3")
@patch("services.filter.filter_worker.flask_app")
def test_successful_filter_applied(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_task.request.id = "fake-task-id"

    with patch("services.filter.filter_worker.TaskRecord"):
        from services.filter.filter_worker import apply_filter
        filter_type="BLUR"
        result = apply_filter.run("input.jpg", "output.tiff", filter_type)

    assert result == {"message": f"'{filter_type}' applied and image uploaded"}


# --- Test 4: PNG filtering uses RGBA mode ---
@patch("services.filter.filter_worker.current_task")
@patch("services.filter.filter_worker.upload_file_to_s3")
@patch("services.filter.filter_worker.download_file_from_s3")
@patch("services.filter.filter_worker.flask_app")
def test_png_input_uses_rgba(mock_flask_app, mock_download, mock_upload, mock_task):
    mock_download.return_value = make_fake_image()
    mock_upload.return_value = "https://fake-s3-url/output.png"
    mock_task.request.id = "fake-task-id"
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.filter.filter_worker.TaskRecord"):
        with patch("PIL.Image.Image.convert", wraps=None) as mock_convert:
            filter_type="BLUR"
            mock_convert.return_value = MagicMock(save=MagicMock())
            from services.filter.filter_worker import apply_filter
            apply_filter.run("input.png", "output.png", filter_type)

    mock_convert.assert_called_with("RGBA")