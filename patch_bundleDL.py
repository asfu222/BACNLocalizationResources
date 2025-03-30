import json
import os
from pathlib import Path
import subprocess
import binascii

def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF

def apply_patch(platform: str):
    with open(f"bundleDownloadInfo-{platform}.json", "r", encoding="utf8") as f:
        data = json.load(f)
    info = {struct["Name"]: struct for struct in data["BundleFiles"]}

    base_to_entries = {}
    for entry in data["BundleFiles"]:
        name = entry["Name"]
        if name.endswith(".bundle"):
            parts = name.rsplit('_', 1)
            if len(parts) == 2 and parts[1].split('.', 1)[0].isdigit():
                base_part = parts[0]
            else:
                base_part = name.rsplit('.', 1)[0]
        else:
            base_part = name
        if base_part not in base_to_entries:
            base_to_entries[base_part] = []
        base_to_entries[base_part].append(entry)

    for resource_dir in Path('./assets').iterdir():
        assets_path = resource_dir / "latest" / platform
        if not assets_path.exists():
            continue

        for asset_file in assets_path.iterdir():
            if not asset_file.is_file():
                continue  # Skip directories

            original_name = asset_file.name
            if original_name.endswith(".bundle"):
                parts = original_name.rsplit('_', 1)
                if len(parts) == 2 and parts[1].split('.', 1)[0].isdigit():
                    asset_base = parts[0]
                else:
                    asset_base = original_name.rsplit('.', 1)[0]
            else:
                asset_base = original_name

            if asset_base in base_to_entries and len(base_to_entries[asset_base]) == 1:
                target_entry = base_to_entries[asset_base][0]
                target_name = target_entry["Name"]
                if original_name != target_name:
                    new_path = asset_file.parent / target_name
                    asset_file.rename(new_path)
                    #subprocess.run(["git", "add", str(asset_file), str(new_path)], check=True)

    for resource_dir in Path('./assets').iterdir():
        assets_path = resource_dir / "latest" / platform
        if not assets_path.exists():
            continue

        asset_list = list(assets_path.iterdir())

        with open(f"bundleDownloadInfo-{platform}.json", "r", encoding="utf8") as f:
            data = json.load(f)
            info = {struct["Name"]: struct for struct in data["BundleFiles"]}

        asset_list = [asset for asset in asset_list if asset.name in info]

        for asset in asset_list:
            new_size = asset.stat().st_size
            new_crc = calculate_crc32(asset)
            print(f'bundleDownloadInfo.json: 修改{asset.name} 文件大小值 {info[asset.name]["Size"]} -> {new_size}')
            print(f'bundleDownloadInfo.json: 修改{asset.name} CRC值 {info[asset.name]["Crc"]} -> {new_crc}')
            info[asset.name]["Size"] = new_size
            info[asset.name]["Crc"] = new_crc
            info[asset.name]["IsPrologue"] = True
            info[asset.name]["IsSplitDownload"] = False

        updated_json_path = assets_path / "bundleDownloadInfo.json"
        with open(updated_json_path, "wb") as f:
            json_data = json.dumps(data, separators=(',', ':'))
            f.write(json_data.encode('utf-8'))
            print(f"{platform}: 已生成对应的bundleDownloadInfo.json")
apply_patch("Android")
apply_patch("iOS")
'''
result = subprocess.run(["git", "diff", "--cached", "--quiet"], capture_output=True)
if result.returncode != 0:
    subprocess.run(["git", "commit", "-m", "Automated rename and update of asset files"], check=True)
    print("Git commit performed.")
else:
    print("No changes to commit.")
'''