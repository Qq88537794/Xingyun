"""
自定义JWT认证装饰器
支持标准JWT Token和开发用管理员Token
"""

import os
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError


def ensure_admin_user():
    """
    确保管理员测试用户存在
    
    Returns:
        int: 管理员用户ID
    """
    from models import db
    from models.user import User
    
    # 查找管理员用户
    admin_user = User.query.filter_by(username='admin_dev').first()
    
    if not admin_user:
        # 创建管理员用户
        admin_user = User(
            username='admin_dev',
            email='admin_dev@test.com'
        )
        admin_user.set_password('admin123')  # 固定密码，仅用于开发
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"✓ 已自动创建管理员测试用户: admin_dev (ID={admin_user.id})")
        except Exception as e:
            db.session.rollback()
            print(f"✗ 创建管理员用户失败: {e}")
            # 尝试再次查找，可能是并发创建
            admin_user = User.query.filter_by(username='admin_dev').first()
            if not admin_user:
                raise Exception("无法创建或找到管理员用户")
    
    return admin_user.id


def jwt_or_admin_required(fn):
    """
    自定义JWT认证装饰器
    
    支持两种认证方式：
    1. 标准JWT Token (Bearer token)
    2. 开发用管理员Token (配置在.env中的ADMIN_DEV_TOKEN)
    
    使用方法：
    @jwt_or_admin_required
    def protected_route():
        pass
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # 获取Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        # 检查是否是管理员Token
        admin_token = os.getenv('ADMIN_DEV_TOKEN')
        if admin_token and auth_header == f'Bearer {admin_token}':
            # 使用管理员Token，确保管理员用户存在
            request.admin_mode = True
            request.current_user_id = ensure_admin_user()
            return fn(*args, **kwargs)
        
        # 标准JWT验证
        try:
            verify_jwt_in_request()
            request.admin_mode = False
            request.current_user_id = get_jwt_identity()
            return fn(*args, **kwargs)
        except NoAuthorizationError:
            return jsonify({
                'code': 401,
                'message': 'Missing or invalid authorization token'
            }), 401
        except Exception as e:
            return jsonify({
                'code': 401,
                'message': f'Authentication failed: {str(e)}'
            }), 401
    
    return wrapper


def get_current_user_id():
    """
    获取当前用户ID
    
    Returns:
        int: 用户ID
    """
    if hasattr(request, 'admin_mode') and request.admin_mode:
        return request.current_user_id
    return get_jwt_identity()
