#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 01:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=1G
#SBATCH --job-name="run_test"
#SBATCH --error=log/run_test_%j.err
#SBATCH --output=log/run_test_%j.out


ml singularity/3.8.1 
ml python/3.8.4
source /projects/b1139/environments/emodpy_om/bin/activate

# EMOD burnin and pickup in one
python launch_sim.py  --models EMOD MalSim OpenMalaria -r test

### EMOD burnin separate from pickup
#python launch_sim.py --emodstep burnin --models EMOD MalSim OpenMalaria

#python launch_sim.py --emodstep burnin --models EMOD MalSim OpenMalaria  --interventions cc_step


### from csv
python launch_sim.py  --models EMOD MalSim OpenMalaria  --rownum 0 --csv baseline_eirsweep_noCM