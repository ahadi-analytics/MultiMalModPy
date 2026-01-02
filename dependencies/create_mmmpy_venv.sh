#!/bin/bash

# Get the directory where the script is running (dependencies folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get project root one level up
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root detected as: $PROJECT_ROOT"

# Path to requirements file
REQ_FILE="$SCRIPT_DIR/requirements.txt"
echo "Using requirements file: $REQ_FILE"

# Prompt user for venv folder name, default is 'venv'
read -p "Enter name for the virtual environment folder (default: venv): " VENV_NAME
VENV_NAME=${VENV_NAME:-venv}

echo "Creating virtual environment named: $VENV_NAME"

# Create virtual environment inside project root
python3 -m venv "$PROJECT_ROOT/$VENV_NAME"

# Activate virtual environment
source "$PROJECT_ROOT/$VENV_NAME/bin/activate"

# Upgrade pip
python -m pip install --upgrade pip

# Install packages one by one and continue on errors
while IFS= read -r pkg || [[ -n "$pkg" ]]; do
    # Skip empty lines or comments
    [[ -z "$pkg" || "$pkg" =~ ^# ]] && continue

    echo "Installing package: $pkg"
    python -m pip install "$pkg" --extra-index-url=https://packages.idmod.org/api/pypi/pypi-production/simple || \
        echo "Failed to install: $pkg"
done < "$REQ_FILE"

echo
echo "NOTE: Some packages may fail to install if your Python version is incompatible or unavailable."
echo "Please check the logs above for any failures."
echo "Installation of virtual python environment complete."
