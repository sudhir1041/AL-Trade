import sys
import py_compile

try:
    py_compile.compile('trademind-ai/backend/apps/exchanges/adapters/mudrex.py', doraise=True)
    print("Syntax OK")
except py_compile.PyCompileError as e:
    print(f"Syntax Error: {e}")
    sys.exit(1)
