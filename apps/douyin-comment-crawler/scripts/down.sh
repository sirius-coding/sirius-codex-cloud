#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
echo "douyin-comment-crawler has no background service to stop"
echo "data/ and exports/ are kept for resume and delivery files"
