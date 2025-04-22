#!/bin/bash

export $(grep -v '^#' ba.env | xargs)

BASE_URL=$(curl -s "$BA_SERVER_URL" | grep -oP '"AddressablesCatalogUrlRoot": *"\K[^"]+' | tail -n 1)

download_file() {
    local url=$1
    local output=$2

    while true; do
        echo "Downloading: $url"
        http_status=$(curl -s -w "%{http_code}" -o "$output" "$url")

        if [ "$http_status" -eq 200 ] && [ -s "$output" ]; then
            echo "Downloaded: $output"
            break
        else
            echo "Download failed with status $http_status or file is empty: $url"
            exit 1
        fi
    done
}


download_file "${BASE_URL}/TableBundles/TableCatalog.bytes" "TableCatalog.bytes"
download_file "${BASE_URL}/MediaResources/Catalog/MediaCatalog.bytes" "MediaCatalog.bytes"
download_file "${BASE_URL}/Android/bundleDownloadInfo.json" "bundleDownloadInfo-Android.json"
download_file "${BASE_URL}/iOS/bundleDownloadInfo.json" "bundleDownloadInfo-iOS.json"
download_file "${BASE_URL}/Android/catalog_Android.zip" "catalog_Android.zip"
download_file "${BASE_URL}/iOS/catalog_iOS.zip" "catalog_iOS.zip"
download_file "${BASE_URL}/TableBundles/Excel.zip" "Excel.zip"
download_file "${BASE_URL}/TableBundles/ExcelDB.db" "ExcelDB.db"
