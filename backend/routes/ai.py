"""
AI相关API路由
提供智能文档生成、RAG问答、内容处理等接口
"""

import logging
import uuid
from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt_identity
import json

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')


# ============== 辅助函数 ==============

def get_ai_services():
    """
    获取AI服务实例
    延迟导入，避免循环依赖
    """
    from ai import (
        LLMFactory, get_llm_factory, init_llm_factory,
        RAGEngine, RAGConfig,
        PromptManager, ContextManager, QualityController
    )
    from ai.prompts.manager import get_prompt_manager, get_prompt_builder
    from ai.prompts.context import get_context_manager
    from ai.prompts.quality import get_quality_controller
    
    return {
        'llm_factory': get_llm_factory,
        'prompt_manager': get_prompt_manager,
        'prompt_builder': get_prompt_builder,
        'context_manager': get_context_manager,
        'quality_controller': get_quality_controller,
        'RAGEngine': RAGEngine,
        'RAGConfig': RAGConfig,
    }


def get_or_init_llm():
    """获取或初始化LLM工厂"""
    from ai.llm.factory import get_llm_factory, init_llm_factory
    from config import Config
    
    factory = get_llm_factory()
    
    # 如果工厂还没有注册LLM，初始化它
    if not factory._llms:
        # 从配置中获取API密钥
        zhipu_key = getattr(Config, 'ZHIPU_API_KEY', None)
        gemini_key = getattr(Config, 'GEMINI_API_KEY', None)
        
        init_llm_factory(
            zhipu_api_key=zhipu_key,
            gemini_api_key=gemini_key,
            default_provider='zhipu'
        )
    
    return factory


# ============== 聊天相关API ==============

