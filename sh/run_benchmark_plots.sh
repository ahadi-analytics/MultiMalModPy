#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 05:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=20G
#SBATCH --job-name="benchmark_plots"
#SBATCH --error=log/benchmark_plots.%j.err
#SBATCH --output=log/benchmark_plots.%j.out


ml singularity/3.8.1 
ml python/3.8.4 
source /projects/b1139/environments/emodpy_om/bin/activate

cd /home/mrm9534/model-characterization
python plot_benchmark.py -d /projects/b1139/emod-om/simulation_outputs/mrm9534/sim_20240830/forcedEIR_CM0_eirsweep --modelname EMOD MalSim OpenMalaria