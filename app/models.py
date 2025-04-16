"""
Database model for uploaded files

Model stores:
- Unique id for each file
- The original filename of the uploaded PDF
- The extracted text content of the file

Used by sqlalchemy to manage file records
"""

from . import db

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)