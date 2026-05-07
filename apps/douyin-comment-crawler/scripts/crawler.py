#!/usr/bin/env python3
from pathlib import Path
import os
import sys


APP_DIR = Path(__file__).resolve().parents[1]
os.chdir(APP_DIR)
sys.path.insert(0, str(APP_DIR))

from douyin_comment_crawler.tui import main


if __name__ == "__main__":
    main()
