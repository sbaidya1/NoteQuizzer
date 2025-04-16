"""
Application factory for the Flask app.

- Loads environment variables
- Sets up Flask configuration
- Initializes the SQLAlchemy database
- Registers routes
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

# load env variables from .env file
load_dotenv()

# initialize sqlachemy
db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # set config values 
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-fallback')
    app.config['UPLOAD_FOLDER'] = os.path.abspath(
      os.path.join(os.path.dirname(__file__), '..', 'uploads')
    )
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notequizzer.db'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

    # initliaze db with app context
    db.init_app(app)

    with app.app_context():
        from . import routes
        db.create_all()

    return app
