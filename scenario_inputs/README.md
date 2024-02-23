
## scenario_inputs

CSV files that specify different simulation experiments to run.

#### File and scenario specifications:
- `baseline_eirsweep_noCM.csv`: most basic simulation without any interventions or treatment of cases  
  - No interventions
  - No case management
  - Varying levels of transmission intensity, defined as EIR or equivalent parameter, that stay constant over the total simulation period
  - Seasonality: perennial, seasonal
  - Entomology mode: dynamic, forced

Forthcoming examples may include:
- `baseline_eirsweep_CM.csv`: 
  - No interventions
  - Varying levels of case management, not changing over time
  - Varying levels of transmission intensity, defined as EIR or equivalent parameter, that stay constant over the total simulation period
  - Seasonality: perennial, seasonal
  - Entomology mode: dynamic, forced

- `baseline_eirchange_noCM.csv`: 
  - No interventions
  - Varying levels of case management, not changing over time
  - Varying or single levels of transmission intensity, defined as EIR or equivalent parameter, that includes a step change inbetween the simulation period
  - Seasonality: perennial (possibly seasonal)
  - Entomology mode: dynamic (possibly forced)
  
- `smc_eirsweep_noCM.csv`: ...
  - ...
- ...

