import os
import sys
import importlib

# Force reimport
if 'app.services.lora_inference' in sys.modules:
    del sys.modules['app.services.lora_inference']

from app.services import lora_inference

print("Module file:", lora_inference.__file__)
print("Module mtime:", os.path.getmtime(lora_inference.__file__))

# Check if the module has the  new code
import inspect
source = inspect.getsource(lora_inference)
if "Unknown LORA provider" in source:
    print("FOUND: 'Unknown LORA provider' in source")
    # Find and print the line
    for i, line in enumerate(source.split("\n")):
        if "Unknown LORA provider" in line:
            print(f"  Line {i}: {line}")
else:
    print("NOT FOUND: 'Unknown LORA provider' in source")

if "DEBUG: Attempting fallback" in source:
    print("FOUND: DEBUG statements in source")
else:
    print("NOT FOUND: DEBUG statements in source")
