from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.user import User

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user info
    
    Headers:
        Authorization: Bearer <access_token>
    
    Returns:
        {
            "user": {
                "id": 1,
                "username": "string",
                "email": "string",
                "avatar": "string",
                "description": "string",
                "settings": {},
                "last_login": "ISO datetime",
                "created_at": "ISO datetime"
            }
        }
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@user_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    
    Headers:
        Authorization: Bearer <access_token>
    
    Request JSON:
        {
            "username": "string",  # optional
            "description": "string",  # optional
            "avatar": "string"  # optional
        }
    
    Returns:
        {
            "message": "更新成功",
            "user": { ... }
        }
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    # Update username if provided
    if 'username' in data:
        new_username = data['username'].strip()
        if new_username and new_username != user.username:
            # Check if username is already taken
            existing = User.query.filter_by(username=new_username).first()
            if existing and existing.id != user.id:
                return jsonify({'error': '用户名已被使用'}), 409
            if len(new_username) < 2 or len(new_username) > 64:
                return jsonify({'error': '用户名长度应为2-64个字符'}), 400
            user.username = new_username
    
    # Update description if provided
    if 'description' in data:
        user.description = data['description']
    
    # Update avatar if provided
    if 'avatar' in data:
        user.avatar = data['avatar']
    
    try:
        db.session.commit()
        return jsonify({
            'message': '更新成功',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@user_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    
    Headers:
        Authorization: Bearer <access_token>
    
    Request JSON:
        {
            "oldPassword": "string",
            "newPassword": "string"
        }
    
    Returns:
        {
            "message": "密码修改成功"
        }
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    old_password = data.get('oldPassword', '')
    new_password = data.get('newPassword', '')
    
    if not old_password or not new_password:
        return jsonify({'error': '原密码和新密码不能为空'}), 400
    
    # Verify old password
    if not user.check_password(old_password):
        return jsonify({'error': '原密码错误'}), 401
    
    # Validate new password
    if len(new_password) < 6:
        return jsonify({'error': '新密码长度至少为6个字符'}), 400
    
    # Set new password
    user.set_password(new_password)
    
    try:
        db.session.commit()
        return jsonify({'message': '密码修改成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'密码修改失败: {str(e)}'}), 500
