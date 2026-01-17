import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

class Config:
    """Flask application configuration"""
    
    # Secret key for JWT
    SECRET_KEY = os.environ.get('SECRET_KEY', 'xingyun-secret-key-dev')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'xingyun-jwt-secret-dev')
    
    # JWT settings
    JWT_ACCESS_TOKEN_EXPIRES = 86400  # 24 hours in seconds
    
    # MySQL Database configuration
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_PORT = os.environ.get('DB_PORT', '3306')
    DB_NAME = os.environ.get('DB_NAME', 'xingyun')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')  # 密码必须从环境变量获取
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'md', 'png', 'jpg', 'jpeg', 'gif', 'xlsx', 'xls', 'pptx', 'ppt'}

