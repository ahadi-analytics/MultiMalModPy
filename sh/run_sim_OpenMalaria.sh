#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 04:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=3G
#SBATCH --job-name="run_openmalaria"
#SBATCH --array=1-720%150
#SBATCH --error=log/run_openmalaria_%A_%a.err
#SBATCH --output=log/run_openmalaria_%A_%a.out


module use /projects/b1139/OpenMalaria/om_v46//modules/ 
module load openmalaria
export PATH=$PATH:/projects/b1139/emod-om/experiments/mrm9534/sim_20240830/forcedEIR_CM0_eirsweep
openMalaria -s xml/${SLURM_ARRAY_TASK_ID}.xml  --output txt/${SLURM_ARRAY_TASK_ID}.txt