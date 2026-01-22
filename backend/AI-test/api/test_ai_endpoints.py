"""
AI模块接口测试脚本
测试三个核心AI接口的功能
使用管理员Token进行快速测试
"""

import requests
import json
import os
import time
from datetime import datetime
from io import BytesIO

# 配置
BASE_URL = "http://127.0.0.1:5000"  # 使用默认5000端口
API_URL = f"{BASE_URL}/api"

# 管理员Token（从.env配置）
ADMIN_TOKEN = "dev-admin-token-2026-xingyun"

# 测试结果记录
test_results = []

# 详细日志开关
VERBOSE = True  # 显示详细的请求和响应


def get_headers():
    """获取包含管理员Token的请求头"""
    return {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Content-Type": "application/json"
    }


def print_section(title):
    """打印章节标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_request(method, url, headers=None, data=None, files=None):
    """打印请求详情"""
    if not VERBOSE:
        return
    
    print(f"📤 请求:")
    print(f"   {method} {url}")
    if headers:
        print(f"   Headers: {json.dumps(dict(headers), indent=2, ensure_ascii=False)}")
    if data:
        print(f"   Body: {json.dumps(data, indent=2, ensure_ascii=False)}")
    if files:
        print(f"   Files: {list(files.keys())}")
    print()


def print_response(resp):
    """打印响应详情"""
    if not VERBOSE:
        return
    
    print(f"📥 响应:")
    print(f"   Status: {resp.status_code}")
    print(f"   Headers: {dict(resp.headers)}")
    try:
        print(f"   Body: {json.dumps(resp.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"   Body: {resp.text[:500]}")
    print()


def log_result(test_name, success, message, details=None):
    """记录测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    result = {
        "test": test_name,
        "success": success,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    print(f"{status} | {test_name}")
    print(f"   消息: {message}")
    if details:
        print(f"   详情: {json.dumps(details, ensure_ascii=False, indent=2)}")
    print()


def test_create_project():
    """创建测试项目（使用管理员权限）"""
    print_section("1. 创建测试项目")
    
    headers = get_headers()
    project_data = {
        "name": f"AI测试项目_{datetime.now().strftime('%H%M%S')}",
        "description": "用于测试AI接口的项目"
    }
    
    try:
        url = f"{API_URL}/projects"
        print_request("POST", url, headers=headers, data=project_data)
        
        resp = requests.post(
            url,
            json=project_data,
            headers=headers,
            timeout=10
        )
        
        print_response(resp)
        
        if resp.status_code == 201:
            project = resp.json()["project"]
            project_id = project["id"]
            log_result(
                "创建项目",
                True,
                f"项目创建成功: {project['name']}",
                {"project_id": project_id}
            )
            return project_id
        else:
            log_result(
                "创建项目",
                False,
                f"创建失败: {resp.status_code}",
                resp.json()
            )
            return None
            
    except Exception as e:
        log_result("创建项目", False, f"异常: {str(e)}")
        return None


def test_upload_resources(project_id):
    """测试资源上传接口"""
    print_section("2. 资源上传测试")
    
    # 创建测试文档
    test_files = [
        {
            "filename": "AI技术介绍.txt",
            "content": """人工智能（Artificial Intelligence, AI）技术发展报告

一、人工智能概述
人工智能是计算机科学的一个重要分支，它致力于研究和开发能够模拟、延伸和扩展人的智能的理论、方法、技术及应用系统。

二、核心技术
1. 机器学习（Machine Learning）
机器学习是AI的核心技术之一，通过算法让计算机从数据中学习规律和模式。主要包括监督学习、无监督学习和强化学习。

2. 深度学习（Deep Learning）
深度学习是机器学习的一个分支，利用多层神经网络模拟人脑的学习过程。在图像识别、语音识别、自然语言处理等领域取得了突破性进展。

3. 自然语言处理（NLP）
自然语言处理研究如何让计算机理解和生成人类语言，包括文本分类、情感分析、机器翻译、对话系统等应用。

三、应用领域
- 医疗诊断：AI辅助医生进行疾病诊断和治疗方案制定
- 金融科技：智能风控、量化交易、客户服务
- 智能制造：工业机器人、预测性维护、质量检测
- 自动驾驶：环境感知、路径规划、决策控制
- 智能客服：智能问答、情感分析、个性化推荐

四、未来展望
随着算力的提升和算法的优化，人工智能将在更多领域发挥重要作用。同时，AI伦理、数据安全等问题也需要得到重视和解决。"""
        },
        {
            "filename": "机器学习实践.md",
            "content": """# 机器学习实践指南

## 1. 数据准备
- 数据收集：从各种来源获取高质量数据
- 数据清洗：处理缺失值、异常值和重复数据
- 特征工程：选择和构建有效的特征

## 2. 模型选择
### 监督学习模型
- 线性回归：用于预测连续值
- 逻辑回归：用于二分类问题
- 决策树：易于理解和解释
- 随机森林：集成多个决策树
- 支持向量机：适合小样本问题
- 神经网络：处理复杂非线性问题

### 无监督学习模型
- K-means聚类：将数据分组
- PCA降维：减少特征维度
- 异常检测：识别异常数据点

## 3. 模型训练
- 选择合适的损失函数
- 设置学习率和优化器
- 使用交叉验证评估模型
- 调整超参数优化性能

## 4. 模型评估
- 分类指标：准确率、精确率、召回率、F1分数
- 回归指标：MAE、MSE、RMSE、R²
- 混淆矩阵分析
- ROC曲线和AUC

## 5. 模型部署
- 模型保存和加载
- API接口设计
- 性能监控
- 持续优化"""
        }
    ]
    
    uploaded_resources = []
    
    for file_info in test_files:
        try:
            filename = file_info["filename"]
            content = file_info["content"]
            
            print(f"正在上传: {filename}")
            print(f"文件大小: {len(content)} 字节\n")
            
            # 准备文件数据
            files = {
                'file': (filename, BytesIO(content.encode('utf-8')), 'text/plain')
            }
            
            # 注意：上传文件时不要设置Content-Type为application/json
            headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
            
            url = f"{API_URL}/projects/{project_id}/resources"
            print_request("POST", url, headers=headers, files=files)
            
            resp = requests.post(
                url,
                files=files,
                headers=headers,
                timeout=30
            )
            
            print_response(resp)
            
            if resp.status_code == 201:
                resource = resp.json()["resource"]
                resource_id = resource["id"]
                uploaded_resources.append({
                    "id": resource_id,
                    "filename": filename
                })
                
                log_result(
                    f"上传资源 - {filename}",
                    True,
                    f"资源上传成功",
                    {
                        "resource_id": resource_id,
                        "filename": filename,
                        "size": len(content)
                    }
                )
            else:
                log_result(
                    f"上传资源 - {filename}",
                    False,
                    f"上传失败: {resp.status_code}",
                    resp.json()
                )
                
        except Exception as e:
            log_result(f"上传资源 - {filename}", False, f"异常: {str(e)}")
    
    return uploaded_resources


def test_ai_chat_simple(project_id):
    """测试AI聊天接口 - Simple模式"""
    print_section("3. AI聊天接口测试 - Simple模式")
    
    headers = get_headers()
    
    # 测试用例
    test_cases = [
        {
            "name": "普通问答",
            "payload": {
                "message": "什么是人工智能？",
                "project_id": project_id,
                "mode": "simple"
            }
        },
        {
            "name": "带文档上下文",
            "payload": {
                "message": "总结一下这段内容的要点",
                "project_id": project_id,
                "mode": "simple",
                "document_content": "人工智能（AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。AI包括机器学习、深度学习、自然语言处理等多个子领域。"
            }
        }
    ]
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            print(f"请求: {case['payload']['message']}")
            
            url = f"{API_URL}/ai/chat"
            print_request("POST", url, headers=headers, data=case["payload"])
            
            resp = requests.post(
                url,
                json=case["payload"],
                headers=headers,
                timeout=30
            )
            
            print_response(resp)
            
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                reply = data.get("message", "")
                
                print(f"回复: {reply[:100]}..." if len(reply) > 100 else f"回复: {reply}")
                
                log_result(
                    f"Simple模式 - {case['name']}",
                    True,
                    "AI响应成功",
                    {
                        "reply_length": len(reply),
                        "tokens_used": data.get("tokens_used"),
                        "sources": len(data.get("sources", []))
                    }
                )
            else:
                log_result(
                    f"Simple模式 - {case['name']}",
                    False,
                    f"请求失败: {resp.status_code}",
                    resp.json()
                )
                
        except Exception as e:
            log_result(f"Simple模式 - {case['name']}", False, f"异常: {str(e)}")


def test_ai_chat_agent(project_id):
    """测试AI聊天接口 - Agent模式"""
    print_section("4. AI聊天接口测试 - Agent模式")
    
    headers = get_headers()
    
    # 测试用例
    test_cases = [
        {
            "name": "生成大纲",
            "payload": {
                "message": "请为'AI应用开发'这个主题生成一个详细的文档大纲",
                "project_id": project_id,
                "mode": "agent"
            }
        },
        {
            "name": "扩写内容",
            "payload": {
                "message": "请扩写这段内容，增加更多细节和例子",
                "project_id": project_id,
                "mode": "agent",
                "document_content": "# AI应用开发\n\n人工智能正在改变世界。",
                "selected_text": "人工智能正在改变世界。"
            }
        },
        {
            "name": "生成摘要",
            "payload": {
                "message": "请总结这篇文档的主要内容",
                "project_id": project_id,
                "mode": "agent",
                "document_content": """
# 人工智能技术发展报告

## 1. 引言
人工智能（Artificial Intelligence, AI）是当今科技领域最热门的话题之一。从自动驾驶到智能助手，AI技术正在深刻改变我们的生活方式。

## 2. 主要技术
### 2.1 机器学习
机器学习是AI的核心技术，通过算法让计算机从数据中学习规律。

### 2.2 深度学习
深度学习利用神经网络模拟人脑处理信息，在图像识别、语音识别等领域取得突破。

## 3. 应用场景
AI在医疗诊断、金融风控、智能制造等多个领域展现出巨大潜力。

## 4. 未来展望
随着算力提升和算法优化，AI将在更多领域发挥作用。
                """
            }
        }
    ]
    
    for case in test_cases:
        try:
            print(f"\n测试: {case['name']}")
            print(f"请求: {case['payload']['message']}")
            
            url = f"{API_URL}/ai/chat"
            print_request("POST", url, headers=headers, data=case["payload"])
            
            resp = requests.post(
                url,
                json=case["payload"],
                headers=headers,
                timeout=45
            )
            
            print_response(resp)
            
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                reply = data.get("message", "")
                operations = data.get("operations", [])
                
                print(f"回复: {reply[:100]}..." if len(reply) > 100 else f"回复: {reply}")
                
                if operations:
                    print(f"操作: {operations[0].get('operation_type', 'unknown')}")
                
                log_result(
                    f"Agent模式 - {case['name']}",
                    True,
                    "AI响应成功",
                    {
                        "reply_length": len(reply),
                        "operations_count": len(operations),
                        "operation_type": operations[0].get("operation_type") if operations else None,
                        "tokens_used": data.get("tokens_used")
                    }
                )
            else:
                log_result(
                    f"Agent模式 - {case['name']}",
                    False,
                    f"请求失败: {resp.status_code}",
                    resp.json()
                )
                
        except Exception as e:
            log_result(f"Agent模式 - {case['name']}", False, f"异常: {str(e)}")


def test_knowledge_base_info(project_id):
    """测试知识库信息接口"""
    print_section("4. 知识库信息接口测试")
    
    headers = get_headers()
    
    try:
        url = f"{API_URL}/ai/knowledge-base/{project_id}/info"
        print_request("GET", url, headers=headers)
        
        resp = requests.get(
            url,
            headers=headers,
            timeout=10
        )
        
        print_response(resp)
        
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            log_result(
                "获取知识库信息",
                True,
                "知识库信息获取成功",
                {
                    "collection_name": data.get("collection_name"),
                    "vector_count": data.get("vector_count"),
                    "indexed_resources": data.get("indexed_resources", [])
                }
            )
        else:
            log_result(
                "获取知识库信息",
                False,
                f"请求失败: {resp.status_code}",
                resp.json()
            )
            
    except Exception as e:
        log_result("获取知识库信息", False, f"异常: {str(e)}")


def test_knowledge_base_search(project_id):
    """测试知识库搜索接口"""
    print_section("6. 知识库搜索接口测试")
    
    headers = get_headers()
    
    test_queries = [
        "人工智能",
        "机器学习的应用",
        "深度学习技术"
    ]
    
    for query in test_queries:
        try:
            print(f"\n搜索: {query}")
            
            url = f"{API_URL}/ai/knowledge-base/{project_id}/search"
            payload = {"query": query, "top_k": 3}
            print_request("POST", url, headers=headers, data=payload)
            
            resp = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=15
            )
            
            print_response(resp)
            
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                results = data.get("results", [])
                
                print(f"找到 {len(results)} 个结果")
                
                log_result(
                    f"知识库搜索 - '{query}'",
                    True,
                    f"搜索成功，找到{len(results)}个结果",
                    {
                        "results_count": len(results),
                        "top_score": results[0].get("score") if results else None
                    }
                )
            else:
                log_result(
                    f"知识库搜索 - '{query}'",
                    False,
                    f"请求失败: {resp.status_code}",
                    resp.json()
                )
                
        except Exception as e:
            log_result(f"知识库搜索 - '{query}'", False, f"异常: {str(e)}")


