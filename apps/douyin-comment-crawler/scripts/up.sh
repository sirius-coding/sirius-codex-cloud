#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
mkdir -p data exports
python3 -m douyin_comment_crawler --help >/dev/null
echo "douyin-comment-crawler ready"
