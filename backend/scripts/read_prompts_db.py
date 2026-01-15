"""
读取 prompts.db 数据库结构
"""
import sqlite3
import json
from pathlib import Path

db_path = Path("E:/project/sfire-ai/database/prompts.db")

if not db_path.exists():
    print(f"数据库文件不存在: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 获取所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("表列表:", tables)

# 获取 prompts 表结构
cursor.execute("PRAGMA table_info(prompts)")
columns = cursor.fetchall()
print("\n表结构 (prompts):")
for col in columns:
    print(f"  {col}")

# 获取示例数据
cursor.execute("SELECT * FROM prompts LIMIT 10")
rows = cursor.fetchall()
print("\n示例数据 (前10条):")
for i, row in enumerate(rows, 1):
    print(f"\n第 {i} 条:")
    for j, col in enumerate(columns):
        print(f"  {col[1]}: {row[j]}")

# 获取所有数据
cursor.execute("SELECT COUNT(*) FROM prompts")
count = cursor.fetchone()[0]
print(f"\n总记录数: {count}")

conn.close()





















