from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .folder import Folder
from .project import Project
from .resource import ProjectResource
