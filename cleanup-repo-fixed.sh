#!/bin/bash

# cleanup-repo-fixed.sh
# 매일 오래된 파일을 정리하되, 전체 용량이 3GB를 넘으면 3GB를 남기고 나머지 파일들을 자동 정리

set -e

# 설정
TARGET_SIZE_GB=3
TARGET_SIZE_BYTES=$((TARGET_SIZE_GB * 1024 * 1024 * 1024))
CLEANUP_DIRS=("./temp" "./output" "./downloads" "./generated" "./cache")
LOG_FILE="./cleanup.log"

# 로그 함수
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 바이트를 읽기 쉬운 형태로 변환
human_readable() {
    local bytes=$1
    if [ $bytes -gt $((1024*1024*1024)) ]; then
        echo "$(($bytes / 1024 / 1024 / 1024))GB"
    elif [ $bytes -gt $((1024*1024)) ]; then
        echo "$(($bytes / 1024 / 1024))MB"
    elif [ $bytes -gt 1024 ]; then
        echo "$(($bytes / 1024))KB"
    else
        echo "${bytes}B"
    fi
}

# 디렉토리별 용량 계산
get_dir_size() {
    local dir=$1
    if [ -d "$dir" ]; then
        du -sb "$dir" 2>/dev/null | cut -f1 || echo 0
    else
        echo 0
    fi
}

# 전체 용량 계산
calculate_total_size() {
    local total=0
    for dir in "${CLEANUP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            local size=$(get_dir_size "$dir")
            total=$((total + size))
        fi
    done
    echo $total
}

# 오래된 파일 정리 (7일 이상)
cleanup_old_files() {
    log "오래된 파일 정리 시작 (7일 이상)"
    
    for dir in "${CLEANUP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            log "디렉토리 정리: $dir"
            find "$dir" -type f -mtime +7 -delete 2>/dev/null || true
            find "$dir" -type d -empty -delete 2>/dev/null || true
        fi
    done
    
    log "오래된 파일 정리 완료"
}

# 용량 기준 정리 (가장 오래된 파일부터)
cleanup_by_size() {
    local current_size=$1
    local target_size=$TARGET_SIZE_BYTES
    
    log "용량 기준 정리 시작 - 현재: $(human_readable $current_size), 목표: $(human_readable $target_size)"
    
    # 모든 정리 대상 파일을 시간순으로 정렬
    local temp_file=$(mktemp)
    
    for dir in "${CLEANUP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            find "$dir" -type f -printf '%T@ %s %p\n' 2>/dev/null >> "$temp_file" || true
        fi
    done
    
    # 시간순 정렬 (오래된 것부터)
    sort -n "$temp_file" > "${temp_file}.sorted"
    
    local deleted_size=0
    while IFS= read -r line && [ $current_size -gt $target_size ]; do
        local file_path=$(echo "$line" | cut -d' ' -f3-)
        local file_size=$(echo "$line" | cut -d' ' -f2)
        
        if [ -f "$file_path" ]; then
            log "삭제: $file_path ($(human_readable $file_size))"
            rm -f "$file_path" 2>/dev/null || true
            current_size=$((current_size - file_size))
            deleted_size=$((deleted_size + file_size))
        fi
    done < "${temp_file}.sorted"
    
    # 임시 파일 정리
    rm -f "$temp_file" "${temp_file}.sorted"
    
    # 빈 디렉토리 정리
    for dir in "${CLEANUP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            find "$dir" -type d -empty -delete 2>/dev/null || true
        fi
    done
    
    log "용량 기준 정리 완료 - 삭제된 용량: $(human_readable $deleted_size)"
}

# 메인 실행 함수
main() {
    log "=== 저장소 정리 시작 ==="
    
    # 정리 대상 디렉토리 생성
    for dir in "${CLEANUP_DIRS[@]}"; do
        mkdir -p "$dir"
    done
    
    # 1. 오래된 파일 정리 (7일 이상)
    cleanup_old_files
    
    # 2. 현재 전체 용량 확인
    local current_size=$(calculate_total_size)
    log "현재 전체 용량: $(human_readable $current_size)"
    
    # 3. 용량이 3GB를 초과하면 추가 정리
    if [ $current_size -gt $TARGET_SIZE_BYTES ]; then
        log "용량 초과 감지 - 추가 정리 필요"
        cleanup_by_size $current_size
        
        # 정리 후 최종 용량 확인
        local final_size=$(calculate_total_size)
        log "정리 후 최종 용량: $(human_readable $final_size)"
    else
        log "용량이 제한 내에 있음 - 추가 정리 불필요"
    fi
    
    # 4. 상태 보고
    log "=== 정리 완료 ==="
    for dir in "${CLEANUP_DIRS[@]}"; do
        if [ -d "$dir" ]; then
            local dir_size=$(get_dir_size "$dir")
            local file_count=$(find "$dir" -type f | wc -l)
            log "  $dir: $(human_readable $dir_size) ($file_count 파일)"
        fi
    done
    
    log "총 용량: $(human_readable $(calculate_total_size))"
}

# 스크립트 실행
main "$@"
