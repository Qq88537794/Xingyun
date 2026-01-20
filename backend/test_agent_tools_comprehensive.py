"""
Agent工具全面测试
测试所有7个工具的功能，包括边界情况和错误处理
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai.agent.tools import (
    ReadDocumentTool,
    WriteDocumentTool,
    EditDocumentTool,
    SearchDocumentTool,
    GenerateOutlineTool,
    ExpandContentTool,
    SummarizeTool,
    create_default_registry,
    ToolRegistry
)


class TestDocumentStorage:
    """测试用的文档存储"""
    
    def __init__(self):
        self.documents = {
            "doc1": "这是一个测试文档。\n第二段内容。\n第三段结束。",
            "doc2": "# 标题\n\n## 章节1\n内容1\n\n## 章节2\n内容2",
        }
    
    def get_document(self, doc_id: str):
        """获取文档"""
        return self.documents.get(doc_id)
    
    def write_document(self, doc_id: str, content: str):
        """写入文档"""
        self.documents[doc_id] = content
        return True


def print_test_header(test_name: str):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")


def print_result(success: bool, result: dict, description: str = ""):
    """打印测试结果"""
    status = "✓ 成功" if success else "✗ 失败"
    print(f"\n{status}: {description}")
    print(f"结果: {result}")


def test_read_document():
    """测试1: 读取文档工具"""
    print_test_header("1. 读取文档工具 (ReadDocumentTool)")
    
    storage = TestDocumentStorage()
    tool = ReadDocumentTool(storage.get_document)
    
    # 测试1.1: 读取存在的文档
    print("\n[1.1] 读取存在的文档")
    result = tool.execute(document_id="doc1")
    print_result(result["success"], result, "读取doc1")
    assert result["success"] == True
    assert "测试文档" in result["content"]
    
    # 测试1.2: 读取不存在的文档
    print("\n[1.2] 读取不存在的文档")
    result = tool.execute(document_id="doc999")
    print_result(result["success"], result, "读取不存在的文档")
    assert result["success"] == False
    assert "不存在" in result["error"]
    
    # 测试1.3: 验证工具定义
    print("\n[1.3] 验证工具定义")
    definition = tool.get_definition()
    print(f"工具名称: {definition.name}")
    print(f"工具描述: {definition.description[:50]}...")
    print(f"参数要求: {definition.parameters['required']}")
    assert definition.name == "read_document"
    assert "document_id" in definition.parameters["required"]


def test_write_document():
    """测试2: 写入文档工具"""
    print_test_header("2. 写入文档工具 (WriteDocumentTool)")
    
    storage = TestDocumentStorage()
    tool = WriteDocumentTool(storage.write_document)
    
    # 测试2.1: 创建新文档
    print("\n[2.1] 创建新文档")
    new_content = "这是一个新创建的文档。\n包含多行内容。"
    result = tool.execute(document_id="doc3", content=new_content)
    print_result(result["success"], result, "创建doc3")
    assert result["success"] == True
    assert storage.documents["doc3"] == new_content
    
    # 测试2.2: 覆盖已有文档
    print("\n[2.2] 覆盖已有文档")
    old_content = storage.documents["doc1"]
    print(f"原内容: {old_content[:30]}...")
    new_content = "完全替换的新内容"
    result = tool.execute(document_id="doc1", content=new_content)
    print_result(result["success"], result, "覆盖doc1")
    assert result["success"] == True
    assert storage.documents["doc1"] == new_content
    assert storage.documents["doc1"] != old_content
    
    # 测试2.3: 空内容
    print("\n[2.3] 写入空内容")
    result = tool.execute(document_id="doc_empty", content="")
    print_result(result["success"], result, "写入空文档")
    assert result["success"] == True


def test_edit_document():
    """测试3: 编辑文档工具"""
    print_test_header("3. 编辑文档工具 (EditDocumentTool)")
    
    storage = TestDocumentStorage()
    tool = EditDocumentTool(storage.get_document, storage.write_document)
    
    # 测试3.1: 插入内容
    print("\n[3.1] 插入内容")
    original = storage.documents["doc1"]
    print(f"原文档: {original}")
    result = tool.execute(
        document_id="doc1",
        action="insert",
        position=6,  # "这是一个"后面
        content="【插入的内容】"
    )
    print_result(result["success"], result, "在位置6插入内容")
    print(f"新文档: {storage.documents['doc1']}")
    assert result["success"] == True
    assert "【插入的内容】" in storage.documents["doc1"]
    
    # 测试3.2: 替换内容
    print("\n[3.2] 替换内容")
    storage.documents["doc1"] = "ABCDEFGHIJK"
    print(f"原文档: {storage.documents['doc1']}")
    result = tool.execute(
        document_id="doc1",
        action="replace",
        position=3,
        end_position=7,
        content="XXX"
    )
    print_result(result["success"], result, "替换位置3-7")
    print(f"新文档: {storage.documents['doc1']}")
    # 位置3-7是DEFG(4个字符)，替换为XXX，结果应该是ABC + XXX + HIJK
    assert storage.documents["doc1"] == "ABCXXXHIJK"
    
    # 测试3.3: 删除内容
    print("\n[3.3] 删除内容")
    storage.documents["doc1"] = "123456789"
    print(f"原文档: {storage.documents['doc1']}")
    result = tool.execute(
        document_id="doc1",
        action="delete",
        position=2,
        end_position=5
    )
    print_result(result["success"], result, "删除位置2-5")
    print(f"新文档: {storage.documents['doc1']}")
    assert storage.documents["doc1"] == "126789"
    
    # 测试3.4: 编辑不存在的文档
    print("\n[3.4] 编辑不存在的文档")
    result = tool.execute(
        document_id="doc_not_exist",
        action="insert",
        position=0,
        content="test"
    )
    print_result(result["success"], result, "编辑不存在的文档")
    assert result["success"] == False
    
    # 测试3.5: 边界情况 - 在开头插入
    print("\n[3.5] 在文档开头插入")
    storage.documents["doc1"] = "原始内容"
    result = tool.execute(
        document_id="doc1",
        action="insert",
        position=0,
        content="【前缀】"
    )
    print_result(result["success"], result, "在开头插入")
    print(f"新文档: {storage.documents['doc1']}")
    assert storage.documents["doc1"].startswith("【前缀】")
    
    # 测试3.6: 边界情况 - 在末尾插入
    print("\n[3.6] 在文档末尾插入")
    storage.documents["doc1"] = "原始内容"
    length = len(storage.documents["doc1"])
    result = tool.execute(
        document_id="doc1",
        action="insert",
        position=length,
        content="【后缀】"
    )
    print_result(result["success"], result, "在末尾插入")
    print(f"新文档: {storage.documents['doc1']}")
    assert storage.documents["doc1"].endswith("【后缀】")


def test_search_document():
    """测试4: 搜索文档工具"""
    print_test_header("4. 搜索文档工具 (SearchDocumentTool)")
    
    storage = TestDocumentStorage()
    storage.documents["search_test"] = """
