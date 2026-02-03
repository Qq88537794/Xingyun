import os
import uuid
from flask import Blueprint, request, jsonify, current_app, url_for
from werkzeug.utils import secure_filename
from flask_jwt_extended import jwt_required

images_bp = Blueprint('images', __name__, url_prefix='/api/images')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@images_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file and allowed_file(file.filename):
        # 生成安全的文件名
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        save_path = os.path.join(current_app.config['EDITOR_IMAGE_FOLDER'], filename)
        
        try:
            file.save(save_path)
            
            # 返回完整的URL
            # 这里我们需要知道服务器的基础URL，或者返回相对路径
            # 假设我们在app.py中配置了 /editor_images/<filename> 的路由
            
            # 获取host url (e.g. http://localhost:5000)
            # url = url_for('uploaded_image', filename=filename, _external=True) 
            # url_for requires the view function to be defined. We'll define it in app.py
            
            url = f"/editor_images/{filename}"
            
            return jsonify({
                'url': url,
                'filename': filename
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
            
    return jsonify({'error': 'File type not allowed'}), 400
