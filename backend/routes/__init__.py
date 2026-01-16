from flask import Blueprint

from .auth import auth_bp
from .projects import projects_bp
from .resources import resources_bp
from .folders import folders_bp


def register_blueprints(app):
    """Register all blueprints with the Flask app"""
    app.register_blueprint(auth_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(folders_bp)
