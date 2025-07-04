#!/bin/bash

# === Configuration (user and platform specific) ===
REPO_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
IMAGE_NAME="emod-with-om-46-R-4.4.1.sif"
IMAGE_DIR="${IMAGE_DIR:-/gpfs/projects/b1139/emod-om/container}"
IMAGE_PATH="${IMAGE_DIR}/${IMAGE_NAME}"
IMAGE_URI="${IMAGE_URI:-library://rungma/multimalmodpy/mmmpy_hpc:rocky8}"
DEFAULT_MODELS="EMOD malariasimulation OpenMalaria"

# === Prompt user for models ===
read -rp "Enter the models to run [default: $DEFAULT_MODELS]: " MODELS
MODELS="${MODELS:-$DEFAULT_MODELS}"

# === Load singularity module ===
echo "Loading Singularity module..."
module load singularity


# === Check if image exists, if not pull it ===
if [ ! -f "$IMAGE_PATH" ]; then
  echo "Singularity image not found at $IMAGE_PATH"
  echo "Pulling image from $IMAGE_URI ..."
  singularity pull --arch amd64 "$IMAGE_PATH" "$IMAGE_URI"
  if [ $? -ne 0 ]; then
    echo "Failed to pull Singularity image."
    exit 1
  fi
else
  echo "Singularity image found at $IMAGE_PATH"
fi


# === Change directory to the repo ===
echo "Changing directory to repository: $REPO_PATH"
cd "$REPO_PATH" || { echo "Repository path not found! Exiting."; exit 1; }

# === Run simulation inside singularity ===
echo "Submitting simulation inside Singularity container..."
singularity exec \
  -B /etc/slurm \
  -B "$(which sbatch)" \
  -B "$(which srun)" \
  -B "$(which sacct)" \
  -B "$(which scontrol)" \
  -B "$(which salloc)" \
  -B "$(which scancel)" \
  -B "$(which squeue)" \
  -B /usr/lib64/slurm/ \
  -B /usr/lib64/libmunge.so.2 \
  -B /usr/lib64/libmunge.so.2.0.0 \
  -B /usr/lib64/libpmi2.so \
  -B /usr/lib64/libpmi2.so.0 \
  -B /usr/lib64/libpmi2.so.0.0.0 \
  -B /usr/lib64/libpmi.so \
  -B /usr/lib64/libpmi.so.0 \
  -B /usr/lib64/libpmi.so.0.0.0 \
  -B /run \
  -B /usr/lib64/libnvidia-ml.so.1 \
  -B /projects \
  -B /scratch \
  --writable-tmpfs \
  "$IMAGE_PATH" \
  /opt/envs/emodpy39/bin/python3 launch_sim.py --models $MODELS  --test

echo "Simulation submission completed."


