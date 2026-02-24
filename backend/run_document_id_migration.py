"""
执行添加 document_id 字段的数据库迁移
"""
import os
import sys
from app import create_app, db

def run_migration():
    """执行迁移"""
    app = create_app()
    
    with app.app_context():
        try:
            # 读取迁移SQL文件
            migration_file = os.path.join(
                os.path.dirname(__file__),
                'migrations',
                'add_document_id_to_ai_history.sql'
            )
            
            with open(migration_file, 'r', encoding='utf-8') as f:
                sql = f.read()
            
            # 分割SQL语句（按分号分割）
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            
            # 执行每条SQL语句
            for statement in statements:
                if statement:
                    print(f"执行: {statement[:100]}...")
                    db.session.execute(db.text(statement))
            
            db.session.commit()
            print("✅ 迁移成功完成！")
            print("已为 ai_chat_history 表添加 document_id 字段")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 迁移失败: {e}")
            sys.exit(1)

if __name__ == '__main__':
    run_migration()
