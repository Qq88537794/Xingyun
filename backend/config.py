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
    
    # ============== AI 配置 ==============
    
    # 智谱AI (Zhipu/GLM) 配置
    ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')
    ZHIPU_MODEL = os.environ.get('ZHIPU_MODEL', 'glm-4-flash')  # 默认使用免费的flash模型
    
    # Google Gemini 配置
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    GEMINI_MODEL = os.environ.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')
    
    # 默认AI提供商 ('zhipu' 或 'gemini')
    DEFAULT_AI_PROVIDER = os.environ.get('DEFAULT_AI_PROVIDER', 'zhipu')
    
    # Embedding 配置
    EMBEDDING_PROVIDER = os.environ.get('EMBEDDING_PROVIDER', 'local')  # 'local', 'zhipu' 或 'gemini'
    EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5')  # 本地模型名称
    EMBEDDING_DEVICE = os.environ.get('EMBEDDING_DEVICE', None)  # 'cpu', 'cuda', 'mps' 或 None(自动)
    EMBEDDING_CACHE_FOLDER = os.environ.get('EMBEDDING_CACHE_FOLDER', None)  # 模型缓存目录
    
    # Qdrant 向量数据库配置
    QDRANT_HOST = os.environ.get('QDRANT_HOST', 'localhost')
    QDRANT_PORT = int(os.environ.get('QDRANT_PORT', '6333'))
    QDRANT_USE_MEMORY = os.environ.get('QDRANT_USE_MEMORY', 'true').lower() == 'true'  # 开发环境使用内存模式
    QDRANT_PATH = os.environ.get('QDRANT_PATH', None)  # 本地持久化路径（可选）
    
    # RAG 配置
    RAG_CHUNK_SIZE = int(os.environ.get('RAG_CHUNK_SIZE', '500'))
    RAG_CHUNK_OVERLAP = int(os.environ.get('RAG_CHUNK_OVERLAP', '50'))
    RAG_TOP_K = int(os.environ.get('RAG_TOP_K', '5'))

