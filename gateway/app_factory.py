from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from database.models import db
from flask_migrate import Migrate
import os

migrate = Migrate()

def create_app():
    app = Flask(__name__)
    env_origins = os.environ.get("REACT_APP_API_URL", "")
    env_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
    allowed_origins = env_origins + [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://*.up.railway.app",
        "https://*.railway.app"
    ]
    CORS(app, 
         origins=allowed_origins, 
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"], 
         allow_headers=["*"],
         supports_credentials=True)

    # Managed database Supabase
    # app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    # database config compatible local dev adaptation
    db_uri = os.environ.get("DATABASE_URL")
    if db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    else:
        # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../instance/imagepipe.db'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:mypassword@postgres:5432/imagepipe'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    migrate.init_app(app, db)

    Swagger(app, template={
        "info": {
            "title": "ImagePipe API",
            "description": "A lightweight image processing platform supporting convert, filter, and OCR.",
            "version": "1.0.0"
        },
        "host": "imagepipe.up.railway.app",
        "basePath": "/api",
        "schemes": ["https"],
    })

    return app
