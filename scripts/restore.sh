#!/bin/bash
# ── SQLite 数据库恢复脚本 ──
# 用法: ./scripts/restore.sh <备份文件.gz> [目标路径]
#
# 示例:
#   ./scripts/restore.sh backups/interview_20260101_030000.db.gz

set -euo pipefail

if [ $# -lt 1 ]; then
    echo "用法: $0 <备份文件.gz> [目标路径]"
    echo "示例: $0 backups/interview_20260101_030000.db.gz data/interview.db"
    exit 1
fi

BACKUP_FILE="$1"
TARGET_DB="${2:-./data/interview.db}"
RESTORE_DIR=$(dirname "$TARGET_DB")

if [ ! -f "$BACKUP_FILE" ]; then
    echo "[ERROR] Backup file not found: $BACKUP_FILE"
    exit 1
fi

mkdir -p "$RESTORE_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restoring $BACKUP_FILE → $TARGET_DB"

# Decompress and restore
gunzip -c "$BACKUP_FILE" > /tmp/_restore_temp.db
sqlite3 "$TARGET_DB" ".restore '/tmp/_restore_temp.db'"
rm -f /tmp/_restore_temp.db

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Restore complete"
echo "       Run: sqlite3 '$TARGET_DB' 'PRAGMA integrity_check;'"
