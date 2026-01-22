"""
AI模块功能测试脚本
测试AI核心功能，不依赖数据库
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("AI模块功能测试")
print("=" * 60)

# 1. 测试环境配置
print("\n[1] 检查环境配置...")
zhipu_key = os.getenv('ZHIPU_API_KEY')
gemini_key = os.getenv('GEMINI_API_KEY')
llm_provider = os.getenv('LLM_PROVIDER', 'zhipu')

print(f"  - LLM_PROVIDER: {llm_provider}")
print(f"  - ZHIPU_API_KEY: {'✓ 已配置' if zhipu_key else '✗ 未配置'}")
print(f"  - GEMINI_API_KEY: {'✓ 已配置' if gemini_key else '✗ 未配置'}")

# 2. 测试LLM导入
print("\n[2] 测试LLM模块导入...")
try:
    from ai.llm.factory import get_llm_factory
    from ai.llm.zhipu import ZhipuLLM
    from ai.llm.gemini import GeminiLLM
    print("  ✓ LLM模块导入成功")
except Exception as e:
    print(f"  ✗ LLM模块导入失败: {e}")
    sys.exit(1)

# 3. 测试Agent模块导入
print("\n[3] 测试Agent模块导入...")
try:
    from ai.agent import (
        AgentProcessor, ToolRegistry, 
        ReadDocumentTool, WriteDocumentTool,
        create_default_registry
    )
    print("  ✓ Agent模块导入成功")
except Exception as e:
    print(f"  ✗ Agent模块导入失败: {e}")
    sys.exit(1)

# 4. 测试Schema导入
print("\n[4] 测试Schema模块导入...")
try:
    from ai.schema import AIRequest, AIResponse, OperationType
    print("  ✓ Schema模块导入成功")
except Exception as e:
    print(f"  ✗ Schema模块导入失败: {e}")
    sys.exit(1)

# 5. 测试LLM初始化
print("\n[5] 测试LLM初始化...")
try:
    factory = get_llm_factory()
    llm = factory.get_llm()
    print(f"  ✓ LLM初始化成功: {llm.__class__.__name__}")
    print(f"    - Provider: {llm.provider.value}")
    print(f"    - Model: {llm.model_name}")
except Exception as e:
    print(f"  ✗ LLM初始化失败: {e}")
    sys.exit(1)

# 6. 测试简单对话
print("\n[6] 测试简单LLM对话...")
try:
    response = llm.simple_chat(
        prompt="请用一句话介绍你自己",
        system_prompt="你是一个AI助手"
    )
    print(f"  ✓ 对话测试成功")
    print(f"    回复: {response[:100]}..." if len(response) > 100 else f"    回复: {response}")
except Exception as e:
    print(f"  ✗ 对话测试失败: {e}")

# 7. 测试工具调用支持
print("\n[7] 测试工具调用支持...")
try:
    # 创建简单的文档操作函数
    test_doc_content = "这是一个测试文档。"
    
    def get_doc(doc_id):
        return test_doc_content
    
    def write_doc(doc_id, content):
        return True
    
    # 创建工具注册表
    registry = create_default_registry(get_doc, write_doc)
    tools = registry.to_llm_tools()
    
    print(f"  ✓ 工具注册成功，共{len(tools)}个工具:")
    for tool in tools[:3]:  # 只显示前3个
        func = tool.get('function', {})
        print(f"    - {func.get('name', 'unknown')}")
    
except Exception as e:
    print(f"  ✗ 工具注册失败: {e}")

# 8. 测试Agent工具调用（如果LLM支持）
print("\n[8] 测试Agent工具调用...")
try:
    if hasattr(llm, 'chat_with_tools'):
        # 准备测试消息
        test_messages = [
            {"role": "user", "content": "请读取文档内容"}
        ]
        
        # 调用工具
        response = llm.chat_with_tools(
            system_prompt="你是一个文档助手，可以使用工具操作文档。",
            messages=test_messages,
            tools=tools,
            temperature=0.7
        )
        
        print(f"  ✓ 工具调用测试成功")
        print(f"    - Finish Reason: {response.get('finish_reason')}")
        print(f"    - Tool Calls: {len(response.get('tool_calls', []))}个")
        if response.get('content'):
            content_preview = response['content'][:80]
            print(f"    - 回复预览: {content_preview}...")
    else:
        print(f"  ⚠ 当前LLM不支持原生工具调用，将使用模拟实现")
        
except Exception as e:
    print(f"  ✗ 工具调用测试失败: {e}")

# 9. 测试AIService（不依赖数据库）
print("\n[9] 测试AIService...")
try:
    from ai.rag.ai_service import AIService
    
    service = AIService()
    print("  ✓ AIService初始化成功")
    
    # 测试Simple模式
    request = AIRequest(
        message="你好，请简单介绍一下你的功能",
        enable_agent=False
    )
    
    response = service.chat(request)
    print(f"  ✓ Simple模式测试成功")
    print(f"    回复: {response.message[:100]}...")
    
except Exception as e:
    print(f"  ✗ AIService测试失败: {e}")
    import traceback
    traceback.print_exc()

# 10. 测试Agent模式（带文档内容）
print("\n[10] 测试Agent模式...")
try:
    test_document = """
# 测试文档

这是一个用于测试的Markdown文档。

## 第一章
这是第一章的内容。

## 第二章
这是第二章的内容。
"""
    
    request = AIRequest(
        message="请帮我总结这个文档的主要内容",
        document_content=test_document,
        document_id="test_doc",
        enable_agent=True
    )
    
    response = service.chat(request)
    print(f"  ✓ Agent模式测试成功")
    print(f"    - 迭代次数: {response.metadata.get('agent_iterations', 0)}")
    print(f"    - 工具调用: {len(response.metadata.get('agent_tool_calls', []))}次")
    print(f"    - 回复: {response.message[:150]}...")
    
    if response.operations:
        print(f"    - 操作: {len(response.operations)}个")
        for op in response.operations[:2]:
            print(f"      * {op.operation_type.value}")
    
except Exception as e:
    print(f"  ✗ Agent模式测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
