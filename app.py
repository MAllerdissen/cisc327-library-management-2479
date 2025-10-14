"""
Main Flask application entry point for the Library Management System.

This module provides the application factory pattern for creating Flask app instances.
Routes are organized in separate blueprint modules in the routes package.
"""

from flask import Flask
from database import init_database, add_sample_data
from routes import register_blueprints


def create_app():
    """
    Application factory function to create and configure Flask app.
    """
    app = Flask(__name__)
    # Minimal secret key for flash messages (not security critical in coursework)
    app.config['SECRET_KEY'] = 'dev-secret-key'

    # Ensure DB exists and has sample data
    init_database()
    add_sample_data()

    # Register blueprints
    register_blueprints(app)
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=4999)
