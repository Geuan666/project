#!/usr/bin/env bash
set -euo pipefail

docfile="$1"
docdir="$2"
docbase="${docfile%.tex}"

mkdir -p "$docdir/other"
cd "$docdir"

latexmk \
  -synctex=1 \
  -interaction=nonstopmode \
  -file-line-error \
  -pdfxe \
  -outdir="$docdir" \
  -auxdir="$docdir/other" \
  -emulate-aux-dir \
  "$docfile"

mv -f "$docbase.fls" "other/$docbase.fls" 2>/dev/null || true
