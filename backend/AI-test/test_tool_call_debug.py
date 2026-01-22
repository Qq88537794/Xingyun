"""
调试智谱工具调用
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

print("调试智谱工具调用")
print("=" * 60)

from ai.llm.zhipu import ZhipuLLM

zhipu_key = os.getenv('ZHIPU_API_KEY')
llm = ZhipuLLM(api_key=zhipu_key, model_name='glm-4-flash')

# 简化的工具定义
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "获取天气信息",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "城市名称"
                }
            },
            "required": ["city"]
        }
    }
}]

print("\n工具定义:")
print(json.dumps(tools, indent=2, ensure_ascii=False))

print("\n发送请求...")
try:
    response = llm.chat_with_tools(
        system_prompt="你是一个助手",
        messages=[{"role": "user", "content": "北京今天天气怎么样？"}],
        tools=tools
    )
    
    print("✓ 成功!")
    print(f"  - Finish Reason: {response.get('finish_reason')}")
    print(f"  - Tool Calls: {len(response.get('tool_calls', []))}")
    print(f"  - Content: {response.get('content', '')[:100]}")
    
    if response.get('tool_calls'):
        for tc in response['tool_calls']:
            print(f"\n  工具调用:")
            print(f"    - ID: {tc.get('id')}")
            print(f"    - Name: {tc.get('function', {}).get('name')}")
            print(f"    - Args: {tc.get('function', {}).get('arguments')}")
    
except Exception as e:
    print(f"✗ 失败: {e}")
    import traceback
    traceback.print_exc()
