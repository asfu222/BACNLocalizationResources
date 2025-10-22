from pathlib import Path
import xxhash
from zlib import crc32
import json
import ctypes
import os
import sys

def is_hidden(filepath: Path):
    """Check if a file is hidden across Windows, macOS, and Linux."""
    if sys.platform == "win32":
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(filepath))
        return attrs != -1 and (attrs & 2)  # FILE_ATTRIBUTE_HIDDEN (0x2)
    else:
        return filepath.name.startswith('.')

ALLOWED_PATHS = [Path("assets/beicheng"), Path("assets/commonpng"), Path("assets/scenariovoice")]
OUTPUT_FILE = Path("assets/catalog.html")
STATIC_NAMES = ["BundlePackingInfo.bytes", "BundlePackingInfo.json", "TableCatalog.bytes", "MediaCatalog.bytes", "catalog_Android.zip", "catalog_iOS.zip"]

def calculate_hash64(name: str | bytes) -> int:
    if isinstance(name, str):
        name = name.encode("utf8")
    return xxhash.xxh64(name).intdigest()

def calculate_crc(path: Path) -> int:
    with path.open("rb") as f:
        return crc32(f.read()) & 0xFFFFFFFF

def generate_file_list():
    file_data = []
    for base_path in ALLOWED_PATHS:
        if not base_path.exists():
            continue
        for file_path in sorted(base_path.rglob("*")):
            if file_path.is_file() and not is_hidden(file_path):
                original_name = file_path.name
                hash64 = calculate_hash64(original_name.lower())
                crc = calculate_crc(file_path)
                new_name = f"{hash64}_{crc}" if original_name not in STATIC_NAMES and not original_name.endswith(".bundle") else original_name
                rel_path = file_path.relative_to("assets").as_posix()
                file_data.append({
                    "original": rel_path,
                    "renamed": new_name,
                    "size": file_path.stat().st_size,
                    "extension": file_path.suffix
                })
    return file_data
def generate_catalog_jsons():
    for base_path in ALLOWED_PATHS:
        if not base_path.exists():
            continue
        for subdir in base_path.iterdir():
            file_list = [str(file.relative_to(subdir)).replace("\\", "/") for file in subdir.rglob("*") if file.is_file()]
            if len(file_list) > 0:
                catalog_path = subdir / "catalog.json"
                if catalog_path.exists():
                    continue
                with open(catalog_path, "wb") as c_json:
                    c_json.write(json.dumps(file_list, separators=(',', ':')).encode())
        
def build_directory_tree(file_data):
    root = {"name": "", "children": {}, "files": [], "all_files": set()}
    for index, file in enumerate(file_data):
        parts = file['original'].split('/')
        current = root
        for part in parts[:-1]:
            if part not in current["children"]:
                current["children"][part] = {"name": part, "children": {}, "files": [], "all_files": set()}
            current = current["children"][part]
        current["files"].append({"name": parts[-1], "index": index})
        current["all_files"].add(index)
    def propagate_files(node):
        for child in node["children"].values():
            propagate_files(child)
            node["all_files"].update(child["all_files"])
    propagate_files(root)
    return root

