# Run simulations



## Pre-defined simulation options  

Coming soon...

## Change input parameters

## Launch simulations

- In terminal navigate to repository  `cd ~/model-characterization`
- Run python script that defines the simulation i.e. `python launch_sim.py` for a test run using defaults specified in
  the script and `parse_launch_args` (see helper.py)
- Check simulations via `squeue -u <username>` (if on slurm)
- Wait for simulations to finish after which analyzer scripts and default plots will automatically start running


 **Submission examples**
- Options to launch as simulation experimenr
  - via python script
  - via shell script (check which submission lines are uncommented)
    - `run_launch_simulations.sh`
  - via terminal 

Testrun 
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria --test`

Baseline run (accepting defaults, or changed defaults in python file) 
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria`
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria  --rownum 0 --csv baseline_eirsweep_noCM`  

Custom simulation experiments (i.e. cc_step)
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria --intervention cc_step --test --emodstep burnin`
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria  --rownum 0 --csv cc_step_test`  






