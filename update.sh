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

TB_BASE_URL=$(export $(grep -v '^#' ba.env | xargs) && curl -s "$BA_SERVER_URL" | grep -oP '"AddressablesCatalogUrlRoot": *"\K[^"]+' | tail -n 1)"/TableBundles/"


# Define file URLs
TABLE_CATALOG="${TB_BASE_URL}TableCatalog.bytes"
TABLE_CATALOG_HASH="${TB_BASE_URL}TableCatalog.hash"

# Download function
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

# Download the files
download_file "$TABLE_CATALOG" "TableCatalog.bytes"

chmod +x ./crcmanip-cli
$PYTHON_CMD patch_table_catalog.py