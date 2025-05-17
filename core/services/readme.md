若不运行 Django 主程序 [manage.py 文件](../../manage.py), 但想测试本文件夹下的各类 `service` 程序时, 需要在程序前导入 Django 设置, 具体代码见下:

```python
import os
import sys
import django

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BiDms.settings")
django.setup()
```