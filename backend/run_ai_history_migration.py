"""
运行AI聊天历史数据库迁移
"""
import pymysql

# 读取 SQL 文件
with open('migrations/add_ai_chat_history.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 连接数据库
connection = pymysql.connect(
    host='127.0.0.1',
    port=3306,
    user='root',
    password='q88537794!',
    database='xingyun',
    charset='utf8mb4'
)

try:
    cursor = connection.cursor()
    
    # 分割并执行每个 SQL 语句
    statements = sql_content.split(';')
    for statement in statements:
        statement = statement.strip()
        if statement:
            print(f"执行: {statement[:80]}...")
            cursor.execute(statement)
    
    connection.commit()
    print("\n✓ AI聊天历史表创建成功！")
    print("✓ 索引创建成功！")
    print("✓ 视图创建成功！")
    
except Exception as e:
    connection.rollback()
    print(f"\n✗ 迁移失败: {e}")
    import traceback
    traceback.print_exc()
    
finally:
    connection.close()
