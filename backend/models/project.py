from datetime import datetime
from . import db


class Project(db.Model):
    """Project model corresponding to 'projects' table"""
    
    __tablename__ = 'projects'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), default='active')
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.TIMESTAMP, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    resources = db.relationship('ProjectResource', backref='project', lazy='dynamic', cascade='all, delete-orphan')
    
    def to_dict(self, include_resources=False):
        """Convert project to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'status': self.status,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_resources:
            data['resources'] = [r.to_dict() for r in self.resources.filter_by().all()]
        return data
    
    def soft_delete(self):
        """Mark project as deleted (soft delete)"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
