# Run simulations



## Quick launch
- Options to launch as simulation experimenr
  - via python script
  - via shell script (check which submission lines are uncommented)
    - `run_launch_simulations.sh`
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



## Run modes

### Normal run

### Test run

### Production run

### Calibration run 


## Customize_



## EMOD serialization

One functional difference between EMOD and other malaria models is the process of serialization (to run multiple
simulations on the same population in series).

- Serialization allows the user to run a simulation, save their status and results at a specified point in time, and
  start another simulation (i.e. with modified campaigns) that continues from the point saved.
- In EMOD, this is often applied to first run the  `burnin` the long initial simulation run, during which population
  immunity is established, followed by the `pickup` which defines the often typical scenario explorations.
- Hence, to avoid running the long initial period everytime, the user can serialize the population at the end of the
  burnin and then run shorter simulations on that population with varying campaign parameters (that do not affect
  population characteristics).

The following parameters need editing in the `launch_sim.py` or in the arguments passed on as defined
in `helper.py/launch_parse_args`:

- To run a burnin simulation :
    - Set `emod_step = ‘burnin’` .
    - Set `burnin = <num of years>` to define duration of the burnin period (which is also used in OpenMalaria, however
      runs much quicker than in EMOD).
    - The experiment ID for this burnin simulation will be needed when running the pickup simulation (and is saved
      automatically in <exp_name> folder, and also printed to console).
  
- To run a pickup simulation(s):
    - In latest version of the framework, submitting a burnin simulation will automatically create and run a
      corresponding pickup simulation via  `launch_pickup.sh`
    - In the files, `emod_step` is set to `pickup` and `emod_serialized_id` automatically to `<burnin experiment id>`
    - Note, pickup simulations cannot run without an attached experiment id (for EMOD).
    - The `launch_pickup.sh` includes the following lines after the required SBATCH specifications:
      -  ```
         ml singularity/3.8.1 
         ml python/3.8.4
         source /projects/b1139/environments/emodpy_om/bin/activate
    
         cd /projects/b1139/emod-om/model-characterization
         python launch_sim.py -d <job_directory>/<exp_name>_burnin80 --suite <SUITE_Name> --expname <exp_name> --emodstep pickup --serializedid <emod_serialized_id> --models EMOD MalSim OpenMalaria
         
         #or
         python launch_simulations.py -d <job_directory>/<exp_name>_burnin80 --suite <SUITE_Name> --expname <exp_name> --emodstep pickup --serializedid <emod_serialized_id> --models EMOD MalSim OpenMalaria
         ```

- To run a customized (new) pickup simulation(s):
    - Use the generated `launch_pickup.sh` as a template:
    - Modify the `expname` to specify a new folder to store the simulation files and change `emodstep` to `new_pickup`
    - Edit the `launch_sim.py` as required, or alternatively use `launch_simulations.py` with the corresponding csv
      -  Use launch_sim.py 
         ```
         python launch_sim.py -d <job_directory>/<exp_name>_burnin80 --suite <SUITE_Name> --expname <exp_name_new> --emodstep new_pickup --serializedid <emod_serialized_id> --models EMOD MalSim OpenMalaria
         ```
      - or launch_sim.py  with specified csv
         ```
         python launch_sim.py -d <job_directory>/<exp_name>_burnin80 --suite <SUITE_Name> --expname <exp_name_new> --emodstep new_pickup --serializedid <emod_serialized_id> --models EMOD MalSim OpenMalaria --csv baseline_eirsweep_noCM --rownum 0 
         ```
    - In the current version of the framework the new simulation experiments has to remain within the same directory (Suite) as the simulation experiment 'picked up from'.

- To run a burnin and pickup simulation (without serializing, as selected as default for testing):
    - Set `emod_step = None`, or if running from terminal, do not specify emod_step, which will default to `None`





