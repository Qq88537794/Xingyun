#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG模块简化测试脚本
避免代理问题，直接测试各组件
"""

import os
import sys

# 设置环境变量禁用代理
os.environ['NO_PROXY'] = 'localhost,127.0.0.1'
os.environ['no_proxy'] = 'localhost,127.0.0.1'
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

# 设置离线模式使用缓存的模型
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['HF_HUB_OFFLINE'] = '1'

# 设置路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    print(f"\n{'='*60}")
    print(f"测试: {title}")
    print('='*60)

def print_result(success, message, details=None):
    status = "✓" if success else "✗"
    print(f"\n{status} {'成功' if success else '失败'}: {message}")
    if details:
        for key, value in details.items():
            print(f"  {key}: {value}")

def test_embedding():
    """测试Embedding服务"""
    print_header("1. Embedding服务")
    
    try:
        from ai.rag.embedding import get_embedding_service
        
        print("\n初始化Embedding服务...")
        embedding_service = get_embedding_service()
        
        # 测试单文本
        text = "Python是一门编程语言"
        vector = embedding_service.embed_text(text)
        print_result(True, "单文本嵌入", {
            "输入": text,
            "向量维度": len(vector)
        })
        
        # 测试批量
        texts = ["Python编程", "JavaScript开发", "数据分析"]
        result = embedding_service.embed_texts(texts)
        print_result(True, "批量嵌入", {
            "输入数量": len(texts),
            "输出数量": len(result.embeddings),
            "向量维度": result.dimensions
        })
        
        return True
    except Exception as e:
        print_result(False, "Embedding测试", {"错误": str(e)})
        return False

def test_chunker():
    """测试文本分块器"""
    print_header("2. 文本分块器")
    
    try:
        from ai.rag.chunker import TextChunker, ChunkingStrategy
        
        test_text = """# 标题
        
这是第一段落，包含一些内容。

这是第二段落，也包含一些内容。

## 子标题

更多内容在这里。
"""
        
        # 测试递归分块
        chunker = TextChunker(chunk_size=100, chunk_overlap=20, strategy=ChunkingStrategy.RECURSIVE)
        chunks = chunker.chunk_text(test_text)
        print_result(True, "递归分块", {"分块数": len(chunks)})
        
        # 测试段落分块
        chunker = TextChunker(chunk_size=500, chunk_overlap=0, strategy=ChunkingStrategy.PARAGRAPH)
        chunks = chunker.chunk_text(test_text)
        print_result(True, "段落分块", {"分块数": len(chunks)})
        
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print_result(False, "分块器测试", {"错误": str(e)})
        return False

def test_qdrant_connection():
    """测试Qdrant连接"""
    print_header("3. Qdrant连接")
    
    try:
        from qdrant_client import QdrantClient
        
        print("\n连接到 localhost:6333...")
        client = QdrantClient(
            host="localhost",
            port=6333,
            timeout=10
        )
        
        # 测试连接
        collections = client.get_collections()
        print_result(True, "Qdrant连接", {
            "已有集合数": len(collections.collections)
        })
        
        # 列出集合
        if collections.collections:
            print("\n  已有集合:")
            for col in collections.collections:
                print(f"    - {col.name}")
        
        return True
    except Exception as e:
        print_result(False, "Qdrant连接", {"错误": str(e)})
        return False

def test_knowledge_base():
    """测试知识库服务"""
    print_header("4. 知识库服务")
    
    try:
        from ai.rag.knowledge_base import KnowledgeBaseService, KnowledgeBaseConfig
        
        print("\n初始化知识库服务（强制使用本地模型）...")
        
        # 强制使用本地模型配置
        config = KnowledgeBaseConfig(
            qdrant_host="localhost",
            qdrant_port=6333,
            qdrant_use_memory=False,  # 使用Qdrant服务
            embedding_provider="local",  # 强制使用本地模型
            embedding_model="BAAI/bge-small-zh-v1.5",
            chunk_size=500,
            chunk_overlap=50,
        )
        
        kb_service = KnowledgeBaseService(config)
        print_result(True, "知识库服务初始化", {
            "类型": type(kb_service).__name__,
            "Embedding": "本地BGE模型"
        })
        
        # 创建测试文件
        test_dir = os.path.join(os.path.dirname(__file__), "test_kb_files")
        os.makedirs(test_dir, exist_ok=True)
        
        test_content = """# Python入门

Python是一门高级编程语言。
它具有简洁清晰的语法。
非常适合初学者学习。

## 安装

使用pip安装包：pip install package_name
"""
        
        test_file = os.path.join(test_dir, "test_python.md")
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        print("\n  创建测试文件: test_python.md")
        
        # 索引到知识库
        print("\n索引文件到知识库...")
        test_project_id = 99999
        
        result = kb_service.index_resource(
            project_id=test_project_id,
            resource_id=1,
            file_path=test_file,
            metadata={"filename": "test_python.md"}
        )
        
        if result.get("success"):
            print_result(True, "索引资源", {
                "分块数": result.get("chunk_count"),
                "总字符": result.get("total_chars")
            })
        else:
            print_result(False, "索引资源", {"错误": result.get("error")})
            return False
        
        # 测试检索
        print("\n测试检索...")
        results = kb_service.search(
            project_id=test_project_id,
            query="Python是什么",
            top_k=3
        )
        
        if results:
            print_result(True, "知识库检索", {"结果数": len(results)})
            for i, r in enumerate(results[:2], 1):
                preview = r.text[:50].replace('\n', ' ') + "..."
                print(f"    [{i}] 相似度: {r.score:.3f} | {preview}")
        else:
            print_result(False, "知识库检索", {"错误": "未找到结果"})
            return False
        
        # 清理测试文件（保留Qdrant数据用于后续测试）
        print("\n清理测试文件...")
        import shutil
        shutil.rmtree(test_dir, ignore_errors=True)
        
        print_result(True, "测试完成", {})
        
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print_result(False, "知识库测试", {"错误": str(e)})
        return False

def main():
    print("\n" + "="*60)
    print("RAG模块简化测试")
    print("="*60)
    
    results = {}
    
    # 运行测试
    results["Embedding"] = test_embedding()
    results["分块器"] = test_chunker()
    results["Qdrant"] = test_qdrant_connection()
    
    # 只有Qdrant连接成功才测试知识库
    if results["Qdrant"]:
        results["知识库"] = test_knowledge_base()
    else:
        results["知识库"] = False
        print("\n跳过知识库测试（Qdrant连接失败）")
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"  {name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有RAG组件测试通过！")
    else:
        print("\n⚠️ 部分测试失败，请检查上面的错误信息")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
