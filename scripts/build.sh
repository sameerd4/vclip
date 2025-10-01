#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST="$ROOT/dist"
GALLERY_SRC="$ROOT/src/photos/gallery"
DATA_SRC="$ROOT/src/data/gallery.json"

# Ensure manifest is current
PYTHONPATH="$ROOT/src" python3 "$ROOT/src/cli.py" --build-manifest >/dev/null

rm -rf "$DIST"
mkdir -p "$DIST/gallery/landscape" "$DIST/gallery/vertical" "$DIST/data"

cp "$ROOT/web/index.html" "$DIST/"
cp "$ROOT/web/styles.css" "$DIST/"
cp "$ROOT/web/app.js" "$DIST/"
cp "$DATA_SRC" "$DIST/data/"

shopt -s nullglob
for file in "$GALLERY_SRC"/landscape/*.jpg; do
  cp "$file" "$DIST/gallery/landscape/"
done
for file in "$GALLERY_SRC"/vertical/*.jpg; do
  cp "$file" "$DIST/gallery/vertical/"
done
shopt -u nullglob

echo "Build complete → $DIST"
