import pymysql

# 读取 SQL 文件
with open('migrations/add_folders.sql', 'r', encoding='utf-8') as f:
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
            print(f"执行: {statement[:50]}...")
            cursor.execute(statement)
    
    connection.commit()
    print("\n✓ 数据库迁移成功完成！")
    
except Exception as e:
    connection.rollback()
    print(f"\n✗ 迁移失败: {e}")
    
finally:
    connection.close()
