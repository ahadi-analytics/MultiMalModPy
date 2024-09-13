#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 10:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=3G
#SBATCH --job-name="run_malariasimulation"
#SBATCH --array=1-720%150
#SBATCH --error=log/run_malariasimulation_%A_%a.err
#SBATCH --output=log/run_malariasimulation_%A_%a.out

cd /home/mrm9534/model-characterization/malariasimulation/
Rscript /home/mrm9534/model-characterization/malariasimulation/malariasimulation_base.R /home/mrm9534/model-characterization/malariasimulation/R_functions/ /projects/b1139/emod-om/experiments/mrm9534/sim_20240830/forcedEIR_CM0_eirsweep ${SLURM_ARRAY_TASK_ID}