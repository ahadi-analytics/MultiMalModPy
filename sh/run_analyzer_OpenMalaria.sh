#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 04:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=20G
#SBATCH --job-name="analyze_OMsim"
#SBATCH --error=log/analyze_OMsim.%j.err
#SBATCH --output=log/analyze_OMsim.%j.out


ml singularity/3.8.1 
ml python/3.8.4 
source /projects/b1139/environments/emodpy_om/bin/activate

cd /home/mrm9534/model-characterization/OpenMalaria
python analyze_sim.py --dir "/projects/b1139/emod-om/experiments/mrm9534/sim_20240830/forcedEIR_CM0_eirsweep"