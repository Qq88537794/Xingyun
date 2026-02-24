"""
检查历史记录是否保存
"""
from app import create_app, db
from models import AIChatHistory

app = create_app()

with app.app_context():
    # 查询最近的记录
    records = AIChatHistory.query.order_by(AIChatHistory.created_at.desc()).limit(10).all()
    
    print(f"数据库中共有 {AIChatHistory.query.count()} 条历史记录")
    print(f"\n最近10条记录:")
    print("=" * 80)
    
    for r in records:
        print(f"\nID: {r.id}")
        print(f"document_id: {r.document_id}")
        print(f"user_message: {r.user_message[:50] if r.user_message else '(无)'}...")
        print(f"ai_response: {r.ai_response[:50]}...")
        print(f"created_at: {r.created_at}")
        print("-" * 80)
