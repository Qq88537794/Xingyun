from datetime import datetime
from . import db


class ProjectResource(db.Model):
    """ProjectResource model corresponding to 'project_resources' table"""
    
    __tablename__ = 'project_resources'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    project_id = db.Column(db.BigInteger, db.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    storage_provider = db.Column(db.String(32), default='local')
    mime_type = db.Column(db.String(128), nullable=True)
    file_size = db.Column(db.BigInteger, default=0)
    parsing_status = db.Column(db.String(32), default='pending')
    vector_collection_id = db.Column(db.String(128), nullable=True)
    error_msg = db.Column(db.Text, nullable=True)
    uploaded_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.TIMESTAMP, nullable=True)
    
    def soft_delete(self):
        """Mark resource as deleted (soft delete)"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert resource to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'filename': self.filename,
            'file_path': self.file_path,
            'storage_provider': self.storage_provider,
            'mime_type': self.mime_type,
            'file_size': self.file_size,
            'parsing_status': self.parsing_status,
            'vector_collection_id': self.vector_collection_id,
            'error_msg': self.error_msg,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }

