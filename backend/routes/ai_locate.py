"""
AI智能定位API
使用智谱AI进行语义理解，智能匹配大纲项与文档内容
"""

from flask import Blueprint, request, jsonify
import logging
import sys
import os
from typing import Dict, Any, List
import re

# 添加AI模块路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ai_test_dir = os.path.join(backend_dir, 'AI-test')
if ai_test_dir not in sys.path:
    sys.path.insert(0, ai_test_dir)

from ai.llm.zhipu import ZhipuLLM

logger = logging.getLogger(__name__)

ai_locate_bp = Blueprint('ai_locate', __name__)

# 智谱AI配置
ZHIPU_API_KEY = "577c04cc82aa4951b90094b6f0e6794c.pj5XdD5D8Oc6uvUh"
ZHIPU_MODEL = "glm-4.5-flash"


def extract_paragraphs(text: str, min_length: int = 20) -> List[Dict[str, Any]]:
    """
    提取文档中的段落
    
    Args:
        text: 文档文本
        min_length: 最小段落长度
    
    Returns:
        段落列表，每个段落包含 position, text, length
    """
    paragraphs = []
    
    print(f"\n=== 段落提取调试 ===")
    print(f"文档总长度: {len(text)}")
    print(f"文档前200字符: {text[:200]}")
    print(f"换行符数量: {text.count(chr(10))}")  # \n
    print(f"回车符数量: {text.count(chr(13))}")  # \r
    
    # 按换行符分割段落
    lines = text.split('\n')
    print(f"分割后行数: {len(lines)}")
    print(f"前5行长度: {[len(line) for line in lines[:5]]}")
    
    current_pos = 0
    
    for original_line in lines:
        line = original_line.strip()
        if len(line) >= min_length:
            # 在原始文本中查找这一行的实际位置
            line_start = text.find(line, current_pos)
            if line_start != -1:
                paragraphs.append({
                    'position': line_start,
                    'text': line,
                    'length': len(line)
                })
        # 移动到下一行（使用原始行的长度）
        current_pos += len(original_line) + 1  # +1 for newline
    
    print(f"提取的段落数: {len(paragraphs)}")
    print(f"=== 段落提取结束 ===\n")
    
    return paragraphs


def ai_semantic_match(outline_title: str, paragraphs: List[Dict[str, Any]], top_n: int = 3, full_outline_path: str = None) -> List[Dict[str, Any]]:
    """
    使用AI进行语义匹配
    
    Args:
        outline_title: 大纲标题（如"NAS的典型应用场景"）
        paragraphs: 段落列表
        top_n: 返回前N个最佳匹配
        full_outline_path: 完整的大纲路径（如"8.1 NAS的典型应用场景"）
    
    Returns:
        匹配结果列表
    """
    try:
        # 初始化智谱AI（增加超时时间到120秒）
        llm = ZhipuLLM(api_key=ZHIPU_API_KEY, model_name=ZHIPU_MODEL, timeout=120)
        
        # 如果有完整路径，使用完整路径进行匹配
        search_text = full_outline_path if full_outline_path else outline_title
        
        # 提取关键词用于预筛选
        import re
        # 先按标点符号和连接词分割
        # 移除常见的连接词和标点
        text_cleaned = re.sub(r'[的和与及、，。！？；：""''（）【】《》\s\.]+', ' ', search_text)
        # 然后提取有意义的词
        keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', text_cleaned)
        print(f"清理后文本: {text_cleaned}")
        print(f"原始关键词: {keywords}")
        
        # 过滤并分割长词
        processed_keywords = []
        for k in keywords:
            if len(k) >= 2:
                # 如果是英文或数字，直接添加
                if re.match(r'^[a-zA-Z0-9]+$', k):
                    processed_keywords.append(k)
                # 如果是中文且长度>4，分割成2-3字的词
                elif len(k) > 4:
                    # 添加完整词
                    processed_keywords.append(k)
                    # 添加2字词
                    for i in range(len(k) - 1):
                        processed_keywords.append(k[i:i+2])
                    # 添加3字词
                    for i in range(len(k) - 2):
                        processed_keywords.append(k[i:i+3])
                else:
                    processed_keywords.append(k)
        
        # 去重
        keywords = list(set(processed_keywords))
        print(f"分词后关键词: {keywords}")
        
        # 技术名称优先级更高
        tech_names = ['NAS', 'SAN', 'HDFS', 'CEPH', 'NDB', 'MYSQL', 'HADOOP', 'ORACLE', 'MONGODB']
        important_keywords = [k for k in keywords if k.upper() in tech_names]
        
        print(f"\n=== AI定位调试信息 ===")
        print(f"搜索文本: {search_text}")
        print(f"提取的关键词: {keywords}")
        print(f"重要关键词: {important_keywords}")
        print(f"段落总数: {len(paragraphs)}")
        
        logger.info(f"关键词: {keywords}, 重要关键词: {important_keywords}")
        
        # 预筛选：找出包含关键词的段落
        candidate_paragraphs = []
        
        # 提取标题的核心内容（去除编号）
        title_parts = search_text.split()
        title_content = ' '.join(title_parts[1:]) if len(title_parts) > 1 else search_text
        # 清理标题内容
        title_content_clean = re.sub(r'[的和与及、，。！？；：""''（）【】《》\s\.]+', '', title_content)
        
        for i, para in enumerate(paragraphs):
            text = para['text']
            text_clean = re.sub(r'[的和与及、，。！？；：""''（）【】《》\s\.]+', '', text)
            
            # 计算匹配分数
            matches = sum(1 for kw in keywords if kw.lower() in text.lower() or kw.upper() in text.upper())
            important_matches = sum(1 for kw in important_keywords if kw.upper() in text.upper())
            
            # 检查是否包含完整标题内容（去除标点后）
            has_full_title = title_content_clean.lower() in text_clean.lower() if len(title_content_clean) > 4 else False
            
            # 调试：显示前几个段落的匹配情况
            if i < 5:
                print(f"\n段落 {i}: {text[:100]}...")
                print(f"  匹配关键词数: {matches}/{len(keywords)}")
                print(f"  匹配重要关键词数: {important_matches}/{len(important_keywords)}")
                print(f"  包含完整标题: {has_full_title}")
            
            # 如果有重要关键词但段落中不包含，跳过
            if important_keywords and important_matches == 0:
                if i < 5:
                    print(f"  跳过（缺少重要关键词）")
                continue
            
            # 至少匹配一个关键词
            if matches > 0:
                # 基础分数
                base_score = (matches + important_matches * 2) / (len(keywords) + len(important_keywords) * 2) if (len(keywords) + len(important_keywords) * 2) > 0 else 0
                
                # 如果包含完整标题，大幅提升分数
                if has_full_title:
                    score = min(base_score + 0.5, 1.0)  # 提升0.5分，最高1.0
                else:
                    score = base_score
                
                candidate_paragraphs.append({
                    'index': i,
                    'para': para,
                    'score': score,
                    'matches': matches,
                    'important_matches': important_matches,
                    'has_full_title': has_full_title
                })
                if i < 5:
                    print(f"  ✅ 加入候选列表（分数: {score:.2f}）")
            else:
                if i < 5:
                    print(f"  跳过（无匹配关键词）")
        
        # 按分数排序，取前20个候选段落（从30减少到20）
        candidate_paragraphs.sort(key=lambda x: x['score'], reverse=True)
        top_candidates = candidate_paragraphs[:20]
        
        print(f"\n预筛选结果: 找到 {len(candidate_paragraphs)} 个候选段落")
        if len(top_candidates) > 0:
            print(f"前3个候选段落:")
            for i, c in enumerate(top_candidates[:3]):
                print(f"  {i+1}. 段落{c['index']}: 分数={c['score']:.2f}, 匹配={c['matches']}/{len(keywords)}")
                print(f"     文本: {c['para']['text'][:80]}...")
        
        logger.info(f"预筛选找到 {len(candidate_paragraphs)} 个候选段落，取前 {len(top_candidates)} 个")
        
        # 如果候选段落太少，放宽条件：取所有段落的前50个
        if len(top_candidates) < 5:
            print(f"\n⚠️ 候选段落太少({len(top_candidates)}个)，使用所有段落的前50个")
            logger.warning(f"候选段落太少({len(top_candidates)}个)，使用所有段落的前50个")
            top_candidates = [
                {
                    'index': i,
                    'para': para,
                    'score': 0.5,
                    'matches': 0,
                    'important_matches': 0
                }
                for i, para in enumerate(paragraphs[:50])
            ]
            print(f"降级方案: 使用前50个段落")
        
        if not top_candidates:
            print(f"\n❌ 预筛选未找到任何候选段落")
            logger.warning("预筛选未找到任何候选段落")
            return []
        
        print(f"\n=== 调试信息结束 ===\n")
        
        # 构建提示词（使用筛选后的段落）
        # 为每个段落提供更多上下文
        paragraphs_text = "\n\n".join([
            f"[段落{c['index']}] (位置:{c['para']['position']}, 匹配分数:{c['score']:.2f})\n{c['para']['text'][:600]}"  # 从800减少到600
            for c in top_candidates
        ])
        
        # 提取大纲标题的层级信息
        title_parts = search_text.split()
        title_number = title_parts[0] if title_parts else ''
        title_content = ' '.join(title_parts[1:]) if len(title_parts) > 1 else search_text
        
        prompt = f"""你是一个文档分析专家。请分析以下大纲标题与文档段落的语义相关性。

**大纲标题**: {search_text}
**标题编号**: {title_number}
**标题内容**: {title_content}

**关键要求**:
1. 必须精确匹配标题内容，不要选择相似但不同的段落
2. 如果标题包含技术名称（如{', '.join(important_keywords) if important_keywords else '无'}），段落必须包含该技术名称
3. 优先选择段落开头或附近包含标题内容的段落
4. 注意区分相似标题：
   - "Ceph的统一存储架构" ≠ "Ceph的典型应用场景"
   - "NAS的典型应用场景" ≠ "SAN的典型应用场景"
5. 如果段落中同时出现多个相关内容，选择最接近标题主题的部分

**候选段落**（已预筛选，按匹配分数排序）:
{paragraphs_text}

**任务**: 
1. 仔细阅读每个候选段落的完整内容
2. 找出与大纲标题语义最匹配的段落（最多{top_n}个）
3. 评分标准：
   - 1.0: 段落主题完全匹配标题
   - 0.8-0.9: 段落主要讨论标题内容
   - 0.6-0.7: 段落部分涉及标题内容
   - <0.6: 段落只是提到标题关键词
4. 按相关性从高到低排序

**输出格式**（严格按照JSON格式）:
```json
{{
  "matches": [
    {{
      "paragraph_index": 0,
      "score": 0.95,
      "reason": "包含NAS和典型应用场景，完全匹配"
    }}
  ]
}}
```

注意：
- 只返回JSON，不要有其他文字
- paragraph_index 是段落编号（从上面的[段落X]中获取）
- score必须是0-1之间的数字
- 如果没有合适的段落，返回空数组
"""
        
        # 调用AI
        messages = [{'role': 'user', 'content': prompt}]
        response = llm.chat(messages=messages, temperature=0.3)
        
        logger.info(f"AI响应长度: {len(response.content)}")
        logger.info(f"AI响应前500字符: {response.content[:500]}")
        
        # 解析AI响应
        import json
        
        # 提取JSON部分
        content = response.content.strip()
        
        # 尝试提取JSON代码块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            logger.info("从代码块中提取JSON")
        else:
            # 尝试直接解析
            json_str = content
            logger.info("直接解析JSON")
        
        logger.info(f"JSON字符串: {json_str[:200]}...")
        
        try:
            result = json.loads(json_str)
            logger.info(f"JSON解析成功: {result}")
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始内容: {content}")
            # 降级到关键词匹配
            return keyword_fallback_match(outline_title, paragraphs, top_n, full_outline_path)
        
        matches = result.get('matches', [])
        logger.info(f"AI返回 {len(matches)} 个匹配")
        
        # 转换为标准格式
        matched_results = []
        for match in matches[:top_n]:
            idx = match.get('paragraph_index', 0)
            # idx 是原始段落列表中的索引（从提示词的[段落X]中获取）
            # 需要在 top_candidates 中找到对应的候选段落
            candidate = next((c for c in top_candidates if c['index'] == idx), None)
            if candidate:
                para = candidate['para']
                matched_results.append({
                    'position': para['position'],
                    'text': para['text'][:200],
                    'score': match.get('score', 0.5),
                    'length': min(len(para['text']), 200),
                    'reason': match.get('reason', '')
                })
            else:
                logger.warning(f"AI返回的段落索引 {idx} 不在候选列表中")
        
        return matched_results
        
    except Exception as e:
        logger.error(f"AI语义匹配失败: {str(e)}", exc_info=True)
        # 降级到关键词匹配
        return keyword_fallback_match(outline_title, paragraphs, top_n)


def keyword_fallback_match(outline_title: str, paragraphs: List[Dict[str, Any]], top_n: int = 3, full_outline_path: str = None) -> List[Dict[str, Any]]:
    """
    关键词匹配（降级方案）
    
    Args:
        outline_title: 大纲标题
        paragraphs: 段落列表
        top_n: 返回前N个最佳匹配
        full_outline_path: 完整的大纲路径
    
    Returns:
        匹配结果列表
    """
    logger.info("使用关键词匹配降级方案")
    
    # 使用完整路径或标题
    search_text = full_outline_path if full_outline_path else outline_title
    
    # 提取关键词（先清理停用词）
    text_cleaned = re.sub(r'[的和与及、，。！？；：""''（）【】《》\s\.]+', ' ', search_text)
    keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', text_cleaned)
    
    # 过滤并分割长词
    processed_keywords = []
    for k in keywords:
        if len(k) >= 2:
            # 如果是英文或数字，直接添加
            if re.match(r'^[a-zA-Z0-9]+$', k):
                processed_keywords.append(k)
            # 如果是中文且长度>4，分割成2-3字的词
            elif len(k) > 4:
                # 添加完整词
                processed_keywords.append(k)
                # 添加2字词
                for i in range(len(k) - 1):
                    processed_keywords.append(k[i:i+2])
                # 添加3字词
                for i in range(len(k) - 2):
                    processed_keywords.append(k[i:i+3])
            else:
                processed_keywords.append(k)
    
    # 去重
    keywords = list(set(processed_keywords))
    
    # 提取重要的技术名称（优先级更高）
    tech_names = ['NAS', 'SAN', 'HDFS', 'CEPH', 'NDB', 'MYSQL', 'HADOOP', 'ORACLE', 'MONGODB']
    important_keywords = [k for k in keywords if k.upper() in tech_names]
    
    if not keywords:
        return []
    
    logger.info(f"关键词: {keywords}, 重要关键词: {important_keywords}")
    
    # 计算每个段落的匹配分数
    scored_paragraphs = []
    for para in paragraphs:
        text = para['text']
        
        # 计算普通关键词匹配
        matches = sum(1 for kw in keywords if kw in text)
        
        # 计算重要关键词匹配（权重更高）
        important_matches = sum(1 for kw in important_keywords if kw in text)
        
        # 如果有重要关键词但段落中不包含，分数大幅降低
        if important_keywords and important_matches == 0:
            score = 0.1 * (matches / len(keywords))
        else:
            # 综合分数：普通关键词 + 重要关键词（权重2倍）
            score = (matches + important_matches * 2) / (len(keywords) + len(important_keywords) * 2)
        
        if score > 0:
            scored_paragraphs.append({
                'position': para['position'],
                'text': para['text'][:200],
                'score': score,
                'length': min(len(para['text']), 200),
                'reason': f'关键词匹配: {matches}/{len(keywords)}, 重要关键词: {important_matches}/{len(important_keywords)}'
            })
    
    # 按分数排序
    scored_paragraphs.sort(key=lambda x: x['score'], reverse=True)
    
    return scored_paragraphs[:top_n]


@ai_locate_bp.route('/api/ai/locate', methods=['POST'])
def ai_locate():
    """
    AI智能定位端点
    
    请求体:
    {
        "outline_title": "大纲标题",
        "document_text": "文档全文",
        "full_outline_path": "完整大纲路径（可选）",  // 如 "8. 应用场景 > 8.1 NAS的典型应用场景"
        "top_n": 3,  // 可选，返回前N个匹配
        "use_ai": true  // 可选，是否使用AI语义匹配（默认true）
    }
    
    响应:
    {
        "success": true,
        "method": "ai_semantic",  // 或 "keyword_fallback"
        "matches": [
            {
                "position": 1234,
                "text": "匹配的段落文本...",
                "score": 0.95,
                "length": 150,
                "reason": "匹配原因说明"
            }
        ]
    }
    """
    try:
        # 获取当前用户ID（如果有JWT token）
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        current_user_id = None
        try:
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
        except:
            pass  # 没有token也可以使用定位功能
        
        data = request.get_json()
        
        outline_title = data.get('outline_title', '')
        document_text = data.get('document_text', '')
        full_outline_path = data.get('full_outline_path', None)
        top_n = data.get('top_n', 3)
        use_ai = data.get('use_ai', True)
        project_id = data.get('project_id')  # 可选的项目ID
        
        if not outline_title or not document_text:
            return jsonify({
                'success': False,
                'error': '缺少必要参数'
            }), 400
        
        logger.info(f"AI定位请求: {outline_title} (完整路径: {full_outline_path}, use_ai={use_ai})")
        
        # 提取段落
        paragraphs = extract_paragraphs(document_text)
        
        if not paragraphs:
            return jsonify({
                'success': False,
                'error': '文档中没有找到有效段落'
            })
        
        # 选择匹配方法
        if use_ai:
            matches = ai_semantic_match(outline_title, paragraphs, top_n, full_outline_path)
            method = 'ai_semantic'
        else:
            matches = keyword_fallback_match(outline_title, paragraphs, top_n, full_outline_path)
            method = 'keyword_fallback'
        
        if matches:
            logger.info(f"找到 {len(matches)} 个匹配，最佳分数: {matches[0]['score']:.2f}")
            
            # 保存到数据库历史记录（如果有用户ID）
            if current_user_id:
                try:
                    from models import AIChatHistory
                    
                    # 构建响应摘要
                    response_summary = f"找到{len(matches)}个匹配，最佳匹配位置: {matches[0]['position']}, 分数: {matches[0]['score']:.2f}"
                    
                    AIChatHistory.save_chat_history(
                        user_id=current_user_id,
                        request_type='locate',
                        ai_response=response_summary,
                        user_message=f"定位大纲: {outline_title}",
                        project_id=project_id
                    )
                except Exception as e:
                    logger.error(f"保存定位历史失败: {e}")
                    # 不影响主流程
            
            return jsonify({
                'success': True,
                'method': method,
                'matches': matches
            })
        else:
            logger.warning(f"未找到匹配: {outline_title}")
            return jsonify({
                'success': False,
                'error': '未找到匹配的段落',
                'method': method
            })
    
    except Exception as e:
        logger.error(f"AI定位失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