def generate_html(file_data):
    directory_tree = build_directory_tree(file_data)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>蔚蓝档案日服汉化文件资源库</title>
    <style>
        body {{ 
            font-family: Arial, sans-serif; 
            margin: 20px; 
            padding-top: 120px; 
            background-color: #f8f9fa;
        }}
        h1 {{ 
            text-align: center; 
            position: fixed; 
            top: 0; 
            left: 0; 
            right: 0; 
            background: white; 
            padding: 15px;
            margin: 0;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .controls {{
            position: fixed;
            top: 60px;
            left: 20px;
            right: 20px;
            background: white;
            z-index: 1000;
            padding: 15px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        .tree {{ 
            margin-left: 20px; 
            margin-top: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .dir-item {{ 
            margin: 5px 0;
            padding: 5px;
            border-left: 2px solid #dee2e6;
        }}
        .dir-header {{ 
            cursor: pointer; 
            padding: 8px;
            display: flex; 
            align-items: center; 
            transition: background-color 0.2s;
        }}
        .dir-header:hover {{ 
            background-color: #f8f9fa;
        }}
        .toggle {{ 
            display: inline-block; 
            width: 20px; 
            font-size: 0.9em;
            color: #6c757d;
        }}
        .checkbox {{ 
            margin: 0 10px 0 5px;
            accent-color: #0d6efd;
        }}
        .file-item {{ 
            display: flex; 
            align-items: center; 
            margin-left: 25px; 
            padding: 8px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }}
        .file-item:hover {{
            background-color: #f8f9fa;
        }}
        .progress-container {{
            flex: 1;
            max-width: 200px;
            height: 20px;
            background-color: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 0 15px;
            display: none;
        }}
        .file-progress-bar {{
            width: 0%;
            height: 100%;
            background-color: #0d6efd;
            transition: width 0.3s ease;
        }}
        .status-text {{
            min-width: 120px;
            text-align: right;
            color: #6c757d;
            font-size: 0.9em;
            display: none;
        }}
        .file-item.downloading .progress-container,
        .file-item.downloading .status-text {{
            display: block;
        }}
        .file-item.completed .status-text,
        .file-item.failed .status-text {{
            display: inline-block;
        }}
        .file-item.completed .progress-container,
        .file-item.failed .progress-container {{
            display: none;
        }}
        #bulk-progress {{
            height: 8px;
            background-color: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }}
        #total-progress {{
            width: 0%;
            height: 100%;
            background-color: #0d6efd;
            transition: width 0.3s ease;
        }}
        button {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background-color: #0d6efd;
            color: white;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        button:hover {{
            opacity: 0.9;
        }}
        button:disabled {{
            background-color: #6c757d;
            cursor: not-allowed;
        }}
        .icons {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            display: flex;
            gap: 10px;
        }}
        .icon {{
            width: 40px;
            height: 40px;
            transition: 0.3s;
        }}
        .icon:hover {{
            opacity: 0.7;
        }}
        
        /* 移动端适配 */
        .controls > div {{
            flex: 1;
            min-width: 0;
            overflow: hidden;
            text-align: right;
        }}
        @media (max-width: 1024px) {{
            :root {{
                --header-height: 55px;
                --controls-height: 100px;
            }}
            body {{ 
                padding-top: calc(var(--header-height) + var(--controls-height) + 30px);
                margin: 8px;
                font-size: 14px;
            }}
            h1 {{
                height: var(--header-height);
                padding: 8px 12px;
                font-size: 1rem;
                line-height: 1.2;
            }}
            .controls {{
                font-size: 0.85rem;
                display: flex;
                flex-wrap: nowrap;
                align-items: center;
            }}
            .controls > div {{
                flex: 1;
                min-width: 0;
                overflow: hidden;
                text-align: right;
            }}
            @media (min-width: 768px) and (max-width: 1024px) {{
                h1 {{
                    font-size: 1.1rem;
                }}
            }}
        @media (max-width: 767px) {{
            :root {{
                --header-height: 50px;
                --controls-height: 90px;
            }}
            body {{
                font-size: 12px;
                padding-top: calc(var(--header-height) + var(--controls-height) + 30px);
            }}
            h1 {{
                font-size: 0.85rem;
                padding: 6px 10px;
            }}
            .controls {{
                font-size: 0.75rem;
                flex-wrap: wrap;
                justify-content: center;
                gap: 3px;
                padding: 5px;
            }}
            .controls > div {{
                flex: 1 1 100%;
                text-align: center;
                margin-top: 3px;
            }}
            #progress-text {{
                font-size: 0.7rem;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                text-align: center;
                margin-top: 20px;
                padding: 0 10px;
                visibility: visible;
                display: inline-block;
                width: 100%;
            }}
            button {{
                flex: 1 1 auto;
                min-width: 55px;
                font-size: 0.7rem !important;
                padding: 5px 7px !important;
            }}
            label {{
                line-height: 1.2;
            }}
            .downloads {{
                position: relative;
                z-index: 10;
                margin-top: 5px;
                width: 100%;
                text-align: center;
            }}
        }}

        }}



    </style>
