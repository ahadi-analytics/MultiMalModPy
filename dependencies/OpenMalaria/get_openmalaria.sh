#!/bin/bash
# -------------------------------
# Download and extract OpenMalaria
# -------------------------------

# Set version number (modify for newer releases)
VERSION=46

# URL for OpenMalaria ZIP
URL="https://github.com/SwissTPH/openmalaria/releases/download/schema-${VERSION}.0/openMalaria-windows.zip"

# Paths for download and extraction
DEST="$PWD/openMalaria-windows.zip"
OUT_DIR="$PWD/om_v$VERSION"
TMP_DIR="$PWD/temp_openMalaria"

# Create output and temporary directories
mkdir -p "$OUT_DIR"
mkdir -p "$TMP_DIR"

echo "Downloading OpenMalaria v$VERSION (modify script for newer versions)..."
curl -L "$URL" -o "$DEST"

echo "Extracting OpenMalaria to temporary folder..."
unzip -o "$DEST" -d "$TMP_DIR"

echo "Moving contents to $OUT_DIR..."
mv "$TMP_DIR"/openMalaria-windows/* "$OUT_DIR"/

# Remove temporary folder and downloaded ZIP
rm -rf "$TMP_DIR"
rm -f "$DEST"

echo
echo "OpenMalaria v$VERSION has been downloaded and extracted to:"
echo "$OUT_DIR"

