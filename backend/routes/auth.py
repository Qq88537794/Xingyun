from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint
    
    Request JSON:
    {
        "username": "string",
        "email": "string",
        "password": "string"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    # Validation
    if not username or not email or not password:
        return jsonify({'error': '用户名、邮箱和密码不能为空'}), 400
    
    if len(username) < 2 or len(username) > 64:
        return jsonify({'error': '用户名长度应为2-64个字符'}), 400
    
    if len(password) < 6:
        return jsonify({'error': '密码长度至少为6个字符'}), 400
    
    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已被注册'}), 409
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': '邮箱已被注册'}), 409
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        
        # Generate access token
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            'message': '注册成功',
            'user': user.to_dict(),
            'access_token': access_token
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'注册失败: {str(e)}'}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Request JSON:
    {
        "username": "string",  # Can be username or email
        "password": "string"
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空'}), 400
    
    # Find user by username or email
    user = User.query.filter(
        (User.username == username) | (User.email == username)
    ).first()
    
    if not user or not user.check_password(password):
        return jsonify({'error': '用户名或密码错误'}), 401
    
    # Generate access token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """
    Get current authenticated user info
    
    Headers:
        Authorization: Bearer <access_token>
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    Update user profile
    
    Headers:
        Authorization: Bearer <access_token>
    
    Request JSON:
    {
        "username": "string" (optional),
        "email": "string" (optional),
        "current_password": "string" (required if changing password),
        "new_password": "string" (optional)
    }
    """
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    
    if not user:
        return jsonify({'error': '用户不存在'}), 404
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    # 更新用户名
    if 'username' in data:
        new_username = data['username'].strip()
        if not new_username:
            return jsonify({'error': '用户名不能为空'}), 400
        
        if len(new_username) < 2 or len(new_username) > 64:
            return jsonify({'error': '用户名长度应为2-64个字符'}), 400
        
        # 检查用户名是否已被其他用户使用
        if new_username != user.username:
            existing_user = User.query.filter_by(username=new_username).first()
            if existing_user:
                return jsonify({'error': '用户名已被使用'}), 409
            user.username = new_username
    
    # 更新邮箱
    if 'email' in data:
        new_email = data['email'].strip()
        if not new_email:
            return jsonify({'error': '邮箱不能为空'}), 400
        
        # 检查邮箱是否已被其他用户使用
        if new_email != user.email:
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user:
                return jsonify({'error': '邮箱已被使用'}), 409
            user.email = new_email
    
    # 更新密码
    if 'new_password' in data:
        current_password = data.get('current_password', '')
        new_password = data['new_password']
        
        # 验证当前密码
        if not current_password:
            return jsonify({'error': '请输入当前密码'}), 400
        
        if not user.check_password(current_password):
            return jsonify({'error': '当前密码错误'}), 401
        
        # 验证新密码
        if len(new_password) < 6:
            return jsonify({'error': '新密码长度至少为6个字符'}), 400
        
        user.set_password(new_password)
    
    try:
        db.session.commit()
        return jsonify({
            'message': '个人资料更新成功',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新失败: {str(e)}'}), 500


@auth_bp.route('/verify-password', methods=['POST'])
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


@auth_bp.route('/avatar', methods=['POST'])
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
    import uuid
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
