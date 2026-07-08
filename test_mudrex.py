import os
import sys

# Test SDK import
try:
    from mudrex import TradeClient
    print("Mudrex SDK imported successfully")
except ImportError as e:
    print(f"Failed to import Mudrex SDK: {e}")
    sys.exit(1)
