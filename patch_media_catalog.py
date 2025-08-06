import json
from pathlib import Path
import binascii
import json
import subprocess
PROLOGUE_ZIPS = [f"CN_Main_1100{i}" for i in range(9)]
def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF
with open("./MediaCatalog.json", "r", encoding="utf8") as f:
    catalog_data = json.loads(f.read())
for asset_dir in Path('./assets').iterdir():
    media_dir = asset_dir / "latest" / "MediaResources"
    voice_dir = media_dir / "GameData" / "Audio" / "VOC_CN"
    hasModded = False
    
    cache_path = voice_dir / "zips.json"
    if cache_path.exists():
        with open(cache_path, "r", encoding="utf8") as f:
            zip_cache = json.load(f)
    else:
        zip_cache = {}
    if cache_path.exists():
        for name, info in zip_cache.items():
            catalog_data["MediaResources"][f"audio/voc_cn/{name.lower()}/{name.lower()}"] = {
                "path": info["path"],
                "file_name": info["file_name"],
                    "bytes": info["bytes"],
                    "crc": info["crc"],
                    "is_prologue": name in PROLOGUE_ZIPS,
                    "is_split_download": False,
                    "media_type": 1
                }
            hasModded = True
    else:
        for voicepack_path in voice_dir.rglob("*.zip"):
            catalog_data["MediaResources"][f"audio/voc_cn/{voicepack_path.stem.lower()}/{voicepack_path.stem.lower()}"] = {
                "path": f"GameData\\Audio\\VOC_CN\\{voicepack_path.stem}.zip",
                "file_name": f"{voicepack_path.stem}.zip",
                    "bytes": voicepack_path.stat().st_size,
                    "crc": calculate_crc32(voicepack_path),
                    "is_prologue": voicepack_path.stem in PROLOGUE_ZIPS,
                    "is_split_download": False,
                    "media_type": 1
                }
            hasModded = True
            zip_cache[voicepack_path.stem] = {
                "path": f"GameData\\Audio\\VOC_CN\\{voicepack_path.stem}.zip",
                "file_name": f"{voicepack_path.stem}.zip",
                "bytes": voicepack_path.stat().st_size,
                "crc": calculate_crc32(voicepack_path)
            }
    if hasModded:
        if not cache_path.exists():
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(zip_cache, f, indent=4, ensure_ascii=False)
        catalog_path = media_dir / "Catalog"
        catalog_path.mkdir(parents=True, exist_ok=True)
        catalog_json_path = catalog_path / "MediaCatalog.json"
        with open(catalog_json_path, "wb") as f:
            f.write(json.dumps(catalog_data).encode())
        subprocess.run([
            "./MemoryPackRepacker", "serialize", "media",
            str(catalog_json_path), str(catalog_path / "MediaCatalog.bytes")
        ])
        if catalog_json_path.exists():
            catalog_json_path.unlink()
