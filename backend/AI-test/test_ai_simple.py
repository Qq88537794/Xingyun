"""
简化的AI模块测试
只测试核心功能，避免复杂导入
"""

import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("AI模块简化测试")
print("=" * 60)

# 1. 测试LLM基础导入
print("\n[1] 测试LLM基础模块...")
try:
    from ai.llm.base import BaseLLM, ModelProvider
    from ai.llm.zhipu import ZhipuLLM
    print("  ✓ LLM基础模块导入成功")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 2. 测试LLM工厂初始化
print("\n[2] 测试LLM工厂...")
try:
    from ai.llm.factory import init_llm_factory, ModelProvider as MP
    
    zhipu_key = os.getenv('ZHIPU_API_KEY')
    if not zhipu_key:
        print("  ✗ 未配置ZHIPU_API_KEY")
        sys.exit(1)
    
    configs = [{
        'provider': 'zhipu',
        'api_key': zhipu_key,
        'model_name': 'glm-4-flash'
    }]
    
    factory = init_llm_factory(configs)
    llm = factory.get_llm()
    print(f"  ✓ LLM工厂初始化成功: {llm.__class__.__name__}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 3. 测试简单对话
print("\n[3] 测试LLM对话...")
try:
    response = llm.simple_chat("你好，请用一句话介绍自己")
    print(f"  ✓ 对话成功")
    print(f"    回复: {response[:80]}...")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 4. 测试Agent工具
print("\n[4] 测试Agent工具模块...")
try:
    from ai.agent.tools import create_default_registry
    
    def get_doc(doc_id):
        return "测试文档内容"
    
    def write_doc(doc_id, content):
        return True
    
    registry = create_default_registry(get_doc, write_doc)
    tools = registry.to_llm_tools()
    
    print(f"  ✓ 工具注册成功: {len(tools)}个工具")
    for i, tool in enumerate(tools[:3], 1):
        func = tool.get('function', {})
        print(f"    {i}. {func.get('name')}")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 测试工具调用
print("\n[5] 测试LLM工具调用...")
try:
    response = llm.chat_with_tools(
        system_prompt="你是一个文档助手",
        messages=[{"role": "user", "content": "请读取文档"}],
        tools=tools
    )
    
    print(f"  ✓ 工具调用测试成功")
    print(f"    - Finish Reason: {response.get('finish_reason')}")
    print(f"    - Tool Calls: {len(response.get('tool_calls', []))}个")
    if response.get('content'):
        print(f"    - 回复: {response['content'][:60]}...")
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

# 6. 测试Agent Processor
print("\n[6] 测试Agent处理器...")
try:
    from ai.agent.processor import AgentProcessor
    
    def llm_caller(system_prompt, messages, tools):
        return llm.chat_with_tools(system_prompt, messages, tools)
    
    processor = AgentProcessor(
        tool_registry=registry,
        llm_caller=llm_caller,
        system_prompt="你是一个智能文档助手",
        max_iterations=5
    )
    
    result = processor.process(
        user_input="请读取文档并告诉我内容",
        session_id="test_session"
    )
    
    print(f"  ✓ Agent测试成功")
    print(f"    - 迭代次数: {result.iterations}")
    print(f"    - 工具调用: {len(result.tool_calls)}次")
    print(f"    - 回复: {result.message[:80]}...")
    
except Exception as e:
    print(f"  ✗ 失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