第一段包含关键词。
第二段也包含关键词内容。
第三段没有。
第四段又出现了关键词。
第五段关键词再次出现。
第六段也有关键词。
    """.strip()
    
    tool = SearchDocumentTool(storage.get_document)
    
    # 测试4.1: 搜索多个匹配
    print("\n[4.1] 搜索多个匹配")
    result = tool.execute(
        document_id="search_test",
        query="关键词",
        max_results=3
    )
    print_result(result["success"], result, "搜索'关键词'，最多3个结果")
    assert result["success"] == True
    assert result["matches"] == 3
    print(f"找到 {result['matches']} 个匹配")
    for i, match in enumerate(result["results"], 1):
        print(f"  匹配{i}: 位置={match['position']}, 上下文=...{match['context'][:30]}...")
    
    # 测试4.2: 搜索不存在的内容
    print("\n[4.2] 搜索不存在的内容")
    result = tool.execute(
        document_id="search_test",
        query="不存在的词",
        max_results=5
    )
    print_result(result["success"], result, "搜索不存在的内容")
    assert result["success"] == True
    assert result["matches"] == 0
    
    # 测试4.3: 搜索单个字符
    print("\n[4.3] 搜索单个字符")
    result = tool.execute(
        document_id="search_test",
        query="段",
        max_results=10
    )
    print_result(result["success"], result, "搜索'段'字")
    assert result["success"] == True
    print(f"找到 {result['matches']} 个匹配")


def test_generate_outline():
    """测试5: 生成大纲工具"""
    print_test_header("5. 生成大纲工具 (GenerateOutlineTool)")
    
    tool = GenerateOutlineTool()
    
    # 测试5.1: 基础大纲生成
    print("\n[5.1] 基础大纲生成")
    result = tool.execute(
        topic="Python编程入门",
        requirements="面向初学者，包含基础语法和实践项目",
        depth=3
    )
    print_result(result["success"], result, "生成Python入门大纲")
    assert result["success"] == True
    assert result["type"] == "outline_request"
    assert result["topic"] == "Python编程入门"
    assert result["depth"] == 3
    
    # 测试5.2: 只有主题
    print("\n[5.2] 只提供主题")
    result = tool.execute(topic="人工智能发展史")
    print_result(result["success"], result, "生成AI历史大纲")
    assert result["success"] == True
    
    # 测试5.3: 验证参数默认值
    print("\n[5.3] 验证默认参数")
    definition = tool.get_definition()
    print(f"默认深度: {definition.parameters['properties']['depth']['default']}")
    assert definition.parameters["properties"]["depth"]["default"] == 3


def test_expand_content():
    """测试6: 扩写内容工具"""
    print_test_header("6. 扩写内容工具 (ExpandContentTool)")
    
    tool = ExpandContentTool()
    
    # 测试6.1: 基础扩写
    print("\n[6.1] 基础扩写")
    result = tool.execute(
        content="Python是一门编程语言。",
        ratio=3,
        focus="历史和应用领域"
    )
    print_result(result["success"], result, "扩写Python介绍")
    assert result["success"] == True
    assert result["type"] == "expand_request"
    assert result["ratio"] == 3
    assert result["focus"] == "历史和应用领域"
    
    # 测试6.2: 最小参数
    print("\n[6.2] 最小参数扩写")
    result = tool.execute(content="简短内容")
    print_result(result["success"], result, "使用默认参数扩写")
    assert result["success"] == True
    assert result["ratio"] == 2  # 默认值
    
    # 测试6.3: 不同扩写倍数
    print("\n[6.3] 不同扩写倍数")
    for ratio in [1.5, 2, 3, 5]:
        result = tool.execute(content="测试内容", ratio=ratio)
        print(f"  倍数={ratio}: {result['ratio']}")
        assert result["ratio"] == ratio


def test_summarize():
    """测试7: 摘要工具"""
    print_test_header("7. 摘要生成工具 (SummarizeTool)")
    
    tool = SummarizeTool()
    
    # 测试7.1: 基础摘要
    print("\n[7.1] 基础摘要")
    long_text = """
