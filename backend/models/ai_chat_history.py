"""
AI聊天历史记录模型
"""
from datetime import datetime
from . import db


class AIChatHistory(db.Model):
    """AI聊天历史记录模型"""
    
    __tablename__ = 'ai_chat_history'
    
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    project_id = db.Column(db.BigInteger, db.ForeignKey('projects.id', ondelete='SET NULL'), nullable=True)
    document_id = db.Column(db.String(255), nullable=True)  # 文档ID，用于区分不同文档的对话
    session_id = db.Column(db.String(255), nullable=True)
    request_type = db.Column(db.String(50), nullable=False)  # 'chat', 'outline', 'expand', 'locate' 等
    user_message = db.Column(db.Text, nullable=True)
    ai_response = db.Column(db.Text, nullable=False)
    tokens_used = db.Column(db.Integer, default=0)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'project_id': self.project_id,
            'document_id': self.document_id,
            'session_id': self.session_id,
            'request_type': self.request_type,
            'user_message': self.user_message,
            'ai_response': self.ai_response,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @staticmethod
    def save_chat_history(user_id, request_type, ai_response, user_message=None, 
                         project_id=None, document_id=None, session_id=None, tokens_used=0):
        """
        保存聊天历史记录
        
        Args:
            user_id: 用户ID
            request_type: 请求类型 ('chat', 'outline', 'expand', 'locate' 等)
            ai_response: AI响应内容
            user_message: 用户消息（可选）
            project_id: 项目ID（可选）
            document_id: 文档ID（可选）
            session_id: 会话ID（可选）
            tokens_used: 使用的token数量（可选）
        
        Returns:
            保存的记录对象
        """
        try:
            history = AIChatHistory(
                user_id=user_id,
                project_id=project_id,
                document_id=document_id,
                session_id=session_id,
                request_type=request_type,
                user_message=user_message,
                ai_response=ai_response,
                tokens_used=tokens_used
            )
            db.session.add(history)
            db.session.commit()
            return history
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_recent_history(user_id, days=3, limit=100):
        """
        获取最近N天的历史记录
        
        Args:
            user_id: 用户ID
            days: 天数（默认3天）
            limit: 返回记录数量限制（默认100）
        
        Returns:
            历史记录列表
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return AIChatHistory.query.filter(
            AIChatHistory.user_id == user_id,
            AIChatHistory.created_at >= cutoff_date
        ).order_by(AIChatHistory.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def cleanup_old_records(days=3):
        """
        清理超过N天的旧记录
        
        Args:
            days: 保留天数（默认3天）
        
        Returns:
            删除的记录数量
        """
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        try:
            deleted_count = AIChatHistory.query.filter(
                AIChatHistory.created_at < cutoff_date
            ).delete()
            db.session.commit()
            return deleted_count
        except Exception as e:
            db.session.rollback()
            raise e
