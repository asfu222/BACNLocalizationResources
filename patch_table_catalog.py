import binascii
import os
import struct
from io import BytesIO
from typing import Any, List
import json
import requests
from pathlib import Path


def patch_file(file_path, db_path) -> None:
    done_patching = False
    bytes_data = None
    with open(file_path, 'rb') as f_read:
        bytes_data = bytearray(f_read.read())
    cursor = BytesIO(initial_bytes=bytes_data)

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
        if key == 'ExcelDB.db':
            modify_exceldb()
            return
        _ = read_i8()  # Skip 1 byte
        _ = read_i32()  # Skip 4 bytes
        name: str = read_string()
        size = read_i64()
        crc = read_i64()
        is_in_build = read_bool()
        is_changed = read_bool()
        is_prologue = read_bool()
        is_split_download = read_bool()
        includes: List[str] = read_includes()

    def modify_exceldb() -> None:
        _ = read_i8()  # Skip 1 byte
        _ = read_i32()  # Skip 4 bytes
        name: str = read_string()
        size_pos = cursor.tell()
        size = read_i64()
        crc_pos = cursor.tell()
        crc = read_i64()
        struct.pack_into("q", bytes_data, size_pos, os.path.getsize(os.path.join(db_path, 'ExcelDB.db')))
        struct.pack_into('q', bytes_data, crc_pos, calculate_crc32(os.path.join(db_path, 'ExcelDB.db')))
        print(f"TableCatalog.bytes: 修改ExcelDB.db 文件大小值 {size} -> {os.path.getsize(os.path.join(db_path, 'ExcelDB.db'))}")
        print(f"TableCatalog.bytes: 修改ExcelDB.db crc值 {crc} -> {calculate_crc32(os.path.join(db_path, 'ExcelDB.db'))}")
        repack_data()

    def repack_data() -> None:
        nonlocal done_patching
        with open(os.path.join(db_path, 'TableCatalog.bytes'), 'wb') as f_write:
            f_write.write(bytes_data)
            done_patching = True
            print('已生成对应ExcelDB.db的TableCatalog.bytes')

    _ = read_i8()  # Skip 1 byte
    data_size = read_i32()

    for _ in range(data_size):
        read_table()
        if done_patching:
            return

def calculate_crc32(file_path) -> int:
    with open(file_path, 'rb') as f:
        return binascii.crc32(f.read()) & 0xFFFFFFFF

for parent in [file.parent for file in Path('./assets').rglob("ExcelDB.db")]:
    patch_file('./TableCatalog.bytes', parent)