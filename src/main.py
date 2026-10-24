"""程序入口。

文件：main.py
功能：把命令行界面作为模块启动点。

用法：
    .\\.venv\\Scripts\\python.exe -m src.main
    .\\.venv\\Scripts\\python.exe -m src.main init
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
