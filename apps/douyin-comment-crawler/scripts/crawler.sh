#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$APP_DIR"

if [[ -t 1 ]] && [[ "${NO_COLOR:-}" == "" ]]; then
  BOLD="$(printf '\033[1m')"
  DIM="$(printf '\033[2m')"
  RED="$(printf '\033[31m')"
  GREEN="$(printf '\033[32m')"
  YELLOW="$(printf '\033[33m')"
  BLUE="$(printf '\033[34m')"
  MAGENTA="$(printf '\033[35m')"
  CYAN="$(printf '\033[36m')"
  RESET="$(printf '\033[0m')"
else
  BOLD=""
  DIM=""
  RED=""
  GREEN=""
  YELLOW=""
  BLUE=""
  MAGENTA=""
  CYAN=""
  RESET=""
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
DEFAULT_PAGE_SIZE="${CRAWLER_PAGE_SIZE:-50}"
DEFAULT_WORKERS="${CRAWLER_WORKERS:-4}"
DEFAULT_MIN_DELAY="${CRAWLER_MIN_DELAY:-0.5}"
DEFAULT_MAX_DELAY="${CRAWLER_MAX_DELAY:-1.5}"
DEFAULT_WATCH_SECONDS="${CRAWLER_WATCH_SECONDS:-5}"
LAST_JOB_ID=""

