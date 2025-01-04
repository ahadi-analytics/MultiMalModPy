
# Model specific configurations  

This page is under construction...   

## EMOD


EMOD allows serialization and to use an alternative base calibration.    


### Serialization

Serialization allows the user to run a simulation, save their status and results at a specified point in time, and
start another simulation (i.e. with modified campaigns) that continues from the point saved.  
In EMOD, this is often applied to first run the  `burnin` the long initial simulation run, during which population 
immunity is established, followed by the `pickup` which defines the often typical scenario explorations.  

The following parameters need editing when running `launch_sim.py`:  

- To run a burnin simulation :  
    - Set `emod_step = ‘burnin’` .  
    - The experiment ID for this burnin simulation will be needed when running the pickup simulation (and is saved
      automatically in <exp_name> folder, and also printed to console).  
  
- To run a pickup simulation(s):  
    - In latest version of the framework, submitting a burnin simulation will automatically create and run a  
      corresponding pickup simulation via  `launch_pickup.sh`  
    - In the files, `emod_step` is set to `pickup` and `emod_serialized_id` automatically to `<burnin experiment id>`
    - Note, pickup simulations cannot run without an attached experiment id (for EMOD).  
    - The `launch_pickup.sh` includes the following lines after the required SBATCH specifications:  
  
       ```
         ml singularity/3.8.1  
         ml python/3.8.4
         source /projects/b1139/environments/mmmpy_venv/bin/activate
    
         cd /projects/b1139/emod-om/model-characterization
         python launch_sim.py -d <job_directory>/<exp_name>_burnin80 --suite <SUITE_Name> --expname <exp_name> --emodstep pickup --serializedid <emod_serialized_id> --models EMOD MalSim OpenMalaria
         
       ```

- To run a customized (new) pickup simulation(s):  
    - Use the generated `launch_pickup.sh` as a template:
    - Modify the `expname` to specify a new folder to store the simulation files and change `emodstep` to `new_pickup`
    - Edit the `launch_sim.py` as required, or alternatively use `launch_simulations.py` with the corresponding csv
      -  Use launch_sim.py 
         ```
         python launch_sim.py -d <job_directory>/<exp_name>_burnin80 --suite <SUITE_Name> --expname <exp_name_new> --emodstep new_pickup --serializedid <emod_serialized_id> --models EMOD MalSim OpenMalaria
         ```

    - In the current version of the framework the new simulation experiments has to remain within the same directory (Suite) as the simulation experiment 'picked up from'.  

- To run a burnin and pickup simulation (without serializing, as selected as default for testing):  
    - Set `emod_step = None`, or if running from terminal, do not specify `emod_step`, which will default to `None`  
  

### Using alternative base calibration   


This section is under construction... 



## malariasimulation 


malariasimulation allows paramter sampling.  


### Parameter sampling    

In malariasimulation, accounting for parameter uncertainty to better reflect potential variability in the simulation results has been integrated by drawing parameter values
from posterior distributions around defined parameter sets.   

Via the set_parameter_draw function up to 1000 different parameter sets for 32 simulation parameters can be selected.
These 32 parameters correspond to: fixed state transitions, immunity boost grace periods, immunity decay rates, immunity reducing probability of detection, infectivity towards mosquitoes,
mortality, probability of clinical infection, probability of pre-erythrocytic infection, and probability of severe infection.

In `MultiMalModPy`, seed values are paired with the parameter_draw value.  

For a single seed, varying parameter sets from in total 1000 sets are drawn and a new draw is made each time new simulations run.
A breakdown of each parameter that is affected in the parameter draw, with parameter type, description, default value, 
maximum and minimum is shown in the core parameter table for malariasimulation.




<br>  

## OpenMalaria     

### Model variants  

OpenMalaria allows to take into account model and parameter uncertainty through varying  [model variants](https://github.com/SwissTPH/openmalaria/wiki/ModelWithinHost#specification-of-model-variants)). 
However, for simplicity in MultiMalModPy, only the base model is included. 


