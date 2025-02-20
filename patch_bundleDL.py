import json
import os
from pathlib import Path
import subprocess
import binascii

def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF
def apply_patch(platform: str): 
    for resource_dir in Path('./assets').iterdir():
        assets_path = resource_dir / "latest" / platform
        if not assets_path.exists():
            continue

        asset_list = assets_path.iterdir()

        with open(f"bundleDownloadInfo-{platform}.json", "r", encoding = "utf8") as f:
            info = json.loads(f.read())["BundleFiles"]

        asset_list = [asset for asset in asset_list if asset.name in info]

        bypassable_assets = [asset for asset in asset_list if info[asset.name]["Size"] == asset.stat().st_size]

        bypass_path = resource_dir / "latest_crcbypass" / platform
        bypass_path.mkdir(parents=True, exist_ok=True)

        for asset in bypassable_assets:
            print(f"发现可直接过校验的文件({asset.Name})，正在生成跟原CRC一样的资源")
            crc = info[asset.name]["Crc"]
            subprocess.run([
                "./crcmanip-cli", "patch",
                asset, bypass_path / asset.Name,
                f'{crc:x}', "-a", "CRC32", "-o", "-p", "-4"
            ], stdout=subprocess.DEVNULL)
            print("生成完毕！")
        for asset in asset_list:
            new_size = asset.stat().st_size
            new_crc = calculate_crc32(file_path)
            print(f'bundleDownloadInfo.json: 修改{asset.name} 文件大小值 {info[asset.name]["Size"]} -> {new_size}')
            print(f'bundleDownloadInfo.json: 修改{asset.name} 文件大小值 {info[asset.name]["Crc"]} -> {new_crc}')
            info[asset.name]["Size"] = new_size
            info[asset.name]["Crc"] = new_crc
        with open(assets_path / "bundleDownloadInfo.json", "wb") as f:
            f.write(json.dumps(info, separators=(',', ':')).encode())
            print(f"{platform}: 已生成对应的bundleDownloadInfo.json")
apply_patch("Android")
apply_patch("iOS")