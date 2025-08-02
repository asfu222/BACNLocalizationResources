import json
from pathlib import Path
import subprocess
import binascii
import re
import shutil
import requests
import argparse
from zipfile import ZipFile
def strip_crc(filename: str) -> str:
    m = re.match(r"^(.+?_)(\d+)(\.[^.]+)$", filename)
    return f"{m.group(1)}{m.group(3)}" if m else filename

def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF

def download_and_extract_if_needed(root_url: str, assets_path: Path, platform: str, pack_name: str):
    zip_path = Path("bundle_cache") / platform / pack_name
    extract_path = assets_path / "temp" / pack_name

    if not extract_path.exists():
        if not zip_path.exists():
            url = f"{root_url}/{platform}_PatchPack/{pack_name}"
            print(f"Downloading pack {pack_name} from {url}")
            response = requests.get(url)
            response.raise_for_status()
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            with open(zip_path, 'wb') as f:
                f.write(response.content)
            print(f"Saved {pack_name} to cache.")

        print(f"Extracting {pack_name} to {extract_path}")
        extract_path.mkdir(parents=True, exist_ok=True)
        with ZipFile(zip_path, 'r') as z:
            z.extractall(extract_path)
    else:
        print(f"{pack_name} already extracted.")

def apply_patch(root_url: str, platform: str):
    # Load bundle download info
    bundle_info_path = Path(f"BundlePackingInfo-{platform}.json")
    if not bundle_info_path.exists():
        print(f"Missing {bundle_info_path}, skipping {platform}")
        return

    with bundle_info_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    stripped_map = {}
    # Mark zips which contain target files
    for pack in data["FullPatchPacks"] + data["UpdatePacks"]:        
        # Map stripped names to entry lists for fuzzy matching
        entries = pack.get("BundleFiles", [])

        for entry in entries:
            old_name = entry.get("Name", "")
            key = strip_crc(old_name)
            stripped_map.setdefault(key, []).append((pack, entry))

    # Process each resource directory
    for resource_dir in Path("./assets").iterdir():
        assets_path = resource_dir / "latest" / f"{platform}_PatchPack"
        if not assets_path.exists():
            continue

        updated_names = {}
        modified_packs = {}

        for asset in assets_path.glob("*.bundle"):
            if not asset.is_file():
                continue

            new_size = asset.stat().st_size
            new_crc = calculate_crc32(asset)
            key = strip_crc(asset.name)
            matches = stripped_map.get(key, [])

            if not matches:
                print(f"No matching entry for {asset.name}, skipping")
                print(key)
                continue
            prefix, suffix = key.rsplit(".", 1)
            new_name = f"{prefix}{new_crc}.{suffix}"
            new_path = asset.with_name(new_name)
            asset.rename(new_path)
            asset = new_path
            
            # Update all matches
            for pack, entry in matches:
                download_and_extract_if_needed(root_url, assets_path, platform, pack["PackName"])
                
                modified_packs[pack["PackName"]] = pack
                
                old_name = entry["Name"]

                # Update fields
                entry["Name"] = asset.name
                entry["Size"] = new_size
                entry["Crc"] = new_crc
                entry["IsSplitDownload"] = False

                updated_names[old_name] = asset.name
                
                dest = assets_path / "temp" / pack["PackName"]
                dest.mkdir(parents=True, exist_ok=True)
                
                shutil.copy(asset, dest / asset.name)
                old_path = dest / old_name
                old_path.unlink()
                
                print(f"BundlePackingInfo.json: 修改{old_name} -> {asset.name} 大小 {new_size}, CRC {new_crc}")
        for pack_dir in assets_path.joinpath("temp").iterdir():
            if not pack_dir.is_dir():
                continue
            output_zip = assets_path / f"{pack_dir.name}"
            cmd = ["zip", "-r", "-X", "-9", str(output_zip.resolve()), "."]
            subprocess.run(cmd, cwd=pack_dir, check=True)
            
            pack = modified_packs[output_zip.name]
            pack["PackSize"] = output_zip.stat().st_size
            pack["Crc"] = calculate_crc32(output_zip)
            
            print(f"BundlePackingInfo.json: 打包更新{output_zip.name}")
        
        for bundle in assets_path.rglob("*.bundle"):
            bundle.unlink()
        # Write updated BundlePackingInfo.json
        out_bundle = assets_path / "BundlePackingInfo.json"
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
    parser = argparse.ArgumentParser("Bundle patcher")
    parser.add_argument("url", help="Addressable catalog root url")
    args = parser.parse_args()
    apply_patch(args.url, "Android")
    apply_patch(args.url, "iOS")
