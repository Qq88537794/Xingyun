"""
文档处理路由
支持文档导入、解析、转换等功能
"""

import os
import logging
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from auth_decorator import jwt_or_admin_required

# 导入文档解析服务
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.document_parser import document_parser_service

logger = logging.getLogger(__name__)

document_bp = Blueprint('document', __name__, url_prefix='/api/document')

# 临时上传目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'temp_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'.docx', '.doc', '.pdf', '.md', '.markdown', '.txt', '.text'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS


@document_bp.route('/parse', methods=['POST'])
@jwt_or_admin_required
def parse_document():
    """
    解析上传的文档
    
    请求：
        - file: 文档文件
        
    响应：
        {
            "code": 200,
            "message": "success",
            "data": {
                "content": "文本内容",
                "html": "HTML内容",
                "metadata": {...},
                "filename": "原始文件名"
            }
        }
    """
    try:
        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'code': 400,
                'message': '没有上传文件',
                'data': None
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'code': 400,
                'message': '文件名为空',
                'data': None
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'code': 400,
                'message': f'不支持的文件格式，支持的格式: {", ".join(ALLOWED_EXTENSIONS)}',
                'data': None
            }), 400
        
        # 保存文件到临时目录
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            # 解析文档
            result = document_parser_service.parse_document(file_path)
            
            if not result['success']:
                return jsonify({
                    'code': 500,
                    'message': result['error'],
                    'data': None
                }), 500
            
            # 返回解析结果
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'content': result['content'],
                    'html': result['html'],
                    'metadata': result['metadata'],
                    'filename': filename
                }
            })
            
        finally:
            # 删除临时文件
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.warning(f"删除临时文件失败: {e}")
    
    except Exception as e:
        logger.error(f"解析文档失败: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'解析失败: {str(e)}',
            'data': None
        }), 500


@document_bp.route('/supported-formats', methods=['GET'])
def get_supported_formats():
    """
    获取支持的文件格式列表
    
    响应：
        {
            "code": 200,
            "message": "success",
            "data": {
                "formats": [".docx", ".pdf", ...]
            }
        }
    """
    try:
        formats = document_parser_service.get_supported_formats()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'formats': formats
            }
        })
    
    except Exception as e:
        logger.error(f"获取支持格式失败: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'获取失败: {str(e)}',
            'data': None
        }), 500
