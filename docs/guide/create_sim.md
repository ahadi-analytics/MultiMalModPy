# Create simulations



The `launch_sim.py` script launches simulation runs, with the possibility to change and
edit parameters directly in the python script or to read in parameter values from a csv file.

The configuration had been moved to the `helper.py` script, allowing the launch python script to overwrite parameters as
needed.



## Scenarios implemented

Scenarios csvs are stored in the `scenario_inputs` sub-directory:

- `baseline_eirsweep_noCM.csv`: most basic simulation without any interventions or treatment of cases  
  Forthcoming examples may include:
- `baseline_eirsweep_CM.csv`:
- `baseline_eirchange_noCM.csv`:
- `cc_step_test.csv`: ...
- `smc_eirsweep_noCM.csv`: ...
- ...

Details provided
in [scenario_inputs/README](https://github.com/numalariamodeling/model-characterization/blob/main/scenario_inputs/README.md)


Example CSV files that specify different simulation experiments to run.
File and scenario specifications most basic simulation without any interventions or treatment of cases.

**baseline_eirsweep_noCM.csv**   
- No interventions  
- No case management  
- Varying levels of transmission intensity, defined as EIR or equivalent parameter, that stay constant over the total simulation period  
- Seasonality: perennial, seasonal  
- Entomology mode: dynamic, forced  


**baseline_eirsweep_CM.csv**  
- No interventions  
- Varying levels of case management, not changing over time  
- Varying levels of transmission intensity, defined as EIR or equivalent parameter, that stay constant over the total simulation period  
- Seasonality: perennial, seasonal  
- Entomology mode: dynamic, forced  

**baseline_eirchange_noCM.csv**    
- No interventions  
- Varying levels of case management, not changing over time  
- Varying or single levels of transmission intensity, defined as EIR or equivalent parameter, that includes a step change inbetween the simulation period  
- Seasonality: perennial (possibly seasonal)  
- Entomology mode: dynamic (possibly forced)  





## Customize simulations
Coming soon..


