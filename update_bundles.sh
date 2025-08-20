#!/bin/bash

export $(grep -v '^#' ba.env | xargs)

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

download_file "${ADDRESSABLE_CATALOG_URL}/Android_PatchPack/BundlePackingInfo.json" "BundlePackingInfo-Android.json"
download_file "${ADDRESSABLE_CATALOG_URL}/iOS_PatchPack/BundlePackingInfo.json" "BundlePackingInfo-iOS.json"
# Switch to {OS}_PatchPack/BundlePackingInfo.json -> full patch zip
download_file "${ADDRESSABLE_CATALOG_URL}/Android_PatchPack/catalog_Android.zip" "catalog_Android.zip"
download_file "${ADDRESSABLE_CATALOG_URL}/iOS_PatchPack/catalog_iOS.zip" "catalog_iOS.zip"