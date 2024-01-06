#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 01:00:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=1G
#SBATCH --job-name="run_baseline_eirsweep"
#SBATCH --error=log/run_baseline_eirsweep_%j.err
#SBATCH --output=log/run_baseline_eirsweep_%j.out


ml singularity/3.8.1 
ml python/3.8.4
source /projects/b1139/environments/emodpy_om/bin/activate

### Test
python launch_simulations.py  --models EMOD MalSim OpenMalaria  --rownum 0 --csv baseline_eirsweep_noCM

### Examples
#python launch_simulations.py  --models EMOD MalSim OpenMalaria  --rownum 1 --csv baseline_eirsweep_noCM --user b1139
#python launch_simulations.py  --models EMOD MalSim OpenMalaria  --rownum 2 --csv baseline_eirsweep_noCM --user b1139
#python launch_simulations.py  --models EMOD MalSim OpenMalaria  --rownum 3 --csv baseline_eirsweep_noCM --user b1139
#python launch_simulations.py  --models EMOD MalSim OpenMalaria  --rownum 4 --csv baseline_eirsweep_noCM --user b1139

### EMOD burnin separate from pickup
#python launch_simulations.py  --emodstep burnin  --models EMOD MalSim OpenMalaria  --rownum 1 --csv baseline_eirsweep_noCM --user b1139