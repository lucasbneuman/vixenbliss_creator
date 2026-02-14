import app.services.lora_inference as m
import inspect
print('module file:', m.__file__)
src = inspect.getsource(m)
print('\n---SOURCE START---\n')
print('\n'.join(src.splitlines()[:200]))
print('\n---SOURCE END---\n')
