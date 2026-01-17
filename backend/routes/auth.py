from datetime import datetime
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
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Generate access token
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'message': '登录成功',
        'user': user.to_dict(),
        'access_token': access_token
    }), 200

