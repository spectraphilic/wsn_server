#!/bin/bash
#
# Rotate and compress log files in var/log/.
#
# This script is safe to run before reloading/restarting Supervisor.
# It renames non-empty *.log files with a timestamp suffix; after the
# reload, Supervisor will create fresh log files with the original names.
#
# Usage:
#
#   ./ansible/rotate-logs.sh            # rotate current *.log files
#   ./ansible/rotate-logs.sh --compress # gzip already rotated *.log.<timestamp> files
#

set -euo pipefail

COMPRESS_ONLY=false

while [ $# -gt 0 ]; do
    case "$1" in
        --compress)
            COMPRESS_ONLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            echo "Usage: $0 [--compress]" >&2
            exit 1
            ;;
    esac
done

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/var/log"

if [ ! -d "$LOG_DIR" ]; then
    echo "Log directory does not exist: $LOG_DIR"
    exit 0
fi

if [ "$COMPRESS_ONLY" = true ]; then
    COMPRESSED=0
    while IFS= read -r rotated; do
        [ -n "$rotated" ] || continue
        gzip "$rotated"
        echo "Compressed: $rotated.gz"
        COMPRESSED=$((COMPRESSED + 1))
    done < <(find "$LOG_DIR" -maxdepth 1 -type f -name '*.log.*' ! -name '*.gz')

    if [ "$COMPRESSED" -eq 0 ]; then
        echo "No rotated logs to compress in $LOG_DIR"
    fi
else
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    ROTATED=0

    for logfile in "$LOG_DIR"/*.log; do
        [ -e "$logfile" ] || continue

        # Skip already rotated files and empty files.
        if [ -s "$logfile" ]; then
            mv "$logfile" "$logfile.$TIMESTAMP"
            echo "Rotated: $logfile -> $logfile.$TIMESTAMP"
            ROTATED=$((ROTATED + 1))
        fi
    done

    if [ "$ROTATED" -eq 0 ]; then
        echo "No logs to rotate in $LOG_DIR"
    fi
fi
