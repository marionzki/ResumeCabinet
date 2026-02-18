import ast
import sys

filename = 'view_flet/forms.py'
try:
    with open(filename, 'r', encoding='utf-8') as f:
        source = f.read()
    ast.parse(source)
    print(f"Syntax OK in {filename}")
except Exception as e:
    print(f"Syntax Error in {filename}: {e}")
    sys.exit(1)
