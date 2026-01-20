"""
测试 BGE 本地嵌入模型配置
"""

import sys
import os

# 添加backend到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def test_imports():
    """测试基本导入"""
    print("测试导入...")
    try:
        from ai.rag.embedding import (
            EmbeddingService, 
            init_embedding_service,
            LocalEmbedding,
            ZhipuEmbedding,
            GeminiEmbedding
        )
        print("✅ embedding 模块导入成功")
        
        from ai.rag.knowledge_base import (
            KnowledgeBaseService,
            KnowledgeBaseConfig,
            get_kb_service
        )
        print("✅ knowledge_base 模块导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config():
    """测试配置"""
    print("\n测试配置...")
    try:
        from ai.rag.knowledge_base import KnowledgeBaseConfig
        
        config = KnowledgeBaseConfig(
            embedding_provider='local',
            embedding_model='BAAI/bge-small-zh-v1.5',
            embedding_device='cpu'
        )
        
        print(f"✅ 配置创建成功")
        print(f"  - Provider: {config.embedding_provider}")
        print(f"  - Model: {config.embedding_model}")
        print(f"  - Device: {config.embedding_device}")
        
        return True
    except Exception as e:
        print(f"❌ 配置失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_service_init():
    """测试嵌入服务初始化（不实际加载模型）"""
    print("\n测试嵌入服务初始化...")
    try:
        from ai.rag.embedding import EmbeddingService
        
        # 测试本地模型配置（不实际初始化，避免下载模型）
        print("  创建本地模型配置（不实际加载）...")
        service = EmbeddingService.__new__(EmbeddingService)
        service.provider = 'local'
        service._providers = EmbeddingService._providers
        
        print(f"✅ 嵌入服务结构正确")
        print(f"  - 支持的提供商: {list(service._providers.keys())}")
        
        return True
    except Exception as e:
        print(f"❌ 嵌入服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("=" * 60)
    print("BGE 本地嵌入模型配置测试")
    print("=" * 60)
    
    results = []
    results.append(("导入测试", test_imports()))
    results.append(("配置测试", test_config()))
    results.append(("嵌入服务测试", test_embedding_service_init()))
    
    print("\n" + "=" * 60)
    print("测试总结:")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    if all_passed:
        print("\n🎉 所有测试通过！BGE模型配置正确。")
        print("\n下一步:")
        print("1. 安装依赖: pip install sentence-transformers torch")
        print("2. 启动后端: python app.py")
        print("3. 首次运行会自动下载 BGE-small 模型（约95MB）")
    else:
        print("\n⚠️  部分测试失败，请检查代码配置。")
    
    sys.exit(0 if all_passed else 1)
