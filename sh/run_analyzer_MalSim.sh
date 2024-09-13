#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 01:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=20G
#SBATCH --job-name="analyze_malariasimulation"
#SBATCH --error=log/analyze_malariasimulation.%j.err
#SBATCH --output=log/analyze_malariasimulation.%j.out

cd /home/mrm9534/model-characterization/MalSim
python analyze_sim.py --job_dir "/projects/b1139/emod-om/experiments/mrm9534/sim_20240830/forcedEIR_CM0_eirsweep"