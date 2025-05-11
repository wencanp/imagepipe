from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()

class TaskRecord(db.Model):
    __tablename__ = 'task_records'

    id = db.Column(db.String(128), primary_key=True)  # Celery task_id
    filename = db.Column(db.String(256))
    process_type = db.Column(db.String(64))
    status = db.Column(db.String(64))  # PENDING, SUCCESS, FAILURE
    error_message = db.Column(db.String(512), nullable=True)
    result_url = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