usage() {
  cat <<'EOF'
Douyin Comment Crawler 操作台

用法:
  bash scripts/crawler.sh
  bash scripts/crawler.sh --help

环境变量默认值:
  CRAWLER_PAGE_SIZE      默认 50
  CRAWLER_WORKERS        默认 4
  CRAWLER_MIN_DELAY      默认 0.5
  CRAWLER_MAX_DELAY      默认 1.5
  CRAWLER_WATCH_SECONDS  默认 5
  PYTHON_BIN             默认 python3
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

hr() {
  printf '%s\n' "${DIM}────────────────────────────────────────────────────────────${RESET}"
}

title() {
  clear_screen
  printf '%s\n' "${BOLD}${CYAN}抖音评论采集操作台${RESET}"
  printf '%s\n' "${DIM}${APP_DIR}${RESET}"
  hr
}

clear_screen() {
  if [[ -t 1 ]]; then
    clear
  fi
}

info() {
  printf '%s\n' "${BLUE}INFO${RESET} $*"
}

ok() {
  printf '%s\n' "${GREEN}OK${RESET} $*"
}

warn() {
  printf '%s\n' "${YELLOW}WARN${RESET} $*"
}

error() {
  printf '%s\n' "${RED}ERR${RESET} $*" >&2
}

pause() {
  printf '\n%s' "${DIM}按 Enter 返回...${RESET}"
  read -r _ || true
}

confirm() {
  local prompt="$1"
  local default="${2:-n}"
  local answer
  local suffix="[y/N]"
  if [[ "$default" == "y" ]]; then
    suffix="[Y/n]"
  fi
  read -r -p "$(printf '%s %s ' "$prompt" "$suffix")" answer || true
  answer="${answer:-$default}"
  [[ "$answer" == "y" || "$answer" == "Y" ]]
}

ask_required() {
  local prompt="$1"
  local value=""
  while [[ -z "$value" ]]; do
    read -r -p "$(printf '%s%s%s: ' "$BOLD" "$prompt" "$RESET")" value || true
    if [[ -z "$value" ]]; then
      warn "该项必填。"
    fi
  done
  printf '%s' "$value"
}

ask_default() {
  local prompt="$1"
  local default="$2"
  local value
  read -r -p "$(printf '%s [%s]: ' "$prompt" "$default")" value || true
  printf '%s' "${value:-$default}"
}

check_ready() {
  mkdir -p data exports
  if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    error "找不到 $PYTHON_BIN。可用 PYTHON_BIN=/path/to/python 覆盖。"
    return 1
  fi
  if [[ ! -f ".env" ]]; then
    warn "未找到 .env。"
    if [[ -f ".env.example" ]] && confirm "是否从 .env.example 创建 .env？" "y"; then
      cp .env.example .env
      warn "已创建 .env，请先写入 DOUYIN_API_BASE_URL 后再执行真实采集。"
    fi
  fi
  if ! "$PYTHON_BIN" -m douyin_comment_crawler --help >/dev/null; then
    error "CLI smoke check 失败。"
    return 1
  fi
  ok "CLI 可用。"
}

extract_job_id() {
  awk -F= '/^job_id=/{print $2; exit}' "$1"
}

run_and_capture_job() {
  local tmp
  tmp="$(mktemp)"
  set +e
  "$@" 2>&1 | tee "$tmp"
  local code="${PIPESTATUS[0]}"
  set -e
  LAST_JOB_ID="$(extract_job_id "$tmp")"
  rm -f "$tmp"
  if [[ "$code" -ne 0 ]]; then
    error "命令失败，exit=$code"
    return "$code"
  fi
  if [[ -n "$LAST_JOB_ID" ]]; then
    ok "任务 ID: ${BOLD}${LAST_JOB_ID}${RESET}"
    after_job_menu "$LAST_JOB_ID"
  fi
}

set_common_args() {
  local page_size="$1"
  local workers="$2"
  local min_delay="$3"
  local max_delay="$4"
  COMMON_ARGS=(--page-size "$page_size" --workers "$workers" --min-delay "$min_delay" --max-delay "$max_delay")
}

prompt_tuning() {
  PAGE_SIZE="$(ask_default "page_size" "$DEFAULT_PAGE_SIZE")"
  WORKERS="$(ask_default "workers" "$DEFAULT_WORKERS")"
  MIN_DELAY="$(ask_default "min_delay" "$DEFAULT_MIN_DELAY")"
  MAX_DELAY="$(ask_default "max_delay" "$DEFAULT_MAX_DELAY")"
}

show_status() {
  local job_id="$1"
  if [[ -z "$job_id" ]]; then
    "$PYTHON_BIN" -m douyin_comment_crawler status
  else
    "$PYTHON_BIN" -m douyin_comment_crawler status --job-id "$job_id"
  fi
}

highlight_status() {
  local line key value
  while IFS= read -r line; do
    key="${line%%=*}"
    value="${line#*=}"
    case "$key" in
      job_id)
        printf '%s=%s%s%s\n' "$key" "$BOLD" "$value" "$RESET"
        ;;
      status)
        case "$value" in
          completed) printf '%s=%s%s%s\n' "$key" "$GREEN" "$value" "$RESET" ;;
          cooldown) printf '%s=%s%s%s\n' "$key" "$YELLOW" "$value" "$RESET" ;;
          failed) printf '%s=%s%s%s\n' "$key" "$RED" "$value" "$RESET" ;;
          *) printf '%s=%s%s%s\n' "$key" "$CYAN" "$value" "$RESET" ;;
        esac
        ;;
      comments|videos_seen|comments_seen|comments_saved|replies_seen|api_requests)
        printf '%s=%s%s%s\n' "$key" "$MAGENTA" "$value" "$RESET"
        ;;
      last_error|cooldown_until)
        printf '%s=%s%s%s\n' "$key" "$YELLOW" "$value" "$RESET"
        ;;
      *)
        printf '%s\n' "$line"
        ;;
    esac
  done
}

status_value() {
  local job_id="$1"
  "$PYTHON_BIN" -m douyin_comment_crawler status --job-id "$job_id" 2>/dev/null | awk -F= '/^status=/{print $2; exit}'
}

watch_job() {
  local job_id="$1"
  local interval
  interval="$(ask_default "刷新间隔秒" "$DEFAULT_WATCH_SECONDS")"
  warn "按 Ctrl+C 停止监控并进入快捷操作。"
  trap 'trap - INT; printf "\n"; return 0' INT
  while true; do
    clear_screen
    printf '%s\n' "${BOLD}${CYAN}实时监控任务${RESET} ${BOLD}${job_id}${RESET}"
    hr
    show_status "$job_id" | highlight_status
    hr
    printf '%s\n' "${DIM}每 ${interval}s 刷新。Ctrl+C 停止。${RESET}"
    sleep "$interval"
  done
}

