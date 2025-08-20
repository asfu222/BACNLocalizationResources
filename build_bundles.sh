#!/bin/bash

set -euo pipefail
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed!" >&2
    exit 1
fi

echo "Using $PYTHON_CMD"

export $(grep -v '^#' ba.env | xargs)

# Extract catalog_Remotes
[ -f ./catalog_Android.zip ] && unzip -o ./catalog_Android.zip -d ./catalog_Android
[ -f ./catalog_iOS.zip ] && unzip -o ./catalog_iOS.zip -d ./catalog_iOS

$PYTHON_CMD patch_bundleDL.py $ADDRESSABLE_CATALOG_URL

# Zip catalog_Remotes
find . -type f -path "*/Android_PatchPack/catalog_Remote.json" -exec sh -c '
  dir=$(dirname "{}")
  zip -j "$dir/catalog_Android.zip" "{}" && rm "{}"
' \;
find . -type f -path "*/iOS_PatchPack/catalog_Remote.json" -exec sh -c '
  dir=$(dirname "{}")
  zip -j "$dir/catalog_iOS.zip" "{}" && rm "{}"
' \;

find . -type d -name "temp" -exec rm -rf {} +
$PYTHON_CMD generate_catalog.py