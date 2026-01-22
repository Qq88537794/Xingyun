import os
import mimetypes
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from auth_decorator import jwt_or_admin_required, get_current_user_id
from models import db
from models.project import Project
from models.resource import ProjectResource

logger = logging.getLogger(__name__)

# 初始化并添加 Office 文档 MIME 类型支持
mimetypes.init()
mimetypes.add_type('application/vnd.openxmlformats-officedocument.wordprocessingml.document', '.docx')
mimetypes.add_type('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', '.xlsx')
mimetypes.add_type('application/vnd.openxmlformats-officedocument.presentationml.presentation', '.pptx')
mimetypes.add_type('application/msword', '.doc')
mimetypes.add_type('application/vnd.ms-excel', '.xls')
mimetypes.add_type('application/vnd.ms-powerpoint', '.ppt')
mimetypes.add_type('text/markdown', '.md')

resources_bp = Blueprint('resources', __name__, url_prefix='/api/projects')


def allowed_file(filename):
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config.get('ALLOWED_EXTENSIONS', set())


def get_project_upload_path(project_id):
    """Get the upload path for a specific project"""
    base_path = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    project_path = os.path.join(base_path, str(project_id))
    
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    
    return project_path


@resources_bp.route('/<int:project_id>/resources', methods=['GET'])
@jwt_or_admin_required
def list_resources(project_id):
    """
    Get all resources for a specific project
    """
    user_id = get_current_user_id()
    
    # Verify project ownership
    project = Project.query.filter_by(id=project_id, user_id=user_id, is_deleted=False).first()
    
    if not project:
        return jsonify({'error': '项目不存在或无权访问'}), 404
    
    resources = ProjectResource.query.filter_by(project_id=project_id, is_deleted=False).order_by(
        ProjectResource.uploaded_at.desc()
    ).all()
    
    return jsonify({
        'resources': [r.to_dict() for r in resources],
        'total': len(resources)
    }), 200


@resources_bp.route('/<int:project_id>/resources', methods=['POST'])
@jwt_or_admin_required
def upload_resource(project_id):
    """
    Upload a file to a project
    
    Form data:
        file: The file to upload
    """
    user_id = get_current_user_id()
    
    # Verify project ownership
    project = Project.query.filter_by(id=project_id, user_id=user_id, is_deleted=False).first()
    
    if not project:
        return jsonify({'error': '项目不存在或无权访问'}), 404
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': '不支持的文件类型'}), 400
    
    # Secure the filename and save
    original_filename = file.filename
    
    # 先提取原始扩展名（处理中文文件名时 secure_filename 可能丢失扩展名）
    _, original_ext = os.path.splitext(original_filename)
    original_ext = original_ext.lower()  # 统一转小写
    
    filename = secure_filename(original_filename)
    
    # 如果 secure_filename 后的文件名没有扩展名或扩展名不匹配，则附加原始扩展名
    _, secured_ext = os.path.splitext(filename)
    if not secured_ext and original_ext:
        filename = filename + original_ext if filename else f"file{original_ext}"
    
    # Add timestamp + random suffix to avoid conflicts (especially for batch uploads)
    import time
    import random
    name, ext = os.path.splitext(filename)
    # 确保 name 不为空
    if not name:
        name = "file"
    # 使用微秒时间戳 + 随机数确保唯一性
    timestamp = int(time.time() * 1000000)  # 微秒级时间戳
    random_suffix = random.randint(1000, 9999)
    filename = f"{name}_{timestamp}_{random_suffix}{ext}"

    
    upload_path = get_project_upload_path(project_id)
    file_path = os.path.join(upload_path, filename)
    
    try:
        file.save(file_path)
        file_size = os.path.getsize(file_path)
        
        # Detect MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        
        # Create database record
        resource = ProjectResource(
            project_id=project_id,
            filename=original_filename,
            file_path=file_path,
            storage_provider='local',
            mime_type=mime_type,
            file_size=file_size,
            parsing_status='pending'
        )
        
        db.session.add(resource)
        db.session.commit()
        
        # 自动索引到知识库（支持的文件类型）
        indexable_extensions = {'.txt', '.md', '.pdf', '.docx'}
        _, ext = os.path.splitext(original_filename)
        
        if ext.lower() in indexable_extensions:
            try:
                from ai.rag.knowledge_base import get_kb_service
                kb_service = get_kb_service()
                index_result = kb_service.index_resource(
                    project_id=project_id,
                    resource_id=resource.id,
                    file_path=file_path,
                    metadata={
                        'filename': original_filename,
                        'mime_type': mime_type,
                        'file_size': file_size
                    }
                )
                
                if index_result.get('success'):
                    resource.parsing_status = 'completed'
                    db.session.commit()
                    logger.info(f"资源 {resource.id} 已索引到知识库: {index_result.get('chunk_count')} 个分块")
                else:
                    resource.parsing_status = 'failed'
                    db.session.commit()
                    logger.warning(f"资源 {resource.id} 索引失败: {index_result.get('error')}")
            except Exception as e:
                logger.error(f"知识库索引失败: {e}")
                resource.parsing_status = 'failed'
                db.session.commit()
        
        return jsonify({
            'message': '文件上传成功',
            'resource': resource.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Clean up file if database operation failed
        if os.path.exists(file_path):
            os.remove(file_path)
        return jsonify({'error': f'文件上传失败: {str(e)}'}), 500


@resources_bp.route('/<int:project_id>/resources/<int:resource_id>', methods=['GET'])
@jwt_or_admin_required
def get_resource(project_id, resource_id):
    """
    Get a specific resource
    """
    user_id = get_current_user_id()
    
    # Verify project ownership
    project = Project.query.filter_by(id=project_id, user_id=user_id, is_deleted=False).first()
    
    if not project:
        return jsonify({'error': '项目不存在或无权访问'}), 404
    
    resource = ProjectResource.query.filter_by(id=resource_id, project_id=project_id, is_deleted=False).first()
    
    if not resource:
        return jsonify({'error': '资源不存在'}), 404
    
    return jsonify({
        'resource': resource.to_dict()
    }), 200


@resources_bp.route('/<int:project_id>/resources/<int:resource_id>', methods=['DELETE'])
@jwt_or_admin_required
def delete_resource(project_id, resource_id):
    """
    Delete a resource file
    """
    user_id = get_current_user_id()
    
    # Verify project ownership
    project = Project.query.filter_by(id=project_id, user_id=user_id, is_deleted=False).first()
    
    if not project:
        return jsonify({'error': '项目不存在或无权访问'}), 404
    
    resource = ProjectResource.query.filter_by(id=resource_id, project_id=project_id, is_deleted=False).first()
    
    if not resource:
        return jsonify({'error': '资源不存在'}), 404
    
    try:
        # 从知识库移除资源（如果已索引）
        try:
            from ai.rag.knowledge_base import get_kb_service
            kb_service = get_kb_service()
            kb_service.remove_resource(project_id, resource_id)
            logger.info(f"资源 {resource_id} 已从知识库移除")
        except Exception as e:
            logger.warning(f"从知识库移除资源失败: {e}")
        
        # 软删除资源
        resource.soft_delete()
        db.session.commit()
        
        return jsonify({
            'message': '资源删除成功',
            'resource': resource.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除资源失败: {str(e)}'}), 500
