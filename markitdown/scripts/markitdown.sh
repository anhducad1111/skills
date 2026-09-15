#!/usr/bin/env bash
# markitdown.sh — wrapper for microsoft/markitdown CLI
set -euo pipefail

export PYTHONWARNINGS="ignore"

if ! command -v markitdown >/dev/null 2>&1; then
    echo "ERR: markitdown not found in PATH. Install with: pip install 'markitdown[all]'" >&2
    exit 127
fi

INPUT="${1:-}"
OUTPUT="${2:-}"

if [[ -z "$INPUT" ]]; then
    echo "Usage: $0 <file-or-url-or-dir> [output-path]" >&2
    exit 1
fi

if [[ "$INPUT" =~ ^https?:// ]]; then
    if [[ -n "$OUTPUT" ]]; then
        markitdown "$INPUT" -o "$OUTPUT"
    else
        markitdown "$INPUT"
    fi
    exit $?
fi

if [[ -d "$INPUT" ]]; then
    DEST="${OUTPUT:-$INPUT/markdown_output}"
    mkdir -p "$DEST"
    find "$INPUT" -maxdepth 1 -type f \( \
        -name "*.pdf" -o -name "*.docx" -o -name "*.pptx" -o -name "*.xlsx" -o \
        -name "*.html" -o -name "*.csv" -o -name "*.json" -o -name "*.xml" -o \
        -name "*.zip" -o -name "*.epub" -o -name "*.jpg" -o -name "*.png" \
    \) | while read -r file; do
        base=$(basename "$file")
        stem="${base%.*}"
        echo "Converting $file -> $DEST/$stem.md"
        markitdown "$file" -o "$DEST/$stem.md"
    done
elif [[ -f "$INPUT" ]]; then
    if [[ -n "$OUTPUT" ]]; then
        mkdir -p "$(dirname "$OUTPUT")"
        markitdown "$INPUT" -o "$OUTPUT"
    else
        markitdown "$INPUT"
    fi
else
    echo "ERR: File or directory does not exist: $INPUT" >&2
    exit 1
fi
