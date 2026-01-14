from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class User(db.Model):
    """User model corresponding to 'users' table"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    avatar = db.Column(db.String(512), nullable=True)
    settings = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    # Relationship
    projects = db.relationship('Project', backref='owner', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set the password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert user to dictionary (exclude sensitive data)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