after_job_menu() {
  local job_id="$1"
  while true; do
    local state
    state="$(status_value "$job_id")"
    printf '\n%s\n' "${BOLD}任务快捷操作${RESET} ${DIM}(status=${state:-unknown})${RESET}"
    printf '%s\n' "1. 实时监控"
    printf '%s\n' "2. 查看状态"
    printf '%s\n' "3. Resume"
    printf '%s\n' "4. 补采回复"
    printf '%s\n' "5. 导出"
    printf '%s\n' "6. 返回主菜单"
    read -r -p "请选择 [1-6]: " choice || true
    case "$choice" in
      1) watch_job "$job_id" ;;
      2) show_status "$job_id" | highlight_status; pause ;;
      3) resume_job "$job_id" ;;
      4) crawl_replies "$job_id" ;;
      5) export_job "$job_id" ;;
      6|"") return 0 ;;
      *) warn "无效选择。" ;;
    esac
  done
}

crawl_video() {
  title
  printf '%s\n' "${BOLD}单视频采集${RESET}"
  local mode target include
  mode="$(ask_default "目标类型：1=aweme-id, 2=url" "1")"
  if [[ "$mode" == "2" ]]; then
    target="$(ask_required "视频 URL")"
    TARGET_ARG=(--url "$target")
  else
    target="$(ask_required "aweme-id")"
    TARGET_ARG=(--aweme-id "$target")
  fi
  include=()
  if confirm "是否同时采集回复？大任务建议选 n，后续用补采回复。" "n"; then
    include=(--include-replies)
  fi
  prompt_tuning
  set_common_args "$PAGE_SIZE" "$WORKERS" "$MIN_DELAY" "$MAX_DELAY"
  run_and_capture_job "$PYTHON_BIN" -m douyin_comment_crawler crawl video "${TARGET_ARG[@]}" "${include[@]}" "${COMMON_ARGS[@]}"
}

crawl_account() {
  title
  printf '%s\n' "${BOLD}账号作品主评论采集${RESET}"
  local mode target include
  mode="$(ask_default "目标类型：1=sec-user-id, 2=url" "1")"
  if [[ "$mode" == "2" ]]; then
    target="$(ask_required "账号 URL")"
    TARGET_ARG=(--url "$target")
  else
    target="$(ask_required "sec-user-id")"
    TARGET_ARG=(--sec-user-id "$target")
  fi
  include=()
  if confirm "是否同时采集回复？推荐 n，主评论完成后再补采。" "n"; then
    include=(--include-replies)
  fi
  prompt_tuning
  set_common_args "$PAGE_SIZE" "$WORKERS" "$MIN_DELAY" "$MAX_DELAY"
  run_and_capture_job "$PYTHON_BIN" -m douyin_comment_crawler crawl account "${TARGET_ARG[@]}" "${include[@]}" "${COMMON_ARGS[@]}"
}

crawl_replies() {
  local job_id="${1:-}"
  title
  printf '%s\n' "${BOLD}二阶段补采回复${RESET}"
  if [[ -z "$job_id" ]]; then
    job_id="$(ask_required "job_id")"
  else
    printf 'job_id=%s%s%s\n' "$BOLD" "$job_id" "$RESET"
  fi
  prompt_tuning
  set_common_args "$PAGE_SIZE" "$WORKERS" "$MIN_DELAY" "$MAX_DELAY"
  run_and_capture_job "$PYTHON_BIN" -m douyin_comment_crawler crawl replies --job-id "$job_id" "${COMMON_ARGS[@]}"
}

