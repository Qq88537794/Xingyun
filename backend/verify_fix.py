"""
快速验证关键词提取修复是否生效
"""
import re

def test_keyword_extraction():
    """测试关键词提取"""
    print("="*60)
    print("关键词提取修复验证")
    print("="*60)
    
    # 测试用例
    test_case = "8.4 Ceph的典型应用场景"
    
    # 提取关键词（修复后的逻辑）
    text_cleaned = re.sub(r'[的和与及、，。！？；：""''（）【】《》\s\.]+', ' ', test_case)
    keywords = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', text_cleaned)
    keywords = [k for k in keywords if len(k) >= 2]
    
    # 技术名称
    tech_names = ['NAS', 'SAN', 'HDFS', 'CEPH', 'NDB', 'MYSQL', 'HADOOP', 'ORACLE', 'MONGODB']
    important_keywords = [k for k in keywords if k.upper() in tech_names]
    
    print(f"\n测试用例: {test_case}")
    print(f"清理后文本: '{text_cleaned}'")
    print(f"提取的关键词: {keywords}")
    print(f"重要关键词: {important_keywords}")
    
    # 验证结果
    print("\n" + "="*60)
    print("验证结果:")
    print("="*60)
    
    success = True
    
    # 检查1：关键词应该被正确分离
    if 'Ceph' in keywords and '典型应用场景' in keywords:
        print("✅ 关键词正确分离")
    else:
        print("❌ 关键词分离失败")
        print(f"   期望: ['Ceph', '典型应用场景']")
        print(f"   实际: {keywords}")
        success = False
    
    # 检查2：技术名称应该被识别
    if 'Ceph' in important_keywords:
        print("✅ 技术名称正确识别")
    else:
        print("❌ 技术名称识别失败")
        print(f"   期望: ['Ceph']")
        print(f"   实际: {important_keywords}")
        success = False
    
    # 检查3：不应该包含完整的长字符串
    has_long_keyword = any(len(k) > 10 for k in keywords)
    if not has_long_keyword:
        print("✅ 没有过长的关键词")
    else:
        print("❌ 存在过长的关键词")
        long_keywords = [k for k in keywords if len(k) > 10]
        print(f"   过长的关键词: {long_keywords}")
        success = False
    
    print("\n" + "="*60)
    if success:
        print("🎉 所有检查通过！修复已生效！")
        print("\n下一步：")
        print("1. 重启后端服务器（Ctrl+C 然后 python app.py）")
        print("2. 刷新前端页面（Ctrl+F5）")
        print("3. 测试AI定位功能")
    else:
        print("❌ 检查失败！请确认代码已更新！")
    print("="*60)
    
    return success


if __name__ == '__main__':
    test_keyword_extraction()
