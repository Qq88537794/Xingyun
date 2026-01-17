from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from models import db
from models.folder import Folder
from models.project import Project

folders_bp = Blueprint('folders', __name__, url_prefix='/api/folders')


@folders_bp.route('', methods=['GET'])
@jwt_required()
def get_folders():
    """获取用户的所有文件夹"""
    user_id = get_jwt_identity()
    
    try:
        folders = Folder.query.filter_by(
            user_id=user_id,
            is_deleted=False
        ).order_by(Folder.sort_order, Folder.created_at.desc()).all()
        
        return jsonify({
            'folders': [f.to_dict(include_projects=True) for f in folders]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@folders_bp.route('', methods=['POST'])
@jwt_required()
def create_folder():
    """创建新文件夹"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': '文件夹名称不能为空'}), 400
    
    try:
        folder = Folder(
            user_id=user_id,
            name=name,
            color=data.get('color', 'blue'),
            icon=data.get('icon', 'folder'),
            parent_id=data.get('parent_id'),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(folder)
        db.session.commit()
        
        return jsonify({
            'message': '文件夹创建成功',
            'folder': folder.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/<int:folder_id>', methods=['PUT'])
@jwt_required()
def update_folder(folder_id):
    """更新文件夹"""
    user_id = get_jwt_identity()
    data = request.get_json()
    
    try:
        folder = Folder.query.filter_by(
            id=folder_id,
            user_id=user_id,
            is_deleted=False
        ).first()
        
        if not folder:
            return jsonify({'error': '文件夹不存在'}), 404
        
        if 'name' in data:
            folder.name = data['name'].strip()
        if 'color' in data:
            folder.color = data['color']
        if 'icon' in data:
            folder.icon = data['icon']
        if 'parent_id' in data:
            folder.parent_id = data['parent_id']
        if 'sort_order' in data:
            folder.sort_order = data['sort_order']
        
        db.session.commit()
        
        return jsonify({
            'message': '文件夹更新成功',
            'folder': folder.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/<int:folder_id>', methods=['DELETE'])
@jwt_required()
def delete_folder(folder_id):
    """删除文件夹（软删除）"""
    user_id = get_jwt_identity()
    
    try:
        folder = Folder.query.filter_by(
            id=folder_id,
            user_id=user_id,
            is_deleted=False
        ).first()
        
        if not folder:
            return jsonify({'error': '文件夹不存在'}), 404
        
        # 软删除文件夹
        folder.soft_delete()
        
        # 将文件夹内的项目移到根目录
        Project.query.filter_by(folder_id=folder_id).update({'folder_id': None})
        
        db.session.commit()
        
        return jsonify({'message': '文件夹删除成功'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/<int:folder_id>/projects/<int:project_id>', methods=['POST'])
@jwt_required()
def add_project_to_folder(folder_id, project_id):
    """将项目添加到文件夹"""
    user_id = get_jwt_identity()
    
    try:
        folder = Folder.query.filter_by(
            id=folder_id,
            user_id=user_id,
            is_deleted=False
        ).first()
        
        if not folder:
            return jsonify({'error': '文件夹不存在'}), 404
        
        project = Project.query.filter_by(
            id=project_id,
            user_id=user_id,
            is_deleted=False
        ).first()
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        project.folder_id = folder_id
        db.session.commit()
        
        return jsonify({'message': '项目已添加到文件夹'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@folders_bp.route('/projects/<int:project_id>/remove', methods=['POST'])
@jwt_required()
def remove_project_from_folder(project_id):
    """将项目从文件夹移出（移到根目录）"""
    user_id = get_jwt_identity()
    
    try:
        project = Project.query.filter_by(
            id=project_id,
            user_id=user_id,
            is_deleted=False
        ).first()
        
        if not project:
            return jsonify({'error': '项目不存在'}), 404
        
        project.folder_id = None
        db.session.commit()
        
        return jsonify({'message': '项目已移出文件夹'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
