"""
清理creation.py中的调试日志代码块
"""
import re
from pathlib import Path

# 读取文件
file_path = Path(__file__).parent.parent / "routers" / "client" / "creation.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 使用正则表达式删除所有 # region agent log 到 # endregion 之间的内容
# 匹配模式：从 # region agent log 开始到 # endregion 结束（包括换行）
pattern = r'\s*# region agent log.*?# endregion\s*\n'
cleaned_content = re.sub(pattern, '', content, flags=re.DOTALL)

# 写回文件
with open(file_path, "w", encoding="utf-8") as f:
    f.write(cleaned_content)

# 统计删除的代码块数量
removed_count = len(re.findall(r'# region agent log', content))
print(f"Removed {removed_count} debug log blocks")

# 统计删除的行数
original_lines = content.count('\n')
cleaned_lines = cleaned_content.count('\n')
removed_lines = original_lines - cleaned_lines
print(f"Removed {removed_lines} lines of code")
print(f"Original: {original_lines} lines")
print(f"Cleaned: {cleaned_lines} lines")
print(f"Reduction: {removed_lines / original_lines * 100:.1f}%")