人工智能（AI）是计算机科学的一个分支，致力于创建能够模拟人类智能的系统。
AI的历史可以追溯到20世纪50年代，当时科学家们开始探索机器是否能够思考。
近年来，随着深度学习和神经网络的发展，AI取得了突破性进展。
现在AI被广泛应用于图像识别、自然语言处理、自动驾驶等领域。
    """.strip()
    
    result = tool.execute(
        content=long_text,
        max_length=50,
        focus_points=["历史", "应用"]
    )
    print_result(result["success"], result, "生成AI简介摘要")
    assert result["success"] == True
    assert result["type"] == "summarize_request"
    assert result["max_length"] == 50
    assert len(result["focus_points"]) == 2
    
    # 测试7.2: 不指定重点
    print("\n[7.2] 不指定重点")
    result = tool.execute(content="一些内容")
    print_result(result["success"], result, "无重点摘要")
    assert result["success"] == True
    assert result["focus_points"] == []
    
    # 测试7.3: 默认长度
    print("\n[7.3] 使用默认长度")
    result = tool.execute(content="测试内容")
    print(f"  默认最大长度: {result['max_length']}")
    assert result["max_length"] == 200


def test_tool_registry():
    """测试8: 工具注册表"""
    print_test_header("8. 工具注册表 (ToolRegistry)")
    
    storage = TestDocumentStorage()
    
    # 测试8.1: 创建默认注册表
    print("\n[8.1] 创建默认注册表")
    registry = create_default_registry(
        storage.get_document,
        storage.write_document
    )
    tools = registry.list_tools()
    print(f"注册的工具: {tools}")
    assert len(tools) == 7
    
    expected_tools = [
        "read_document", "write_document", "edit_document",
        "search_document", "generate_outline", "expand_content", "summarize"
    ]
    for tool_name in expected_tools:
        assert tool_name in tools, f"缺少工具: {tool_name}"
    
    # 测试8.2: 获取工具定义
    print("\n[8.2] 获取工具定义")
    definitions = registry.get_definitions()
    print(f"工具定义数量: {len(definitions)}")
    for defn in definitions:
        print(f"  - {defn.name}: {defn.description[:40]}...")
    assert len(definitions) == 7
    
    # 测试8.3: 转换为LLM格式
    print("\n[8.3] 转换为LLM工具格式")
    llm_tools = registry.to_llm_tools()
    print(f"LLM工具格式数量: {len(llm_tools)}")
    first_tool = llm_tools[0]
    print(f"第一个工具结构: {first_tool.keys()}")
    print(f"  type: {first_tool['type']}")
    print(f"  function.name: {first_tool['function']['name']}")
    print(f"  function.description: {first_tool['function']['description'][:50]}...")
    assert first_tool["type"] == "function"
    assert "name" in first_tool["function"]
    assert "description" in first_tool["function"]
    assert "parameters" in first_tool["function"]
    
    # 测试8.4: 执行工具
    print("\n[8.4] 通过注册表执行工具")
    result = registry.execute("read_document", {"document_id": "doc1"})
    print(f"执行结果: {result}")
    assert result["success"] == True
    
    # 测试8.5: 执行不存在的工具
    print("\n[8.5] 执行不存在的工具")
    try:
        registry.execute("not_exist", {})
        assert False, "应该抛出异常"
    except ValueError as e:
        print(f"✓ 正确抛出异常: {e}")
    
    # 测试8.6: 构建提示词
    print("\n[8.6] 构建工具提示词")
    prompt = registry.build_tools_prompt()
    print(f"提示词长度: {len(prompt)} 字符")
    print(f"提示词预览:\n{prompt[:200]}...")
    assert "可用工具" in prompt
    assert len(prompt) > 100


def test_tool_definitions_format():
    """测试9: 工具定义格式规范"""
    print_test_header("9. 工具定义格式规范")
    
    storage = TestDocumentStorage()
    registry = create_default_registry(
        storage.get_document,
        storage.write_document
    )
    
    print("\n[9.1] 验证每个工具的LLM格式")
    llm_tools = registry.to_llm_tools()
    
    for i, tool in enumerate(llm_tools, 1):
        print(f"\n工具 {i}: {tool['function']['name']}")
        
        # 验证基本结构
        assert tool["type"] == "function"
        assert "function" in tool
        
        func = tool["function"]
        assert "name" in func
        assert "description" in func
        assert "parameters" in func
        
        params = func["parameters"]
        assert params["type"] == "object"
        assert "properties" in params
        
        print(f"  ✓ 名称: {func['name']}")
        print(f"  ✓ 描述: {func['description'][:50]}...")
        print(f"  ✓ 参数数量: {len(params['properties'])}")
        if "required" in params:
            print(f"  ✓ 必需参数: {params['required']}")


def test_integration_scenario():
    """测试10: 综合场景测试"""
    print_test_header("10. 综合场景测试")
    
    storage = TestDocumentStorage()
    storage.documents["article"] = """
