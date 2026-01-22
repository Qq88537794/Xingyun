"""
AI API路由
提供统一的问答接口和知识库管理
"""

import logging
import json
import os
from flask import Blueprint, request, jsonify, Response, stream_with_context

from auth_decorator import jwt_or_admin_required, get_current_user_id
from ai.schema import AIRequest, AIResponse, OperationType
from ai.rag.ai_service import get_ai_service
from ai.rag.knowledge_base import get_kb_service

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


# ============== 统一问答接口 ==============

@ai_bp.route('/chat', methods=['POST'])
@jwt_or_admin_required
def chat():
    """
    统一问答接口
    
    这是AI模块的唯一入口，自动处理：
    1. 普通问答
    2. RAG检索增强（如果项目有知识库）
    3. 文档操作（如果AI判断需要）
    4. Agent工具调用（如果启用Agent模式）
    
    Request Body:
    {
        "message": "用户输入（必需）",
        "session_id": "会话ID（可选，用于多轮对话）",
        "project_id": 1,  // 项目ID（可选，用于RAG检索）
        "document_content": "当前文档内容（可选，用于文档操作）",
        "document_id": "文档ID（可选）",
        "selected_text": "选中的文本（可选）",
        "selection_range": {"start": 0, "end": 100},  // 选中范围（可选）
        "enable_rag": true,  // 是否启用RAG（可选，默认自动判断）
        "enable_agent": false,  // 是否启用Agent模式（可选，默认false）
        "stream": false  // 是否流式响应（可选）
    }
    
    Agent模式说明：
    当 enable_agent=true 且提供了 document_content 时，AI将使用工具调用循环来：
    - 读取文档内容 (read_document)
    - 搜索文档内容 (search_document)
    - 编辑文档 (edit_document)
    - 覆写文档 (write_document)
    - 生成大纲、扩写、摘要等
    
    流式响应事件类型（stream=true时）：
    - {"type": "content", "content": "..."}  // 文本内容
    - {"type": "thinking", "iteration": 1}   // Agent思考过程
    - {"type": "tool_call", "name": "...", "arguments": {...}}  // 工具调用
    - {"type": "tool_result", "name": "...", "result": {...}}   // 工具结果
    - {"type": "done", "session_id": "...", ...}  // 完成
    - {"type": "error", "error": "..."}  // 错误
    
    Response:
    {
        "code": 200,
        "message": "success",
        "data": {
            "message": "AI的回复说明",
            "operations": [
                {
                    "operation_type": "generate_outline",
                    "target_file": "文档ID",
                    "content": "操作内容",
                    "position": null,
                    "metadata": {}
                }
            ],
            "sources": [
                {"text": "来源文本...", "score": 0.85, "resource_id": 1}
            ],
            "session_id": "会话ID",
            "tokens_used": 100,
            "requires_confirmation": true,
            "metadata": {
                "agent_iterations": 3,  // Agent模式时的迭代次数
                "agent_tool_calls": [...]  // Agent模式时的工具调用记录
            }
        }
    }
    """
    try:
        data = request.get_json()
        
        # 验证必需参数
        message = data.get('message', '').strip()
        if not message:
            return jsonify({
                'code': 400,
                'message': '消息不能为空'
            }), 400
        
        # 构建请求
        ai_request = AIRequest.from_dict(data)
        
        # 获取AI服务
        ai_service = get_ai_service()
        
        # 检查是否需要流式响应
        if ai_request.stream:
            def generate():
                for chunk in ai_service.chat_stream(ai_request):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )
        
        # 非流式响应
        response = ai_service.chat(ai_request)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': response.to_dict()
        })
    
    except Exception as e:
        logger.error(f"聊天接口错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/chat/history', methods=['GET'])
@jwt_or_admin_required
def get_chat_history():
    """
    获取聊天历史
    
    Query Params:
    - session_id: 会话ID（必需）
    - limit: 返回消息数量（可选，默认50）
    """
    try:
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        
        if not session_id:
            return jsonify({
                'code': 400,
                'message': '需要提供session_id'
            }), 400
        
        ai_service = get_ai_service()
        result = ai_service.get_session_history(session_id, limit)
        
        if "error" in result:
            return jsonify({
                'code': 404,
                'message': result["error"]
            }), 404
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': result
        })
    
    except Exception as e:
        logger.error(f"获取聊天历史错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/chat/sessions/<session_id>', methods=['DELETE'])
@jwt_or_admin_required
def delete_chat_session(session_id):
    """删除聊天会话"""
    try:
        ai_service = get_ai_service()
        ai_service.clear_session(session_id)
        
        return jsonify({
            'code': 200,
            'message': '会话已删除'
        })
    
    except Exception as e:
        logger.error(f"删除会话错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


# ============== 知识库管理接口（调试用） ==============
# 注意：资源的索引和移除已自动集成到资源上传/删除API中
# 这些接口仅用于调试和手动管理

@ai_bp.route('/knowledge-base/<int:project_id>/info', methods=['GET'])
@jwt_or_admin_required
def get_kb_info(project_id):
    """
    获取项目知识库信息
    
    返回知识库的状态、已索引的资源等信息
    """
    try:
        kb_service = get_kb_service()
        info = kb_service.get_kb_info(project_id)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': info
        })
    
    except Exception as e:
        logger.error(f"获取知识库信息错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/knowledge-base/<int:project_id>/search', methods=['POST'])
@jwt_or_admin_required
def search_kb(project_id):
    """
    在知识库中搜索（仅用于调试/测试）
    
    正常使用时，搜索功能集成在chat接口中自动执行
    
    Request Body:
    {
        "query": "搜索内容",
        "top_k": 5
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 5)
        
        if not query:
            return jsonify({
                'code': 400,
                'message': '查询不能为空'
            }), 400
        
        kb_service = get_kb_service()
        results = kb_service.search(project_id, query, top_k)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'results': [
                    {
                        'text': r.text,
                        'score': r.score,
                        'resource_id': r.metadata.get('resource_id'),
                        'metadata': r.metadata
                    }
                    for r in results
                ]
            }
        })
    
    except Exception as e:
        logger.error(f"搜索知识库错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


# ============== 文件操作类型说明接口 ==============

@ai_bp.route('/operations', methods=['GET'])
@jwt_or_admin_required
def list_operations():
    """
    列出所有支持的文件操作类型
    
    用于前端了解AI可能返回的操作类型
    """
    operations = [
        {
            "type": op.value,
            "description": {
                "none": "无操作，仅回复",
                "generate_outline": "生成文档大纲",
                "expand_content": "扩写内容",
                "summarize": "生成摘要",
                "style_transfer": "风格迁移",
                "grammar_check": "语法检查",
                "insert_text": "插入文本",
                "replace_text": "替换文本",
                "delete_text": "删除文本",
                "format_text": "格式化文本"
            }.get(op.value, op.value)
        }
        for op in OperationType
    ]
    
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': operations
    })
