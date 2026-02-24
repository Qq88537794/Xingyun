"""
清理超过3天的AI聊天历史记录
可以通过cron或任务计划程序定期运行此脚本
"""
import sys
import os

# 添加项目路径
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app import create_app
from models import AIChatHistory

def cleanup_old_records(days=3):
    """清理超过N天的旧记录"""
    app = create_app()
    
    with app.app_context():
        try:
            deleted_count = AIChatHistory.cleanup_old_records(days=days)
            print(f"✓ 成功清理 {deleted_count} 条超过 {days} 天的记录")
            return deleted_count
        except Exception as e:
            print(f"✗ 清理失败: {e}")
            import traceback
            traceback.print_exc()
            return 0

if __name__ == '__main__':
    # 默认清理3天前的记录
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    print(f"开始清理超过 {days} 天的AI聊天历史记录...")
    cleanup_old_records(days)