batch_crawl() {
  title
  printf '%s\n' "${BOLD}批量文件采集${RESET}"
  local file include
  file="$(ask_required "批量文件路径")"
  if [[ ! -f "$file" ]]; then
    error "文件不存在: $file"
    pause
    return 0
  fi
  include=()
  if confirm "是否同时采集回复？推荐 n，主评论完成后再补采。" "n"; then
    include=(--include-replies)
  fi
  prompt_tuning
  set_common_args "$PAGE_SIZE" "$WORKERS" "$MIN_DELAY" "$MAX_DELAY"
  "$PYTHON_BIN" -m douyin_comment_crawler batch --file "$file" "${include[@]}" "${COMMON_ARGS[@]}"
  pause
}

view_status_menu() {
  title
  printf '%s\n' "${BOLD}查看状态${RESET}"
  local job_id
  read -r -p "job_id（留空查看最近任务）: " job_id || true
  show_status "$job_id" | highlight_status
  pause
}

watch_menu() {
  title
  local job_id
  job_id="$(ask_required "job_id")"
  watch_job "$job_id"
  after_job_menu "$job_id"
}

export_job() {
  local job_id="${1:-}"
  title
  printf '%s\n' "${BOLD}导出任务数据${RESET}"
  if [[ -z "$job_id" ]]; then
    job_id="$(ask_required "job_id")"
  else
    printf 'job_id=%s%s%s\n' "$BOLD" "$job_id" "$RESET"
  fi
  local fmt
  fmt="$(ask_default "导出格式 jsonl/csv" "csv")"
  local flags=()
  if confirm "过滤空文本 empty_text？" "y"; then
    flags+=(--exclude-flag empty_text)
  fi
  if confirm "过滤纯媒体 media_only？" "y"; then
    flags+=(--exclude-flag media_only)
  fi
  "$PYTHON_BIN" -m douyin_comment_crawler export --job-id "$job_id" --format "$fmt" "${flags[@]}"
  pause
}

resume_job() {
  local job_id="${1:-}"
  title
  printf '%s\n' "${BOLD}Resume 任务${RESET}"
  if [[ -z "$job_id" ]]; then
    job_id="$(ask_required "job_id")"
  else
    printf 'job_id=%s%s%s\n' "$BOLD" "$job_id" "$RESET"
  fi
  prompt_tuning
  set_common_args "$PAGE_SIZE" "$WORKERS" "$MIN_DELAY" "$MAX_DELAY"
  run_and_capture_job "$PYTHON_BIN" -m douyin_comment_crawler resume --job-id "$job_id" "${COMMON_ARGS[@]}"
}

health_menu() {
  title
  printf '%s\n' "${BOLD}账号组健康状态${RESET}"
  "$PYTHON_BIN" -m douyin_comment_crawler status --health | highlight_status
  pause
}

main_menu() {
  while true; do
    title
    printf '%s\n' "${BOLD}默认性能参数${RESET}: page_size=${MAGENTA}${DEFAULT_PAGE_SIZE}${RESET} workers=${MAGENTA}${DEFAULT_WORKERS}${RESET} delay=${MAGENTA}${DEFAULT_MIN_DELAY}-${DEFAULT_MAX_DELAY}s/request${RESET}"
    printf '%s\n' "${DIM}建议：大任务先采主评论，再补采回复。${RESET}"
    hr
    printf '%s\n' "1. 采集单个视频"
    printf '%s\n' "2. 采集账号作品主评论"
    printf '%s\n' "3. 为已有任务补采回复"
    printf '%s\n' "4. 批量文件采集"
    printf '%s\n' "5. 查看任务状态"
    printf '%s\n' "6. 实时监控任务"
    printf '%s\n' "7. 导出任务数据"
    printf '%s\n' "8. Resume 失败/冷却任务"
    printf '%s\n' "9. 查看账号组健康状态"
    printf '%s\n' "0. 退出"
    hr
    read -r -p "请选择 [0-9]: " choice || true
    case "$choice" in
      1) crawl_video ;;
      2) crawl_account ;;
      3) crawl_replies ;;
      4) batch_crawl ;;
      5) view_status_menu ;;
      6) watch_menu ;;
      7) export_job ;;
      8) resume_job ;;
      9) health_menu ;;
      0) exit 0 ;;
      *) warn "无效选择。"; sleep 1 ;;
    esac
  done
}

check_ready
main_menu
