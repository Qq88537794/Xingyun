from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db
from models.project import Project

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


@projects_bp.route('', methods=['GET'])
@jwt_required()
def list_projects():
    """
    Get all projects for the current user
    
    Query params:
        include_deleted: bool (default: false) - Include soft-deleted projects
    """
    user_id = int(get_jwt_identity())
    include_deleted = request.args.get('include_deleted', 'false').lower() == 'true'
    
    query = Project.query.filter_by(user_id=user_id)
    
    if not include_deleted:
        query = query.filter_by(is_deleted=False)
    
    projects = query.order_by(Project.created_at.desc()).all()
    
    return jsonify({
        'projects': [p.to_dict() for p in projects],
        'total': len(projects)
    }), 200


@projects_bp.route('', methods=['POST'])
@jwt_required()
def create_project():
    """
    Create a new project
    
    Request JSON:
    {
        "name": "string",
        "description": "string" (optional)
    }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'error': '项目名称不能为空'}), 400
    
    if len(name) > 128:
        return jsonify({'error': '项目名称不能超过128个字符'}), 400
    
    project = Project(
        user_id=user_id,
        name=name,
        description=description if description else None,
        status='active'
    )
    
    try:
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'message': '项目创建成功',
            'project': project.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建项目失败: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>', methods=['GET'])
@jwt_required()
def get_project(project_id):
    """
    Get a specific project by ID
    
    Query params:
        include_resources: bool (default: false) - Include project resources
    """
    user_id = int(get_jwt_identity())
    include_resources = request.args.get('include_resources', 'false').lower() == 'true'
    
    project = Project.query.filter_by(id=project_id, user_id=user_id, is_deleted=False).first()
    
    if not project:
        return jsonify({'error': '项目不存在或无权访问'}), 404
    
    return jsonify({
        'project': project.to_dict(include_resources=include_resources)
    }), 200


@projects_bp.route('/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    """
    Update a project
    
    Request JSON:
    {
        "name": "string" (optional),
        "description": "string" (optional),
        "status": "active" | "archived" (optional)
    }
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    if not data:
        return jsonify({'error': '请求数据不能为空'}), 400
    
    project = Project.query.filter_by(id=project_id, user_id=user_id, is_deleted=False).first()
    
    if not project:
        return jsonify({'error': '项目不存在或无权访问'}), 404
    
    # Update fields if provided
    if 'name' in data:
        name = data['name'].strip()
        if not name:
            return jsonify({'error': '项目名称不能为空'}), 400
        if len(name) > 128:
            return jsonify({'error': '项目名称不能超过128个字符'}), 400
        project.name = name
    
    if 'description' in data:
        project.description = data['description'].strip() if data['description'] else None
    
    if 'status' in data:
        if data['status'] not in ['active', 'archived']:
            return jsonify({'error': '状态值无效，只能为 active 或 archived'}), 400
        project.status = data['status']
    
    try:
        db.session.commit()
        
        return jsonify({
            'message': '项目更新成功',
            'project': project.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新项目失败: {str(e)}'}), 500


@projects_bp.route('/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    """
    Soft delete a project
    """
    user_id = int(get_jwt_identity())
    
    project = Project.query.filter_by(id=project_id, user_id=user_id, is_deleted=False).first()
    
    if not project:
        return jsonify({'error': '项目不存在或无权访问'}), 404
    
    try:
        project.soft_delete()
        db.session.commit()
        
        return jsonify({
            'message': '项目删除成功',
            'project': project.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除项目失败: {str(e)}'}), 500
