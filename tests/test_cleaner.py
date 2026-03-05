'''
Tests for cleaner service.

Test 1: no expired files returns early message
Test 2: expired files are deleted from S3 and database
Test 3: single file deletion failure is skipped, others continue
Test 4: list_objects failure returns error status
'''


import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone


def make_s3_object(key, hours_old):
    """Helper: create a fake S3 object with LastModified"""
    return {
        'Key': key,
        'LastModified': datetime.now(timezone.utc) - timedelta(hours=hours_old)
    }


# --- Test 1: no expired files returns early message ---
@patch("services.cleaner.cleaner_worker.s3")
@patch("services.cleaner.cleaner_worker.create_app")
def test_no_expired_files_returns_message(mock_create_app, mock_s3):
    # 1 is less than EXPIRATION_HOURS = 12
    mock_s3.list_objects_v2.return_value = {
        'Contents': [make_s3_object("uploads/file.jpg", hours_old=1)]
    }

    from services.cleaner.cleaner_worker import clean_expired_files
    result = clean_expired_files.run()

    assert result == {"message": "No expired files to clean up"}


# --- Test 2: expired files are deleted from S3 and database ---
@patch("services.cleaner.cleaner_worker.s3")
@patch("services.cleaner.cleaner_worker.create_app")
def test_expired_files_are_deleted(mock_create_app, mock_s3):
    # 24 is over EXPIRATION_HOURS = 12
    mock_s3.list_objects_v2.return_value = {
        'Contents': [make_s3_object("uploads/old_file.jpg", hours_old=24)]
    }
    mock_s3.delete_object.return_value = {}

    mock_flask_app = MagicMock()
    mock_create_app.return_value = mock_flask_app
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.cleaner.cleaner_worker.TaskRecord") as mock_task_record:
        mock_task_record.delete_by_filename.return_value = True
        from services.cleaner.cleaner_worker import clean_expired_files
        result = clean_expired_files.run()

    # test delete_object was called (bucket name differs, test without this)
    call_kwargs = mock_s3.delete_object.call_args.kwargs
    assert call_kwargs["Key"] == "uploads/old_file.jpg"
    assert "uploads/old_file.jpg" in result["deleted_files"]
    assert "old_file.jpg" in result["deleted_db_records"]


# -- Test 3: single file deletion failure is skipped, others continue ---
@patch("services.cleaner.cleaner_worker.s3")
@patch("services.cleaner.cleaner_worker.create_app")
def test_single_file_deletion_failure_is_skipped(mock_create_app, mock_s3):
    mock_s3.list_objects_v2.return_value = {
        'Contents': [
            make_s3_object("uploads/bad_file.jpg", hours_old=24),
            make_s3_object("uploads/good_file.jpg", hours_old=24),
        ]
    }
    # failure 1st, succuss 2nd
    mock_s3.delete_object.side_effect = [Exception("S3 error"), {}]

    mock_flask_app = MagicMock()
    mock_create_app.return_value = mock_flask_app
    mock_flask_app.app_context.return_value.__enter__ = MagicMock()
    mock_flask_app.app_context.return_value.__exit__ = MagicMock(return_value=False)

    with patch("services.cleaner.cleaner_worker.TaskRecord") as mock_task_record:
        mock_task_record.delete_by_filename.return_value = True
        from services.cleaner.cleaner_worker import clean_expired_files
        result = clean_expired_files.run()

    # bad_file skipped，good_file successfully deleted
    assert "uploads/bad_file.jpg" not in result["deleted_files"]
    assert "uploads/good_file.jpg" in result["deleted_files"]


# --- Test 4: list_objects failure returns error status ---
@patch("services.cleaner.cleaner_worker.current_task")
@patch("services.cleaner.cleaner_worker.s3")
@patch("services.cleaner.cleaner_worker.create_app")
def test_list_objects_failure_returns_error(mock_create_app, mock_s3, mock_task):
    mock_s3.list_objects_v2.side_effect = Exception("S3 unavailable")
    mock_task.request.id = "fake-task-id"

    from services.cleaner.cleaner_worker import clean_expired_files
    result = clean_expired_files.run()

    assert result["status"] == "failed"
    assert "S3 unavailable" in result["error"]