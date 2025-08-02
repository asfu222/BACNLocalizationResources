import sys
from pathlib import Path
from collections import defaultdict

CHUNK_SIZE = 25 * 1024 * 1024  # 25 MB


def split_file(filepath: Path):
    if not filepath.is_file():
        print(f"File {filepath} does not exist or is not a file.")
        return

    filesize = filepath.stat().st_size
    if filesize <= CHUNK_SIZE:
        #print(f"Skipping {filepath} (size {filesize} bytes ≤ 25MB)")
        return

    with filepath.open('rb') as f:
        part_num = 0
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            part_filename = filepath.with_name(f"{filepath.name}.part{part_num:03d}")
            with part_filename.open('wb') as chunk_file:
                chunk_file.write(chunk)
            print(f"Created split: {part_filename}")
            part_num += 1

    # print(f"Splitting complete for {filepath}. Total parts: {part_num}")

    # Delete original file after splitting
    try:
        filepath.unlink()
        # print(f"Deleted original file: {filepath}")
    except Exception as e:
        print(f"Failed to delete original file {filepath}: {e}")


def split_recursive(directory: str):
    path_obj = Path(directory)
    if not path_obj.is_dir():
        print(f"{directory} is not a valid directory.")
        return

    #print(f"Scanning directory recursively for files > 25MB in {directory}...")
    for file_path in path_obj.rglob('*'):
        if file_path.is_file():
            split_file(file_path)


def join_files_recursive(directory: str):
    path_obj = Path(directory)
    if not path_obj.is_dir():
        print(f"{directory} is not a valid directory.")
        return

    # Find all part files matching *.partNNN pattern
    parts_dict = defaultdict(list)  # base filename -> list of part files

    for part_file in path_obj.rglob('*.part[0-9][0-9][0-9]'):
        # Extract base filename by stripping .partNNN suffix
        base_name = part_file.name.rsplit('.part', 1)[0]
        base_path = part_file.parent / base_name
        parts_dict[base_path].append(part_file)

    if not parts_dict:
        print(f"No split part files found in directory {directory}")
        return

    for base_path, part_files in parts_dict.items():
        # Sort part files by their part number
        part_files.sort(key=lambda p: int(p.name.rsplit('.part', 1)[1]))
        output_file = base_path  # Restore original filename without .partNNN

        print(f"Reconstructing {output_file} from {len(part_files)} parts...")
        with output_file.open('wb') as outfile:
            for part_file in part_files:
                with part_file.open('rb') as pf:
                    while True:
                        data = pf.read(1024 * 1024)
                        if not data:
                            break
                        outfile.write(data)
                #print(f"Appended {part_file}")

        print(f"Reconstruction complete: {output_file}")

        # Delete part files after successful reconstruction
        for part_file in part_files:
            try:
                part_file.unlink()
                print(f"Deleted part file: {part_file}")
            except Exception as e:
                print(f"Failed to delete part file {part_file}: {e}")


def print_usage():
    print("Usage:")
    print("  python split_join.py split [directory]     # recursively split large files in directory (default: current dir)")
    print("  python split_join.py join [directory]      # recursively join split parts in directory (default: current dir)")


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print_usage()
        sys.exit(1)

    mode = sys.argv[1].lower()

    if mode == 'split':
        directory = sys.argv[2] if len(sys.argv) == 3 else '.'
        split_recursive(directory)
    elif mode == 'join':
        directory = sys.argv[2] if len(sys.argv) == 3 else '.'
        join_files_recursive(directory)
    else:
        print("Invalid mode. Use 'split' or 'join'.")
        print_usage()
        sys.exit(1)
