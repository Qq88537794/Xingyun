import os
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

from config import Config
from models import db
from routes import register_blueprints


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
