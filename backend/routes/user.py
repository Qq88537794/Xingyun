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
            "email": "string",  # optional
            "description": "string",  # optional
            "avatar": "string",  # optional
            "current_password": "string",  # required if changing password
            "new_password": "string"  # optional
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
    
    # Update email if provided
    if 'email' in data:
        new_email = data['email'].strip()
        if not new_email:
            return jsonify({'error': '邮箱不能为空'}), 400
        
        # Check if email is already used by another user
        if new_email != user.email:
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                return jsonify({'error': '邮箱已被使用'}), 409
            user.email = new_email
    
    # Update description if provided
    if 'description' in data:
        user.description = data['description']
    
    # Update avatar if provided
    if 'avatar' in data:
        user.avatar = data['avatar']
    
    # Update password if provided
    if 'new_password' in data:
        current_password = data.get('current_password', '')
        new_password = data['new_password']
        
        # Verify current password
        if not current_password:
            return jsonify({'error': '请输入当前密码'}), 400
        
        if not user.check_password(current_password):
            return jsonify({'error': '当前密码错误'}), 401
        
        # Validate new password
        if len(new_password) < 6:
            return jsonify({'error': '新密码长度至少为6个字符'}), 400
        
        user.set_password(new_password)
    
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


@user_bp.route('/verify-password', methods=['POST'])
@jwt_required()
def verify_password():
    """
    Verify user's current password
    
    Headers:
        Authorization: Bearer <access_token>
    
    Request JSON:
    {
        "password": "string"
    }
    
    Response:
    {
        "valid": true/false
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    password = data.get('password', '')
    
    if not password:
        return jsonify({'error': '密码不能为空'}), 400
    
    # 验证密码
    is_valid = user.check_password(password)
    
    return jsonify({
        'valid': is_valid,
        'message': '密码正确' if is_valid else '密码错误'
    }), 200


@user_bp.route('/avatar', methods=['POST'])
@jwt_required()
def upload_avatar():
    """
    Upload user avatar
    
    Headers:
        Authorization: Bearer <access_token>
    
    Form Data:
        avatar: image file
    
    Response:
    {
        "message": "头像上传成功",
        "user": {...}
    }
    """
    import os
    from werkzeug.utils import secure_filename
    from flask import current_app
    import uuid
    
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    # 检查是否有文件
    if 'avatar' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['avatar']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    # 验证文件类型
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    filename = secure_filename(file.filename)
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': '只支持 PNG、JPG、JPEG、GIF、WebP 格式的图片'}), 400
    
    # 创建上传目录
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    avatars_folder = os.path.join(upload_folder, 'avatars')
    os.makedirs(avatars_folder, exist_ok=True)
    
    # 生成唯一文件名
    unique_filename = f"{user_id}_{uuid.uuid4().hex}.{file_ext}"
    file_path = os.path.join(avatars_folder, unique_filename)
    
    try:
        # 删除旧头像文件（如果存在）
        if user.avatar:
            old_avatar_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', user.avatar.lstrip('/'))
            if os.path.exists(old_avatar_path):
                try:
                    os.remove(old_avatar_path)
                except Exception as e:
                    print(f"删除旧头像失败: {e}")
        
        # 保存新头像
        file.save(file_path)
        
        # 更新数据库中的头像路径
        user.avatar = f"/uploads/avatars/{unique_filename}"
        db.session.commit()
        
        return jsonify({
            'message': '头像上传成功',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'上传失败: {str(e)}'}), 500
