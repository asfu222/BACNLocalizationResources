import json
import os
from pathlib import Path
import subprocess
import binascii
import re
def strip_crc(filename: str) -> str:
    m = re.match(r"^(.+?_)(\d+)(\.[^.]+)$", filename)
    return f"{m.group(1)}{m.group(3)}" if m else filename
def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF

def apply_patch(platform: str):
    # Load bundle download info
    bundle_info_path = Path(f"bundleDownloadInfo-{platform}.json")
    if not bundle_info_path.exists():
        print(f"Missing {bundle_info_path}, skipping {platform}")
        return

    with bundle_info_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # Map stripped names to entry lists for fuzzy matching
    entries = data.get("BundleFiles", [])
    stripped_map = {}
    for entry in entries:
        old_name = entry.get("Name", "")
        key = strip_crc(old_name)
        stripped_map.setdefault(key, []).append(entry)

    # Process each resource directory
    for resource_dir in Path("./assets").iterdir():
        assets_path = resource_dir / "latest" / platform
        if not assets_path.exists():
            continue

        updated_names = {}
        for asset in assets_path.iterdir():
            if not asset.is_file():
                continue

            new_size = asset.stat().st_size
            new_crc = calculate_crc32(asset)
            key = strip_crc(asset.name)
            matches = stripped_map.get(key, [])

            if not matches:
                print(f"No matching entry for {asset.name}, skipping")
                continue
            prefix, suffix = key.rsplit(".", 1)
            new_name = f"{prefix}_{new_crc}.{suffix}"
            new_path = asset.with_name(new_name)
            asset.rename(new_path)
            asset = new_path
            
            # Take the first match
            entry = matches[0]
            old_name = entry["Name"]

            # Update fields
            entry["Name"] = asset.name
            entry["Size"] = new_size
            entry["Crc"] = new_crc
            entry["IsSplitDownload"] = False

            updated_names[old_name] = asset.name
            print(f"bundleDownloadInfo.json: 修改{old_name} -> {asset.name} 大小 {new_size}, CRC {new_crc}")

        # Write updated bundleDownloadInfo.json
        out_bundle = assets_path / "bundleDownloadInfo.json"
        with out_bundle.open("w", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"), ensure_ascii=False)
        print(f"{platform}: 已生成对应的 {out_bundle}")

        # Update catalog_Remote.json
        catalog_dir = Path(f"./catalog_{platform}")
        catalog_src = catalog_dir / "catalog_Remote.json"
        if not catalog_src.exists():
            print(f"{catalog_src} 不存在，跳过 catalog_Remote 更新")
            continue

        text = catalog_src.read_text(encoding="utf-8")
        for old, new in updated_names.items():
            # Replace all occurrences of old name with new name
            text = text.replace(old, new)

        out_catalog = assets_path / "catalog_Remote.json"
        out_catalog.write_text(text, encoding="utf-8")
        print(f"{platform}: 已生成对应的 catalog_Remote")


if __name__ == "__main__":
    apply_patch("Android")
    apply_patch("iOS")
