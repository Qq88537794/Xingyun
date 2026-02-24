"""
调试大纲生成响应
查看后端返回的实际数据结构
"""
import requests
import json

BASE_URL = "http://localhost:5000"
TOKEN = None

def login():
    """登录"""
    global TOKEN
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        data = response.json()
        if 'data' in data and 'token' in data['data']:
            TOKEN = data['data']['token']
        elif 'access_token' in data:
            TOKEN = data['access_token']
        elif 'token' in data:
            TOKEN = data['token']
        else:
            print(f"❌ 登录响应格式错误: {data}")
            return False
        print("✅ 登录成功\n")
        return True
    else:
        print(f"❌ 登录失败: {response.status_code}")
        print(response.text)
        return False

def test_outline():
    """测试大纲生成"""
    print("=" * 80)
    print("测试: 生成大纲")
    print("=" * 80)
    
    response = requests.post(
        f"{BASE_URL}/api/ai/chat",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "message": "生成大纲",
            "project_id": 1,
            "document_id": "test_doc",
            "document_content": "人工智能是计算机科学的一个分支。它研究如何让计算机模拟人类的智能行为。",
            "enable_agent": True,
            "enable_rag": False
        }
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        
        print("\n【message 字段】")
        print("-" * 80)
        message = data.get('message', '')
        print(f"长度: {len(message)}")
        print(f"内容:\n{message}\n")
        
        print("\n【operations 字段】")
        print("-" * 80)
        operations = data.get('operations', [])
        print(f"数量: {len(operations)}")
        
        for i, op in enumerate(operations):
            print(f"\n操作 {i+1}:")
            print(f"  operation_type: {op.get('operation_type')}")
            content = op.get('content', '')
            print(f"  content长度: {len(content)}")
            print(f"  content:\n{content}\n")
        
        print("\n【重复检查】")
        print("-" * 80)
        
        if operations and operations[0].get('content'):
            op_content = operations[0]['content']
            
            # 检查message是否包含op_content
            if len(op_content) > 50:
                op_start = op_content[:50]
                if op_start in message:
                    print("⚠️ 警告: message 包含了 operation.content 的内容")
                    print(f"   重复部分: {op_start}...")
                else:
                    print("✅ message 和 operation.content 是分开的")
            
            # 检查op_content内部是否有重复行
            lines = op_content.split('\n')
            seen = {}
            duplicates = []
            
            for line_num, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped and (stripped[0].isdigit() or stripped.startswith('#')):
                    if stripped in seen:
                        duplicates.append((line_num, stripped, seen[stripped]))
                    else:
                        seen[stripped] = line_num
            
            if duplicates:
                print(f"\n⚠️ 警告: 发现 {len(duplicates)} 行重复:")
                for line_num, content, first_line in duplicates[:5]:
                    print(f"   行{line_num} 重复了行{first_line}: {content[:60]}...")
            else:
                print("\n✅ operation.content 内部没有重复行")
        
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)

def test_normal_chat():
    """测试普通对话（不应该生成大纲）"""
    print("\n" + "=" * 80)
    print("测试: 普通对话（不应该生成大纲）")
    print("=" * 80)
    
    response = requests.post(
        f"{BASE_URL}/api/ai/chat",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "message": "请解释一下什么是人工智能",
            "project_id": 1,
            "document_id": "test_doc",
            "document_content": "人工智能是计算机科学的一个分支。",
            "enable_agent": False,
            "enable_rag": False
        }
    )
    
    if response.status_code == 200:
        data = response.json()['data']
        
        message = data.get('message', '')
        operations = data.get('operations', [])
        
        print(f"\nmessage长度: {len(message)}")
        print(f"message前200字符:\n{message[:200]}...\n")
        
        print(f"operations数量: {len(operations)}")
        if operations:
            for op in operations:
                print(f"  - operation_type: {op.get('operation_type')}")
        
        # 检查是否错误地识别为生成大纲
        if operations and operations[0].get('operation_type') == 'generate_outline':
            print("\n❌ 错误: 普通对话被识别为生成大纲！")
        else:
            print("\n✅ 正确: 没有被识别为生成大纲")
    else:
        print(f"❌ 请求失败: {response.status_code}")

if __name__ == '__main__':
    if login():
        test_outline()
        test_normal_chat()
