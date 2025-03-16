#!/bin/bash

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
download_file "${BASE_URL}/TableBundles/Excel.zip" "Excel.zip"