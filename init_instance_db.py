import os
from gateway.app_factory import create_app
from database.models import db

if __name__ == "__main__":
    # automatically create the instance directory and database tables
    os.makedirs("/app/instance", exist_ok=True)
    app = create_app()
    with app.app_context():
        db.create_all()
    print("[INFO] instance directory and database tables created.")
