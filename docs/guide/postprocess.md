
# Submit run and analyze simulations

- In terminal navigate to repository  `cd ~/model-characterization`
- Run python script that defines the simulation i.e. `python launch_sim.py` for a test run using defaults specified in
  the script and `parse_launch_args` (see helper.py)
    - Other options defined in the [run_launch_sim.sh](https://github.com/numalariamodeling/model-characterization/blob/main/run_launch_sim.sh)
    - `python launch_sim.py --emodstep burnin --models EMOD MalSim OpenMalaria`
    - `python launch_sim.py --models EMOD MalSim OpenMalaria --rownum 0 --csv baseline_eirsweep_noCM`
- Check simulations via `squeue -u <username>`
- Wait for simulations to finish after which analyzer scripts and default plots will automatically start running
- If you need to resubmit the `analyze_sim.py` script, it can be found in `experiments/<suite>/<exp_name>`
     ```
      cd /home/b1139/model-characterization/EMOD  
      python analyze_sim.py -d /projects/b1139/emod-om/experiments/forcedEIR/baseline_noCM_EIRseason -i
      fb508aba-2aa7-43b3-b365-ea7c227d7781
     ``` 
- Perform additional analysis or plot custom results