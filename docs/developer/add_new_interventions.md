
# Add New Interventions 

This page explains how to **create new interventions** in MultiMalModPy.  
If you're looking to **run simulations using existing interventions**, see the [User Guide – Interventions](../getting_started/parameters.md#interventions).


<div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; border-left: 5px solid #FFB6C1;">
    <span style="font-weight: bold;">❗</span> Adding an intervention using **model-specific defaults** from different models requires **careful implementation**, **testing**, and **alignment** to ensure results remain comparable across models.
</div>


---

## Intervention Structure

Interventions are modular and located under:  

interventions/  
│  
├── init.py  
├── ccstep.py  
└── smc.py # Placeholder, not currently supported  
└── <intervention>.py # Any new interventions user may add

To activate interventions, import them in your experiment setup:

```python
from interventions.ccstep import *
# from interventions.smc import *  # Currently not supported
```


# How to add a new intervention (e.g., SMC) 

Adding a new intervention involves:

1. Create a file: `interventions/smc.py`
2. Implement intervention logic for each of the models:

    - EMOD
       - `EMOD/functions/interventions.py`: Add or update functions that define EMOD-specific intervention parameters and how they are injected into the configuration or campaign builder.
    - malariasimulation
       - `malariasimulation/functions/interventions.R`: Add functions that define R-based intervention parameters. 
    - OpenMalaria
      - `OpenMalaria/functions/interventions.py`: Define logic for what XML fragment(s) need to be added for the new intervention.  
      - `OpenMalaria/snippets.py`: Add or update reusable XML chunks or template snippets for the new intervention.  
      - `OpenMalaria/scaffolds.py`: Modify or extend XML scaffold generation to insert placeholders or dynamically fill intervention-specific tags.  
      
3. Define these functions: 
  ```
     def smc_params(exp): ...
     def smc_columns(exp, df): ...
     def smc_input_check(exp): ...
  ```
4. Update the dispatchers:
Edit these functions (usually found in your experiment setup or helper file):

- `exp_params_to_update`: Reads exp.intervention_list and adds parameters for each supported intervention
- `scenario_df_to_update`: Modifies the scenario dataframe (e.g., removes duplicates, adds columns)
- `intervention_params_to_check`: Validates experiment parameters for each active intervention


```  
    # In exp_params_to_update
    if 'smc' in exp.intervention_list:
        exp = smc_params(exp)
    
    # In scenario_df_to_update
    if 'smc' in exp.intervention_list:
        df = smc_columns(exp, df)
    
    # In intervention_params_to_check
    if 'smc' in exp.intervention_list:
        smc_input_check(exp)
```

5. Consider intervention specific custom reporter or plotters.
 

6. Test (example):

```
 python launch_sim.py --models EMOD --interventions smc --test
``` 