</head>
<body>
    <h1>蔚蓝档案日服汉化资源库</h1>
    <div class="controls">
        <div style="display: flex; gap: 10px; align-items: center;">
            <label style="display: flex; align-items: center; gap: 5px;">
                <input type="checkbox" id="renameToggle" checked>
                使用游戏可用命名（替换文件党请勾选）
            </label>
            <label style="display: flex; align-items: center; gap: 5px;">
                <input type="checkbox" id="compressToggle" checked>
                合并压缩成 artifacts.zip
            </label>
            <button onclick="startDownloads()" id="startBtn">开始下载</button>
            <button onclick="pauseDownloads()" id="pauseBtn">暂停下载</button>
            <button onclick="cancelDownloads()">取消下载</button>
            <div style="flex: 1; text-align: right;">
                <span id="progress-text" style="color: #6c757d;"></span>
            </div>
        </div>
        <div id="bulk-progress">
            <div id="total-progress"></div>
        </div>
    </div>
    <div class="tree">
"""
    def generate_tree_html(node, level=0):
        indent = level * 20
        html = ""
        for dir_name, child in sorted(node["children"].items()):
            html += f"""
            <div class="dir-item" style="margin-left: {indent}px">
                <div class="dir-header">
                    <input type="checkbox" class="checkbox dir-checkbox">
                    <span class="toggle" onclick="toggleDirectory(this)">▶&#xFE0E;</span>
                    <span>{dir_name}/</span>
                </div>
                <div class="dir-contents" style="display:none;">
                    {generate_tree_html(child, level + 1)}
                </div>
            </div>
            """
        for file in sorted(node["files"], key=lambda x: (x['name'] not in STATIC_NAMES, x['name'])):
            html += f"""
            <div class="file-item">
                <input type="checkbox" class="checkbox file-checkbox" data-index="{file['index']}">
                <span style="flex-grow:1">{file['name']}</span>
                <div class="progress-container">
                    <div class="file-progress-bar" id="file-progress-{file['index']}"></div>
                </div>
                <span class="status-text" id="file-status-{file['index']}"></span>
            </div>
            """
        return html
    html_content += generate_tree_html(directory_tree)
    html_content += f"""
    </div>
    <div class="icons">
        <a href="https://github.com/asfu222/BACNLocalizationResources" target="_blank">
            <img src="https://www.github.com/favicon.ico" class="icon" alt="GitHub">
        </a>
        <a href="https://space.bilibili.com/3546839682911153" target="_blank">
            <img src="https://www.bilibili.com/favicon.ico" class="icon" alt="Bilibili">
        </a>
    </div>
    <script type="module">
      (async () => {{
          const module = await import('https://cdn.jsdelivr.net/npm/client-zip/index.js');
          window.downloadZip = module.downloadZip;
      }})();
    </script>
    <script>
        const fileData = {json.dumps(file_data)};
        let downloadQueue = [];
        let activeXHRs = new Map();
        let isPaused = false;
        let totalFiles = 0;
        let completedFiles = 0;
        let totalSize = 0;
        let downloadedSize = 0;
        let downloadedFiles = [];
        const CONCURRENCY_LIMIT = 10;
        let currentIndex = 0;

        function toggleDirectory(toggle) {{
            const contents = toggle.parentElement.nextElementSibling;
            contents.style.display = contents.style.display === 'none' ? 'block' : 'none';
            toggle.innerHTML = contents.style.display === 'none' ? '▶&#xFE0E;' : '▼';
        }}

        function getSortedFileIndices(container) {{
            const indices = [];
            const walker = document.createTreeWalker(
                container,
                NodeFilter.SHOW_ELEMENT,
                {{ acceptNode: node => 
                    node.classList?.contains('file-checkbox') ? 
                    NodeFilter.FILTER_ACCEPT : 
                    NodeFilter.FILTER_SKIP 
                }}
            );
            while(walker.nextNode()) {{
                indices.push(parseInt(walker.currentNode.dataset.index));
            }}
            return indices;
        }}

        function resetProgress() {{
            activeXHRs.forEach(xhr => xhr.abort());
            activeXHRs.clear();
            downloadedSize = 0;
            completedFiles = 0;
            downloadedFiles = [];
            currentIndex = 0;
            document.querySelectorAll('.file-progress-bar').forEach(bar => bar.style.width = '0%');
            document.querySelectorAll('.status-text').forEach(span => span.textContent = '');
            document.getElementById('total-progress').style.width = '0%';
            updateProgress();
        }}

        function updateProgress() {{
            const totalMB = (totalSize / 1024 / 1024).toFixed(1);
            const downloadedMB = (downloadedSize / 1024 / 1024).toFixed(1);
            const progress = totalSize > 0 ? (downloadedSize / totalSize) * 100 : 0;
            document.getElementById('total-progress').style.width = `${{progress}}%`;
            document.getElementById('progress-text').textContent = 
                `${{completedFiles}}/${{totalFiles}} 文件 (${{downloadedMB}}MB/${{totalMB}}MB)`;
        }}

        function handleDirectorySelection(checkbox) {{
            const container = checkbox.closest('.dir-item').querySelector('.dir-contents');
            const indices = getSortedFileIndices(container);
            const isChecked = checkbox.checked;
            indices.forEach(index => {{
                const fileCheckbox = document.querySelector(`.file-checkbox[data-index="${{index}}"]`);
                if (fileCheckbox) {{
                    const wasChecked = fileCheckbox.checked;
                    fileCheckbox.checked = isChecked;
                    if (wasChecked !== isChecked) {{
                        const file = fileData[index];
                        if (isChecked) {{
                            if (!downloadQueue.includes(index)) downloadQueue.push(index);
                            totalSize += file.size;
                        }} else {{
                            downloadQueue = downloadQueue.filter(i => i !== index);
                            totalSize -= file.size;
                        }}
                    }}
                }}
            }});
            downloadQueue = Array.from(new Set([
                ...downloadQueue.filter(i => !indices.includes(i)),
                ...(isChecked ? indices : [])
            ]));
            totalFiles = downloadQueue.length;
            resetProgress();
            document.getElementById('startBtn').disabled = totalFiles === 0;
        }}

        document.addEventListener('change', (event) => {{
            if (event.target.classList.contains('dir-checkbox')) {{
                handleDirectorySelection(event.target);
            }}
            if (event.target.classList.contains('file-checkbox')) {{
                const index = parseInt(event.target.dataset.index);
                const file = fileData[index];
                const wasChecked = downloadQueue.includes(index);
                if (event.target.checked && !wasChecked) {{
                    downloadQueue.push(index);
                    totalSize += file.size;
                }} else if (!event.target.checked && wasChecked) {{
                    downloadQueue = downloadQueue.filter(i => i !== index);
                    totalSize -= file.size;
                }}
                totalFiles = downloadQueue.length;
                resetProgress();
                document.getElementById('startBtn').disabled = totalFiles === 0;
            }}
        }});

        async function processFile(index) {{
            return new Promise((resolve) => {{
                const xhr = new XMLHttpRequest();
                const file = fileData[index];
                const progressBar = document.getElementById(`file-progress-${{index}}`);
                const statusText = document.getElementById(`file-status-${{index}}`);
                const fileItem = document.querySelector(`.file-checkbox[data-index="${{index}}"]`).closest('.file-item');
                
                fileItem.classList.add('downloading');
                activeXHRs.set(index, xhr);

                const rootUrl = `${{window.location.origin}}${{window.location.pathname.split('/').slice(0, -1).join('/')}}/`;
                xhr.open('GET', `${{rootUrl}}${{file.original}}`);
                xhr.responseType = 'blob';

                xhr.onprogress = (event) => {{
                    if (event.lengthComputable) {{
                        const percent = (event.loaded / event.total) * 100;
                        progressBar.style.width = `${{percent}}%`;
                        downloadedSize += event.loaded - (xhr._lastLoaded || 0);
                        xhr._lastLoaded = event.loaded;
                        updateProgress();
                    }}
                }};

                xhr.onload = () => {{
                    fileItem.classList.remove('downloading');
                    if (xhr.status === 200) {{
                        const blob = new Blob([xhr.response], {{ type: 'application/octet-stream' }});
                        let filename;
                        if (document.getElementById('renameToggle').checked) {{
                            filename = file.renamed;
                        }} else {{
                            const originalName = file.original.split('/').pop();
                            filename = originalName.includes('.') 
                                ? originalName 
                                : `${{originalName}}${{file.extension}}`;
                        }}
                        if (document.getElementById('compressToggle').checked) {{
                            downloadedFiles.push({{filename: filename, blob: blob}});
                        }} else {{
                            const link = document.createElement('a');
                            link.href = URL.createObjectURL(blob);
                            link.download = filename;
                            link.click();
                        }}
                        statusText.textContent = '下载完毕';
                        fileItem.classList.add('completed');
                    }} else {{
                        statusText.textContent = '下载失败';
                        fileItem.classList.add('failed');
                    }}
                    completedFiles++;
                    activeXHRs.delete(index);
                    resolve();
                }};

                xhr.onerror = () => {{
                    fileItem.classList.remove('downloading');
                    statusText.textContent = '下载失败';
                    fileItem.classList.add('failed');
                    completedFiles++;
                    activeXHRs.delete(index);
                    resolve();
                }};

                xhr.send();
            }});
        }}

        async function startDownloads() {{
            isPaused = false;
            const queue = downloadQueue;
            currentIndex = 0;
            completedFiles = 0;
            downloadedSize = 0;
            
            const workers = Array(CONCURRENCY_LIMIT).fill().map(async () => {{
                while (currentIndex < queue.length && !isPaused) {{
                    const index = queue[currentIndex];
                    currentIndex++;
                    await processFile(index);
                }}
            }});
            
            await Promise.all(workers);
            
            if (!isPaused && completedFiles === totalFiles) {{
                if (document.getElementById('compressToggle').checked) {{
                    const files = downloadedFiles.map(file => ({{
                        name: file.filename,
                        input: file.blob
                    }}));
                    const blob = await window.downloadZip(files).blob();
                    const link = document.createElement("a");
                    link.href = URL.createObjectURL(blob);
                    link.download = "artifacts.zip";
                    link.click();
                }}
                resetProgress();
            }}
        }}

        function pauseDownloads() {{
            isPaused = true;
            activeXHRs.forEach(xhr => xhr.abort());
            activeXHRs.clear();
            document.getElementById('pauseBtn').textContent = '继续下载';
            document.getElementById('pauseBtn').onclick = resumeDownloads;
        }}

        function resumeDownloads() {{
            isPaused = false;
            document.getElementById('pauseBtn').textContent = '暂停下载';
            document.getElementById('pauseBtn').onclick = pauseDownloads;
            startDownloads();
        }}

        function cancelDownloads() {{
            isPaused = true;
            activeXHRs.forEach(xhr => xhr.abort());
            activeXHRs.clear();
            downloadQueue = [];
            totalFiles = 0;
            totalSize = 0;
            downloadedSize = 0;
            completedFiles = 0;
            currentIndex = 0;
            downloadedFiles = [];
            document.querySelectorAll('.file-progress-bar').forEach(bar => bar.style.width = '0%');
            document.querySelectorAll('.status-text').forEach(span => span.textContent = '');
            document.querySelectorAll('.file-item').forEach(item => {{
                item.classList.remove('downloading', 'completed', 'failed');
            }});
            document.getElementById('total-progress').style.width = '0%';
            updateProgress();
            document.querySelectorAll('.file-checkbox, .dir-checkbox').forEach(cb => cb.checked = false);
            document.getElementById('startBtn').disabled = true;
        }}
    </script>
</body>
</html>
"""
    return html_content

def main():
    file_data = generate_file_list()
    #html_content = generate_html(file_data)
    #OUTPUT_FILE.write_text(html_content, encoding="utf-8")
    #print(f"Generated {OUTPUT_FILE} with {len(file_data)} files.")
    generate_catalog_jsons()
    print("Generated catalog jsons")

if __name__ == "__main__":
    main()
