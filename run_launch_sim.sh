#!/bin/bash
#SBATCH -A b1139
#SBATCH -p b1139
#SBATCH -t 0:30:00
#SBATCH -N 1
#SBATCH --ntasks-per-node=1
#SBATCH --mem-per-cpu=3G
#SBATCH --job-name="run_MMMPy"
#SBATCH --error=log/run_MMMPy_%A_%a.err
#SBATCH --output=log/run_MMMPy_%A_%a.out

cd /home/rer4177/MultiMalModPy
python launch_sim.py --models EMOD malariasimulation OpenMalaria --emodstep burnin --csv example1 --rownum 0
python launch_sim.py --models EMOD malariasimulation OpenMalaria --emodstep burnin --csv example1 --rownum 1