def generate_report():
    """生成测试报告"""
    print_section("测试报告总结")
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["success"])
    failed = total - passed
    
    print(f"总测试数: {total}")
    print(f"通过: {passed} ✅")
    print(f"失败: {failed} ❌")
    print(f"通过率: {(passed/total*100):.1f}%\n")
    
    if failed > 0:
        print("失败的测试:")
        for result in test_results:
            if not result["success"]:
                print(f"  - {result['test']}: {result['message']}")
    
    # 保存详细报告
    report_file = f"AI_ENDPOINTS_TEST_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": f"{(passed/total*100):.1f}%"
            },
            "results": test_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n详细报告已保存到: {report_file}")


def main():
    """主测试流程"""
    print("\n" + "=" * 80)
    print("  AI模块接口测试 (使用管理员Token)")
    print("  测试时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 80)
    
    print(f"\n✓ 使用管理员Token: {ADMIN_TOKEN}")
    print(f"✓ 后端地址: {BASE_URL}\n")
    
    # 1. 创建项目
    project_id = test_create_project()
    if not project_id:
        print("\n❌ 项目创建失败，无法继续测试")
        return
    
    # 2. 上传资源
    uploaded_resources = test_upload_resources(project_id)
    if not uploaded_resources:
        print("\n⚠️ 资源上传失败，知识库可能为空")
    else:
        print(f"\n✅ 成功上传 {len(uploaded_resources)} 个资源")
        # 等待资源索引完成 (实际项目中应该监控索引状态)
        print("⏳ 等待5秒让资源索引完成...")
        time.sleep(5)
    
    # 3. 测试AI聊天 - Simple模式
    test_ai_chat_simple(project_id)
    
    # 4. 测试AI聊天 - Agent模式
    test_ai_chat_agent(project_id)
    
    # 5. 测试知识库信息
    test_knowledge_base_info(project_id)
    
    # 6. 测试知识库搜索
    test_knowledge_base_search(project_id)
    
    # 7. 生成报告
    generate_report()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生异常: {str(e)}")
        import traceback
        traceback.print_exc()
