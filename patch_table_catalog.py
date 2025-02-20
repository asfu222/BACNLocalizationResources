import binascii
import os
import struct
from io import BytesIO
from typing import Any, List
import json
import requests
from pathlib import Path
import subprocess

def patch_files(original_catalog_path, files_path, bypass_path = None) -> None:
    done_patching = False
    bytes_data = None
    files_to_patch = [f for f in os.listdir(files_path) if os.path.isfile(os.path.join(files_path, f))]
    with open(original_catalog_path, 'rb') as f_read:
        bytes_data = bytearray(f_read.read())
    cursor = BytesIO(initial_bytes=bytes_data)
    if bypass_path is not None and os.path.exists(bypass_path):
        bypass_path = None

    def read_i8() -> Any:
        return struct.unpack('b', cursor.read(1))[0]

    def read_i32() -> Any:
        return struct.unpack('i', cursor.read(4))[0]

    def read_i64() -> Any:
        return struct.unpack('q', cursor.read(8))[0]

    def read_bool() -> Any:
        return struct.unpack('?', cursor.read(1))[0]

    def read_string() -> str:
        length = read_i32()
        return cursor.read(length).decode('utf-8', errors='replace')

    def read_includes() -> List[str]:
        size = read_i32()
        if size == -1:
            return []
        _ = read_i32()  # Skip 4 bytes
        includes: list = []

        for _ in range(size):
            includes.append(read_string())
            if _ != size - 1:
                _ = read_i32()  # Skip 4 bytes
        return includes

    def read_table() -> None:
        _ = read_i32()  # Skip 4 bytes
        key: str = read_string()
        _ = read_i8()  # Skip 1 byte
        _ = read_i32()  # Skip 4 bytes
        name: str = read_string()
        if key in files_to_patch:
            size_pos = cursor.tell()
            size = read_i64()
            crc_pos = cursor.tell()
            crc = read_i64()
            patched_file = os.path.join(files_path, key)
            patched_file_size = os.path.getsize(patched_file)
            struct.pack_into("q", bytes_data, size_pos, patched_file_size)
            struct.pack_into('q', bytes_data, crc_pos, calculate_crc32(patched_file))
            print(f"TableCatalog.bytes: 修改{key} 文件大小值 {size} -> {patched_file_size}")
            print(f"TableCatalog.bytes: 修改{key} crc值 {crc} -> {calculate_crc32(patched_file)}")
            if bypass_path is not None:
                if size == patched_file_size:
                    print(f"发现可直接过校验的文件({patched_file})，正在生成跟原CRC一样的资源")
                    bypass_path.mkdir(parents=True, exist_ok=True)
                    subprocess.run([
                        "./crcmanip-cli", "patch",
                        patched_file, os.path.join(bypass_path, key),
                        f'{crc:x}', "-a", "CRC32", "-o", "-p", "-4"
                    ], stdout=subprocess.DEVNULL)
                    print("生成完毕！")
                else:
                    print(f"{patched_file}: 不可生成直接过校验的资源（资源文件大小值必须跟日服原文件一致）。")
            files_to_patch.remove(key)
            if len(files_to_patch) == 0:
                repack_data()
                return
        else: 
            size = read_i64()
            crc = read_i64()
        is_in_build = read_bool()
        is_changed = read_bool()
        is_prologue = read_bool()
        is_split_download = read_bool()
        includes: List[str] = read_includes()

    def repack_data() -> None:
        nonlocal done_patching
        with open(os.path.join(files_path, 'TableCatalog.bytes'), 'wb') as f_write:
            f_write.write(bytes_data)
            done_patching = True
            print('已生成对应的TableCatalog.bytes')

    _ = read_i8()  # Skip 1 byte
    data_size = read_i32()

    for _ in range(data_size):
        read_table()
        if done_patching:
            return

def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF

for asset_dir in Path('./assets').iterdir():
    latest_dir = asset_dir / "latest"
    db_path = latest_dir / "TableBundles" / "ExcelDB.db"

    if db_path.exists():
        original_parent = db_path.parent
        bypass_path = asset_dir / "latest_crcbypass" / "TableBundles"

        patch_files('./TableCatalog.bytes', original_parent, bypass_path)
