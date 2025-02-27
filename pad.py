import os
import zipfile

def pad_normal(file_path, target_size):
    """
    Pads a non-ZIP file with null bytes (\x00) to reach the target size.
    """
    current_size = os.path.getsize(file_path)
    if current_size >= target_size:
        print("File already meets or exceeds target size.")
        return
    
    with open(file_path, 'ab') as f:
        f.write(b'\x00' * (target_size - current_size))
    print(f"Padded {file_path} to {target_size} bytes.")

def pad_zip(zip_path, target_size):
    """
    Pads a ZIP file using the ZIP comment field without modifying actual contents.
    Works without opening the ZIP file to avoid issues with password-protected files.
    """
    current_size = os.path.getsize(zip_path)
    if current_size >= target_size:
        print("ZIP file already meets or exceeds target size.")
        return
    
    pad_size = target_size - current_size
    comment = b'A' * min(pad_size, 65535)
    
    with open(zip_path, 'r+b') as f:
        f.seek(-2, os.SEEK_END)
        f.write(len(comment).to_bytes(2, 'little'))
        f.write(comment)
    print(f"Padded ZIP comment in {zip_path} to reach target size.")

def pad_file(file_path, target_size):
    if not file_path.endswith(".zip"):
        pad_normal(file_path, target_size)
    #else:
        #pad_zip(file_path, target_size)