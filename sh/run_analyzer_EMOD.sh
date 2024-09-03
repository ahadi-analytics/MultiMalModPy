#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 04:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=100G
#SBATCH --job-name="analyze_EMODsim"
#SBATCH --error=log/analyze_EMODsim.%j.err
#SBATCH --output=log/analyze_EMODsim.%j.out


ml singularity/3.8.1 
ml python/3.8.4 
source /projects/b1139/environments/emodpy_om/bin/activate

cd /home/mrm9534/model-characterization/EMOD
python analyze_sim.py -d /projects/b1139/emod-om/experiments/mrm9534/sim_20240830/forcedEIR_CM0_eirsweep -i dc0eea7f-ba81-4f61-94f6-0a8e57ae1909