from datetime import datetime
from . import db


class Folder(db.Model):
    """Folder model for organizing projects"""
    
    __tablename__ = 'folders'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    color = db.Column(db.String(32), default='blue')  # 文件夹颜色
    icon = db.Column(db.String(32), default='folder')  # 图标类型
    parent_id = db.Column(db.BigInteger, db.ForeignKey('folders.id', ondelete='CASCADE'), nullable=True)  # 支持嵌套文件夹
    sort_order = db.Column(db.Integer, default=0)  # 排序
    is_deleted = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.TIMESTAMP, nullable=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('Project', backref='folder', lazy='dynamic')
    subfolders = db.relationship('Folder', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def to_dict(self, include_projects=False, include_subfolders=False):
        """Convert folder to dictionary"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'color': self.color,
            'icon': self.icon,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'is_deleted': self.is_deleted,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        
        if include_projects:
            data['projects'] = [p.to_dict() for p in self.projects.filter_by(is_deleted=False).all()]
            data['project_count'] = self.projects.filter_by(is_deleted=False).count()
        
        if include_subfolders:
            data['subfolders'] = [f.to_dict() for f in self.subfolders.filter_by(is_deleted=False).all()]
        
        return data
    
    def soft_delete(self):
        """Mark folder as deleted (soft delete)"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
