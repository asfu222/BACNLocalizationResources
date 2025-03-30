import json
from pathlib import Path
import binascii
import json
import subprocess
def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF
with open("./MediaCatalog.json", "r", encoding="utf8") as f:
    catalog_data = json.loads(f.read())
for asset_dir in Path('./assets').iterdir():
    media_dir = asset_dir / "latest" / "MediaResources"
    hasModded = False
    for i in range(1, 1000):
        voicepack_path = media_dir / "GameData" / "Audio" / "VOC_CN" / f"CN_Main_{i}.zip"
        if voicepack_path.is_file():
            catalog_data["MediaResources"][f"audio/voc_cn/cn_main_{i}/cn_main_{i}"] = {
                "path": f"GameData\\Audio\\VOC_CN\\CN_Main_{i}.zip",
                "file_name": f"CN_Main_{i}.zip",
                "bytes": voicepack_path.stat().st_size,
                "crc": calculate_crc32(voicepack_path),
                "is_prologue": True,
                "is_split_download": False,
                "media_type": 1
            }
            hasModded = True
        else:
            break
    if hasModded:
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