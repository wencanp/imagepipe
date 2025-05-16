from flask import Flask
from database.models import db
from flask_migrate import Migrate
import os

migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # database config compatible local dev adaptation
    db_uri = os.environ.get("IMAGEPIPE_DB_URI")
    if db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    else:
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/imagepipe.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mypassword@postgres:5432/imagepipe'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)
    return app
