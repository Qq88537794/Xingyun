import os
import sys
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# 将 AI-test 目录添加到 Python 路径，以便导入 ai 模块
backend_dir = os.path.dirname(os.path.abspath(__file__))
ai_test_dir = os.path.join(backend_dir, 'AI-test')
if ai_test_dir not in sys.path:
    sys.path.insert(0, ai_test_dir)

from config import Config
from models import db
from routes import register_blueprints


def init_llm():
    """初始化LLM工厂"""
    from ai.llm import init_llm_factory, ModelProvider
    
    # 读取环境配置
    llm_provider = os.getenv('LLM_PROVIDER', 'zhipu')
    zhipu_key = os.getenv('ZHIPU_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    configs = []
    
    # 根据配置创建LLM实例
    if zhipu_key:
        configs.append({
            'provider': 'zhipu',
            'api_key': zhipu_key,
            'model_name': 'glm-4-flash',
            'instance_name': 'zhipu_default'
        })
    
    if gemini_key:
        configs.append({
            'provider': 'gemini',
            'api_key': gemini_key,
            'model_name': 'gemini-2.0-flash-exp',
            'instance_name': 'gemini_default'
        })
    
    if not configs:
        print("警告: 未配置任何LLM API密钥")
        return
    
    # 初始化工厂
    default_provider = ModelProvider.ZHIPU if llm_provider == 'zhipu' else ModelProvider.GEMINI
    factory = init_llm_factory(configs, default_provider=default_provider)
    
    print(f"LLM工厂初始化成功，默认提供商: {default_provider.value}")


def create_app():
    """Application factory function"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # JWT configuration
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)
    
    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}, r"/uploads/*": {"origins": "*"}})
    db.init_app(app)
    JWTManager(app)
    
    # Initialize LLM
    with app.app_context():
        init_llm()
    
    # Create upload folder if not exists
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)
    
    # Register blueprints
    register_blueprints(app)
    
    # Serve uploaded files
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files"""
        return send_from_directory(Config.UPLOAD_FOLDER, filename)
    
    # Health check endpoint
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'ok',
            'message': '行云智能文档工作站 API 服务运行中'
        }), 200
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': '资源不存在'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': '服务器内部错误'}), 500
    
    return app


if __name__ == '__main__':
    app = create_app()
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    print("=" * 50)
    print("行云智能文档工作站 API 服务")
    print("=" * 50)
    print(f"Running on: http://127.0.0.1:5000")
    print(f"Upload folder: {Config.UPLOAD_FOLDER}")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)
