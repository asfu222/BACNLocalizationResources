if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python is not installed!" >&2
    exit 1
fi

echo "Using $PYTHON_CMD"

cd BlueArchiveLocalizationTools
$PYTHON_CMD -m pip install -r requirements.txt
find ../assets -type d -path '*/buildSrc/Excel' | while read -r d; do
  out=$(echo "$d" | sed 's|/buildSrc/Excel/*$|/Excel.zip|')
  echo ../Excel.zip "$d" "$out"
  $PYTHON_CMD build_excel_zip.py ../Excel.zip "$d" "$out"
done
cd ..
find . -type d -path "*/buildSrc/Excel" -exec rm -rf {} +

chmod +x ./crcmanip-cli
$PYTHON_CMD patch_table_catalog.py
$PYTHON_CMD patch_bundleDL.py

# Clean up
find . -type d -name "temp" -exec rm -rf {} +

$PYTHON_CMD generate_catalog.py

cp -p ba.env ./assets/ba.env