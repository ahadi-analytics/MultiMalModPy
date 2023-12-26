#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 01:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem=8G
#SBATCH --job-name="run_submit_exp"
#SBATCH --error=log/submit_exp_%j.err
#SBATCH --output=log/submit_exp_%j.out


ml singularity/3.8.1 
ml python/3.8.4
source /projects/b1139/environments/emodpy_om/bin/activate

cd /home/mrm9534/model-characterization
python launch_test_emodstep.py --emodstep burnin --models EMOD MalSim OpenMalaria 



#cd /home/mrm9534/model-characterization
#python simulations/launch_baseline.py 