# Python编程入门

## 简介
Python是一门简单易学的编程语言。

## 特点
- 语法清晰
- 功能强大
- 社区活跃

## 应用领域
Python广泛应用于数据科学、Web开发等领域。
    """.strip()
    
    registry = create_default_registry(
        storage.get_document,
        storage.write_document
    )
    
    # 场景: 读取 -> 搜索 -> 编辑 -> 验证
    print("\n[10.1] 场景: 修改文章内容")
    
    # 步骤1: 读取文档
    print("\n步骤1: 读取原文档")
    result = registry.execute("read_document", {"document_id": "article"})
    print(f"✓ 读取成功，长度: {result['length']} 字符")
    original_length = result['length']
    
    # 步骤2: 搜索特定内容
    print("\n步骤2: 搜索'Python'")
    result = registry.execute("search_document", {
        "document_id": "article",
        "query": "Python",
        "max_results": 3
    })
    print(f"✓ 找到 {result['matches']} 个匹配")
    first_match_pos = result["results"][0]["position"] if result["results"] else 0
    print(f"  第一个匹配位置: {first_match_pos}")
    
    # 步骤3: 在特定位置插入内容
    print("\n步骤3: 在'简介'段落后插入内容")
    result = registry.execute("edit_document", {
        "document_id": "article",
        "action": "insert",
        "position": 50,  # 大约在简介后面
        "content": "\n\n本文将带您快速入门Python编程。"
    })
    print(f"✓ 插入成功: {result['message']}")
    
    # 步骤4: 验证修改
    print("\n步骤4: 验证修改结果")
    result = registry.execute("read_document", {"document_id": "article"})
    new_length = result['length']
    print(f"✓ 原长度: {original_length}, 新长度: {new_length}")
    print(f"✓ 增加了 {new_length - original_length} 字符")
    assert new_length > original_length
    assert "快速入门" in result['content']
    
    # 步骤5: 替换内容
    print("\n步骤5: 替换标题")
    current_content = storage.documents["article"]
    title_pos = current_content.find("Python编程入门")
    result = registry.execute("edit_document", {
        "document_id": "article",
        "action": "replace",
        "position": title_pos,
        "end_position": title_pos + len("Python编程入门"),
        "content": "Python完全指南"
    })
    print(f"✓ 替换成功")
    
    # 最终验证
    print("\n最终验证:")
    result = registry.execute("read_document", {"document_id": "article"})
    assert "Python完全指南" in result['content']
    assert "快速入门" in result['content']
    print("✓ 所有修改都已正确应用")
    print(f"\n最终文档预览:\n{result['content'][:200]}...")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Agent工具全面测试套件")
    print("="*60)
    
    test_functions = [
        ("1. 读取文档", test_read_document),
        ("2. 写入文档", test_write_document),
        ("3. 编辑文档", test_edit_document),
        ("4. 搜索文档", test_search_document),
        ("5. 生成大纲", test_generate_outline),
        ("6. 扩写内容", test_expand_content),
        ("7. 生成摘要", test_summarize),
        ("8. 工具注册表", test_tool_registry),
        ("9. 格式规范", test_tool_definitions_format),
        ("10. 综合场景", test_integration_scenario),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for name, test_func in test_functions:
        try:
            test_func()
            passed += 1
            print(f"\n✓ {name} 测试通过")
        except AssertionError as e:
            failed += 1
            error_msg = f"{name} 断言失败: {e}"
            errors.append(error_msg)
            print(f"\n✗ {error_msg}")
        except Exception as e:
            failed += 1
            error_msg = f"{name} 运行错误: {e}"
            errors.append(error_msg)
            print(f"\n✗ {error_msg}")
            import traceback
            traceback.print_exc()
    
    # 总结报告
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"总测试数: {passed + failed}")
    print(f"✓ 通过: {passed}")
    print(f"✗ 失败: {failed}")
    
    if errors:
        print("\n失败详情:")
        for i, error in enumerate(errors, 1):
            print(f"{i}. {error}")
    
    success_rate = (passed / (passed + failed)) * 100 if (passed + failed) > 0 else 0
    print(f"\n成功率: {success_rate:.1f}%")
    
    if failed == 0:
        print("\n🎉 所有测试通过！工具系统运行正常。")
    else:
        print(f"\n⚠️ 有 {failed} 个测试失败，请检查错误信息。")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
