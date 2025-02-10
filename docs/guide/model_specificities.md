
# Model specific configurations


## Serialization

###  EMOD
EMOD allows serialization and to use an alternative base calibration.    

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
  

## Using alternative base calibration

### EMOD
This section is under construction... 


### OpenMalaria     

Model variants  
OpenMalaria allows to take into account model and parameter uncertainty through varying  [model variants](https://github.com/SwissTPH/openmalaria/wiki/ModelWithinHost#specification-of-model-variants)). 
However, for simplicity in MultiMalModPy, only the base model is included. 



## Parameter sampling    

### malariasimulation 
malariasimulation allows paramter sampling.  

In malariasimulation, accounting for parameter uncertainty to better reflect potential variability in the simulation results has been integrated by drawing parameter values
from posterior distributions around defined parameter sets.   

Via the set_parameter_draw function up to 1000 different parameter sets for 32 simulation parameters can be selected.
These 32 parameters correspond to: fixed state transitions, immunity boost grace periods, immunity decay rates, immunity reducing probability of detection, infectivity towards mosquitoes,
mortality, probability of clinical infection, probability of pre-erythrocytic infection, and probability of severe infection.

In `MultiMalModPy`, seed values are paired with the parameter_draw value.  

For a single seed, varying parameter sets from in total 1000 sets are drawn and a new draw is made each time new simulations run.
A breakdown of each parameter that is affected in the parameter draw, with parameter type, description, default value, 
maximum and minimum is shown in the core parameter table for malariasimulation.

## Importation 

### EMOD  

Importation in EMOD is setup using the [add_outbreak_individual](https://docs.idmod.org/projects/emodpy-malaria/en/latest/emodpy_malaria.interventions.outbreak.html#emodpy_malaria.interventions.outbreak.add_outbreak_individual) function from emodpy-malaria.  
The specific python code snippet, as used in MultiMalModPy [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/functions/EMOD_functions.py#L113), is shown below:  

```python
ncases_per_year_per1000pop = (exp.emod_importation_rate * exp.emod_pop_size) / 1000
add_outbreak_individual(camp, start_day=1, target_num_individuals=ncases_per_year_per1000pop,
                        repetitions=-1, timesteps_between_repetitions=365)
```

### OpenMalaria  

Importation in OpenMalaria is setup using [importedInfections](https://github.com/SwissTPH/openmalaria/wiki/ModelIntervMisc#import-infections):
The specific XML chunk, as used in MultiMalModPy [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/OpenMalaria/scaffolds/R0000GA.xml#L72), is shown below:  

```XML 
<importedInfections>
    <timed>
        <rate time="0" value="@importation_rate@"/>
    </timed>
</importedInfections>
```

## Entomology mode

### EMOD  

Relevant code chunks are under EMOD_functions.py [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/functions/EMOD_functions.py#L100) and
 under EMOD/utils.py [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/utils.py#L61).

'Forced' EIR uses the [add_scheduled_input_eir](https://docs.idmod.org/projects/emodpy-malaria/en/latest/emodpy_malaria.interventions.inputeir.html#emodpy_malaria.interventions.inputeir.add_scheduled_input_eir) function from emodpy-malaria.

```python
## If forced EIR, treated as campaign in EMOD
if row.entomology_mode == 'forced':
    set_inputEIR_seasonality(camp, float(row.model_input_em), row.seasonality)
```

```python
if entomology_mode == 'dynamic':
    task.common_assets.add_directory(os.path.join(manifest.input_dir, "example_weather"), relative_path="climate")
```

They also require different sweeping, defined in `config_sweep_builder` (and `config_sweep_builder_pickup`) [see code](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/utils.py#L251C1-L265C42).
You can find details on parameter sweeping for building scenarios under [simulation guide/scenarios]()

### OpenMalaria  

`entomology_mode` in OpenMalaria defines the feedback from human infectiousness to subsequent Entomological Infection Rate (EIR).   
`entomology_mode` in OpenMalaria is setup by literally defining the ['mode of entomology'](https://github.com/SwissTPH/openmalaria/wiki/ModelTransmission#simulation-mode):
The specific XML chunk, as used in MultiMalModPy [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/OpenMalaria/scaffolds/R0000GA.xml#L131C6-L131C21), is shown below:  

```XML 
<entomology mode="@entomology_mode@" name="Namawala" scaledAnnualEIR="@eir@">
```


