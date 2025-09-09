import json
from pathlib import Path
import binascii
import json
import subprocess
def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF
with open("./TableCatalog.json", "r", encoding="utf8") as f:
    catalog_data = json.loads(f.read())

channel_dirs = (
    channel_dir
    for asset_dir in Path("./assets").iterdir() if asset_dir.is_dir()
    for channel_dir in asset_dir.iterdir() if channel_dir.is_dir()
    if (channel_dir / "TableBundles" / "ExcelDB.db").exists()
)

for channel_dir in channel_dirs:
    files_path = channel_dir / "TableBundles"
    
    files_to_patch = {f.name: f for f in files_path.iterdir() if f.is_file()}
    
    hasModded = False
    
    for key, item in catalog_data["Table"].items(): # TablePack unsupported for now
        if key in files_to_patch:
            size = item["size"]
            crc = item["crc"]
            patched_file = files_path / key
            patched_file_size = patched_file.stat().st_size
            patched_file_crc = calculate_crc32(patched_file)
            item["size"] = patched_file_size
            item["crc"] = patched_file_crc
            hasModded = True
            print(f"TableCatalog.bytes: 修改{key} 文件大小值 {size} -> {patched_file_size}")
            print(f"TableCatalog.bytes: 修改{key} crc值 {crc} -> {patched_file_crc}")
            # Could also do the crc bypass method from before, but not implemented here because it is unnecessary

    if hasModded:
        catalog_json_path = files_path / "TableCatalog.json"
        with open(catalog_json_path, "wb") as f:
            f.write(json.dumps(catalog_data).encode())
        subprocess.run([
            "./MemoryPackRepacker", "serialize", "table",
            str(catalog_json_path), str(files_path / "TableCatalog.bytes")
        ])
        if catalog_json_path.exists():
            catalog_json_path.unlink()
