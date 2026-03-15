import os
import re

src_path = "/Users/xuhongzhe/工程/测试项目/Manim/.agent/workflows/manim-explainer.md"
dst_path = "/Users/xuhongzhe/工程/测试项目/Manim/github版本/workflows/manim-explainer.md"

with open(src_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace hardcoded user path
content = content.replace("`/Users/xuhongzhe/工程/测试项目/Manim`", "`当前工作区根目录`")
# Clean up bash commands
content = re.sub(r"cd /Users/xuhongzhe/工程/测试项目/Manim && source venv/bin/activate && ", "source venv/bin/activate && ", content)

with open(dst_path, "w", encoding="utf-8") as f:
    f.write(content)

