#!/bin/bash

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

BASE_URL=$(curl -s "$BA_SERVER_URL" | grep -oP '"AddressablesCatalogUrlRoot": *"\K[^"]+' | tail -n 1)

download_file() {
    local url=$1
    local output=$2

    echo "Downloading: $url"
    curl -s -o "$output" "$url"

    if [ $? -eq 0 ]; then
        echo "Downloaded: $output"
    else
        echo "Failed to download: $url"
        exit 1
    fi
}

download_file "${BASE_URL}/TableBundles/TableCatalog.bytes" "TableCatalog.bytes"
download_file "${BASE_URL}/Android/bundleDownloadInfo.json" "bundleDownloadInfo-Android.json"
download_file "${BASE_URL}/iOS/bundleDownloadInfo.json" "bundleDownloadInfo-iOS.json"

chmod +x ./crcmanip-cli
$PYTHON_CMD patch_table_catalog.py
$PYTHON_CMD patch_bundleDL.py