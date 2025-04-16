"""
Run script for the Flask application

Creates app instance and runs it with Flask's built-in development server

To start server: 
python run.py
"""

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)