@ai_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    """
    聊天接口
    
    Request Body:
    {
        "message": "用户消息",
        "session_id": "会话ID(可选)",
        "context": "额外上下文(可选)",
        "model": "模型名称(可选)",
        "stream": false
    }
    
    Response:
    {
        "code": 200,
        "message": "success",
        "data": {
            "reply": "AI回复",
            "session_id": "会话ID",
            "tokens_used": 100
        }
    }
    """
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        session_id = data.get('session_id') or str(uuid.uuid4())
        context = data.get('context', '')
        model = data.get('model')
        stream = data.get('stream', False)
        
        if not user_message:
            return jsonify({
                'code': 400,
                'message': '消息不能为空'
            }), 400
        
        # 获取服务
        from ai.prompts.context import get_context_manager
        context_manager = get_context_manager()
        
        # 获取或创建会话上下文
        conv_context = context_manager.get_or_create_context(
            session_id=session_id,
            system_prompt="你是行云智能文档工作站的AI助手，专注于帮助用户进行文档创作、内容优化和知识问答。请提供专业、准确、有帮助的回答。"
        )
        
        # 添加用户消息
        conv_context.add_message('user', user_message)
        
        # 构建完整的消息列表
        messages = conv_context.get_messages_for_llm()
        
        # 如果有额外上下文，添加到用户消息中
        if context:
            messages[-1]['content'] = f"参考资料:\n{context}\n\n用户问题: {user_message}"
        
        # 获取LLM
        factory = get_or_init_llm()
        llm = factory.get_llm(model)
        
        if stream:
            # 流式响应
            def generate():
                full_response = ""
                for chunk in llm.stream(messages):
                    if chunk.content:
                        full_response += chunk.content
                        yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"
                
                # 保存助手回复
                conv_context.add_message('assistant', full_response)
                yield f"data: {json.dumps({'done': True, 'session_id': session_id}, ensure_ascii=False)}\n\n"
            
            return Response(
                stream_with_context(generate()),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'X-Accel-Buffering': 'no'
                }
            )
        else:
            # 非流式响应
            response = llm.chat(messages)
            
            # 保存助手回复
            conv_context.add_message('assistant', response.content)
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'reply': response.content,
                    'session_id': session_id,
                    'tokens_used': response.usage.total_tokens if response.usage else 0
                }
            })
    
    except Exception as e:
        logger.error(f"聊天接口错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/chat/history', methods=['GET'])
@jwt_required()
def get_chat_history():
    """
    获取聊天历史
    
    Query Params:
    - session_id: 会话ID
    - limit: 返回消息数量限制
    """
    try:
        session_id = request.args.get('session_id')
        limit = int(request.args.get('limit', 50))
        
        if not session_id:
            return jsonify({
                'code': 400,
                'message': '需要提供session_id'
            }), 400
        
        from ai.prompts.context import get_context_manager
        context_manager = get_context_manager()
        
        if session_id not in context_manager._sessions:
            return jsonify({
                'code': 404,
                'message': '会话不存在'
            }), 404
        
        context = context_manager._sessions[session_id]
        messages = context.get_recent_messages(limit)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'session_id': session_id,
                'messages': [m.to_dict() for m in messages],
                'total_tokens': context.total_tokens
            }
        })
    
    except Exception as e:
        logger.error(f"获取聊天历史错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/chat/sessions', methods=['GET'])
@jwt_required()
def list_chat_sessions():
    """列出所有聊天会话"""
    try:
        from ai.prompts.context import get_context_manager
        context_manager = get_context_manager()
        
        sessions = context_manager.list_sessions()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': sessions
        })
    
    except Exception as e:
        logger.error(f"列出会话错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/chat/sessions/<session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    """删除聊天会话"""
    try:
        from ai.prompts.context import get_context_manager
        context_manager = get_context_manager()
        
        context_manager.delete_session(session_id)
        
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


# ============== 内容生成API ==============

@ai_bp.route('/generate/outline', methods=['POST'])
@jwt_required()
def generate_outline():
    """
    生成文档大纲
    
    Request Body:
    {
        "topic": "文档主题",
        "context": "参考资料(可选)",
        "requirements": "具体要求(可选)",
        "style": "风格要求(可选)"
    }
    """
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({
                'code': 400,
                'message': '主题不能为空'
            }), 400
        
        from ai.prompts.manager import get_prompt_builder
        builder = get_prompt_builder()
        
        prompt = builder.outline(
            topic=topic,
            context=data.get('context'),
            requirements=data.get('requirements'),
            style=data.get('style')
        )
        
        factory = get_or_init_llm()
        llm = factory.get_llm()
        
        response = llm.chat([{'role': 'user', 'content': prompt}])
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'outline': response.content,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
        })
    
    except Exception as e:
        logger.error(f"生成大纲错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/generate/expand', methods=['POST'])
@jwt_required()
def expand_content():
    """
    扩展内容
    
    Request Body:
    {
        "content": "待扩展内容",
        "context": "参考资料(可选)",
        "ratio": "扩展倍数(可选,默认2-3)",
        "tone": "语言风格(可选)",
        "focus_areas": ["重点方向1", "重点方向2"]
    }
    """
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'code': 400,
                'message': '内容不能为空'
            }), 400
        
        from ai.prompts.manager import get_prompt_builder
        builder = get_prompt_builder()
        
        prompt = builder.expand(
            content=content,
            context=data.get('context'),
            ratio=data.get('ratio', '2-3'),
            tone=data.get('tone', '专业、正式'),
            focus_areas=data.get('focus_areas')
        )
        
        factory = get_or_init_llm()
        llm = factory.get_llm()
        
        response = llm.chat([{'role': 'user', 'content': prompt}])
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'expanded_content': response.content,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
        })
    
    except Exception as e:
        logger.error(f"扩展内容错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/generate/summarize', methods=['POST'])
@jwt_required()
def summarize_content():
    """
    生成摘要
    
    Request Body:
    {
        "content": "待摘要内容",
        "length": "摘要长度(可选)",
        "include_keywords": true,
        "focus_points": "重点关注方向(可选)"
    }
    """
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'code': 400,
                'message': '内容不能为空'
            }), 400
        
        from ai.prompts.manager import get_prompt_builder
        builder = get_prompt_builder()
        
        prompt = builder.summarize(
            content=content,
            length=data.get('length', '200-300字'),
            include_keywords=data.get('include_keywords', True),
            focus_points=data.get('focus_points')
        )
        
        factory = get_or_init_llm()
        llm = factory.get_llm()
        
        response = llm.chat([{'role': 'user', 'content': prompt}])
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'summary': response.content,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
        })
    
    except Exception as e:
        logger.error(f"生成摘要错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/generate/style-transfer', methods=['POST'])
@jwt_required()
def style_transfer():
    """
    风格迁移
    
    Request Body:
    {
        "content": "原始内容",
        "target_style": "目标风格",
        "style_description": "风格详细描述(可选)",
        "preserve_structure": true
    }
    """
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        target_style = data.get('target_style', '').strip()
        
        if not content or not target_style:
            return jsonify({
                'code': 400,
                'message': '内容和目标风格不能为空'
            }), 400
        
        from ai.prompts.manager import get_prompt_builder
        builder = get_prompt_builder()
        
        prompt = builder.style_transfer(
            content=content,
            target_style=target_style,
            style_description=data.get('style_description', ''),
            preserve_structure=data.get('preserve_structure', True)
        )
        
        factory = get_or_init_llm()
        llm = factory.get_llm()
        
        response = llm.chat([{'role': 'user', 'content': prompt}])
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'transferred_content': response.content,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
        })
    
    except Exception as e:
        logger.error(f"风格迁移错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/generate/grammar-check', methods=['POST'])
@jwt_required()
def grammar_check():
    """
    语法检查
    
    Request Body:
    {
        "content": "待检查内容",
        "check_style": false
    }
    """
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'code': 400,
                'message': '内容不能为空'
            }), 400
        
        from ai.prompts.manager import get_prompt_builder
        builder = get_prompt_builder()
        
        prompt = builder.grammar_check(
            content=content,
            check_style=data.get('check_style', False)
        )
        
        factory = get_or_init_llm()
        llm = factory.get_llm()
        
        response = llm.chat([{'role': 'user', 'content': prompt}])
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'result': response.content,
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
        })
    
    except Exception as e:
        logger.error(f"语法检查错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


# ============== RAG相关API ==============

# RAG引擎实例(延迟初始化)
_rag_engine = None

def get_rag_engine():
    """获取RAG引擎实例"""
    global _rag_engine
    
    if _rag_engine is None:
        from ai.rag import RAGEngine, RAGConfig
        from config import Config
        
        config = RAGConfig(
            chunk_size=getattr(Config, 'RAG_CHUNK_SIZE', 500),
            chunk_overlap=getattr(Config, 'RAG_CHUNK_OVERLAP', 50),
            top_k=getattr(Config, 'RAG_TOP_K', 5),
            use_reranker=getattr(Config, 'RAG_USE_RERANKER', True),
            hybrid_search=getattr(Config, 'RAG_HYBRID_SEARCH', True),
        )
        
        _rag_engine = RAGEngine(
            embedding_provider=getattr(Config, 'EMBEDDING_PROVIDER', 'zhipu'),
            embedding_api_key=getattr(Config, 'ZHIPU_API_KEY', None) or getattr(Config, 'GEMINI_API_KEY', None),
            collection_name='xingyun_docs',
            persist_directory=getattr(Config, 'RAG_PERSIST_DIR', None),
            config=config
        )
    
    return _rag_engine


@ai_bp.route('/rag/index', methods=['POST'])
@jwt_required()
def rag_index_document():
    """
    索引文档到RAG系统
    
    Request Body:
    {
        "text": "文档文本",
        "doc_id": "文档ID",
        "metadata": {"key": "value"}
    }
    或上传文件
    """
    try:
        rag_engine = get_rag_engine()
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            # 文件上传
            file = request.files.get('file')
            doc_id = request.form.get('doc_id')
            metadata_str = request.form.get('metadata', '{}')
            
            if not file:
                return jsonify({
                    'code': 400,
                    'message': '请上传文件'
                }), 400
            
            import tempfile
            import os
            
            # 保存临时文件
            suffix = os.path.splitext(file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                file.save(tmp.name)
                tmp_path = tmp.name
            
            try:
                metadata = json.loads(metadata_str)
                metadata['filename'] = file.filename
                
                indexed = rag_engine.index_file(
                    file_path=tmp_path,
                    doc_id=doc_id,
                    metadata=metadata
                )
                
                return jsonify({
                    'code': 200,
                    'message': 'success',
                    'data': {
                        'doc_id': indexed.doc_id,
                        'chunk_count': indexed.chunk_count,
                        'filename': file.filename
                    }
                })
            finally:
                os.unlink(tmp_path)
        else:
            # JSON请求
            data = request.get_json()
            text = data.get('text', '').strip()
            doc_id = data.get('doc_id')
            metadata = data.get('metadata', {})
            
            if not text:
                return jsonify({
                    'code': 400,
                    'message': '文本内容不能为空'
                }), 400
            
            indexed = rag_engine.index_text(
                text=text,
                doc_id=doc_id,
                metadata=metadata
            )
            
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'doc_id': indexed.doc_id,
                    'chunk_count': indexed.chunk_count
                }
            })
    
    except Exception as e:
        logger.error(f"索引文档错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/rag/search', methods=['POST'])
@jwt_required()
def rag_search():
    """
    RAG检索
    
    Request Body:
    {
        "query": "检索查询",
        "top_k": 5,
        "filters": {"key": "value"}
    }
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 5)
        filters = data.get('filters')
        
        if not query:
            return jsonify({
                'code': 400,
                'message': '查询不能为空'
            }), 400
        
        rag_engine = get_rag_engine()
        
        results = rag_engine.search(
            query=query,
            top_k=top_k,
            filters=filters
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'results': [
                    {
                        'text': r.text,
                        'score': r.score,
                        'doc_id': r.doc_id,
                        'metadata': r.metadata
                    }
                    for r in results
                ]
            }
        })
    
    except Exception as e:
        logger.error(f"RAG检索错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/rag/qa', methods=['POST'])
@jwt_required()
def rag_qa():
    """
    RAG问答
    
    Request Body:
    {
        "question": "问题",
        "session_id": "会话ID(可选)",
        "top_k": 5
    }
    """
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        session_id = data.get('session_id')
        top_k = data.get('top_k', 5)
        
        if not question:
            return jsonify({
                'code': 400,
                'message': '问题不能为空'
            }), 400
        
        rag_engine = get_rag_engine()
        
        # 检索相关内容
        results = rag_engine.search(query=question, top_k=top_k)
        
        # 构建上下文
        context = rag_engine.build_context(results)
        
        # 构建RAG问答提示
        from ai.prompts.manager import get_prompt_builder
        builder = get_prompt_builder()
        
        # 获取对话历史
        chat_history = None
        if session_id:
            from ai.prompts.context import get_context_manager
            context_manager = get_context_manager()
            messages = context_manager.get_messages(session_id, include_system=False)
            if messages:
                chat_history = '\n'.join([
                    f"{'用户' if m['role'] == 'user' else '助手'}: {m['content'][:200]}"
                    for m in messages[-6:]
                ])
        
        prompt = builder.rag_qa(
            question=question,
            context=context,
            chat_history=chat_history
        )
        
        # 调用LLM
        factory = get_or_init_llm()
        llm = factory.get_llm()
        
        response = llm.chat([{'role': 'user', 'content': prompt}])
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'answer': response.content,
                'sources': [
                    {
                        'text': r.text[:200] + '...' if len(r.text) > 200 else r.text,
                        'score': r.score,
                        'doc_id': r.doc_id
                    }
                    for r in results[:3]
                ],
                'tokens_used': response.usage.total_tokens if response.usage else 0
            }
        })
    
    except Exception as e:
        logger.error(f"RAG问答错误: {e}", exc_info=True)
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/rag/delete/<doc_id>', methods=['DELETE'])
@jwt_required()
def rag_delete_document(doc_id):
    """删除已索引的文档"""
    try:
        rag_engine = get_rag_engine()
        
        rag_engine.delete_document(doc_id)
        
        return jsonify({
            'code': 200,
            'message': '文档已删除'
        })
    
    except Exception as e:
        logger.error(f"删除文档错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


# ============== 质量控制API ==============

@ai_bp.route('/quality/check', methods=['POST'])
@jwt_required()
def check_content_quality():
    """
    检查内容质量
    
    Request Body:
    {
        "content": "待检查内容",
        "check_repetition": true,
        "check_coherence": true,
        "check_completeness": true
    }
    """
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'code': 400,
                'message': '内容不能为空'
            }), 400
        
        from ai.prompts.quality import get_quality_controller
        controller = get_quality_controller()
        
        report = controller.check_quality(
            content=content,
            check_repetition=data.get('check_repetition', True),
            check_coherence=data.get('check_coherence', True),
            check_completeness=data.get('check_completeness', True)
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': report.to_dict()
        })
    
    except Exception as e:
        logger.error(f"质量检查错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/quality/improve', methods=['POST'])
@jwt_required()
def improve_content_quality():
    """
    改进内容质量
    
    Request Body:
    {
        "content": "待改进内容",
        "auto_fix": true
    }
    """
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({
                'code': 400,
                'message': '内容不能为空'
            }), 400
        
        from ai.prompts.quality import get_quality_controller
        controller = get_quality_controller()
        
        improved_content, report = controller.improve_content(
            content=content,
            auto_fix=data.get('auto_fix', True)
        )
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'improved_content': improved_content,
                'quality_report': report.to_dict()
            }
        })
    
    except Exception as e:
        logger.error(f"改进质量错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


# ============== 模型管理API ==============

@ai_bp.route('/models', methods=['GET'])
@jwt_required()
def list_models():
    """列出可用的AI模型"""
    try:
        factory = get_or_init_llm()
        
        models = []
        for name, llm in factory._llms.items():
            models.append({
                'name': name,
                'provider': llm.provider.value,
                'model': llm.model,
                'is_default': name == factory._default_llm
            })
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'models': models,
                'default': factory._default_llm
            }
        })
    
    except Exception as e:
        logger.error(f"列出模型错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500


@ai_bp.route('/models/stats', methods=['GET'])
@jwt_required()
def get_model_stats():
    """获取模型使用统计"""
    try:
        factory = get_or_init_llm()
        
        stats = {}
        for name, llm in factory._llms.items():
            stats[name] = llm.get_stats()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': stats
        })
    
    except Exception as e:
        logger.error(f"获取统计错误: {e}")
        return jsonify({
            'code': 500,
            'message': f'服务器错误: {str(e)}'
        }), 500
