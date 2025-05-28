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
    
    @classmethod
    def create_record(cls, task_id, filename, process_type):
        record = cls(
            id=task_id,
            filename=filename,
            process_type=process_type,
            status='PENDING'
        )
        db.session.add(record)
        db.session.commit()

    @classmethod
    def update_record(cls, task_id, status, result_url=None, error_message=None):
        record = cls.query.get(task_id)
        if not record:
            return {"error": "Task record not found"}
        if status: 
            record.status = status
        if result_url:
            record.result_url = result_url
        if error_message:
            record.error_message = error_message

        db.session.commit()
