#!/bin/bash

# Get the directory where the script is running (dependencies folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get project root one level up
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Project root detected as: $PROJECT_ROOT"
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

# Install requirements from dependencies folder
pip install -r "$REQ_FILE"

echo
echo "Installation of virtual python environment complete."
