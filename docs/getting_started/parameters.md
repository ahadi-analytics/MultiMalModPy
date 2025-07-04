
# Parameter Categories of MultiMalModPy

MultiMalModPy requires users to specify three key types of parameters:

_Malaria_  
Define and align malaria-related inputs across all models to ensure comparability.  
This includes key factors influencing malaria transmission dynamics, such as seasonality, case management, and
importation.

_Simulation_  
Specify details for each simulation experiment, including population size, number of seeds, simulation duration, and
burn-in period.  
Additionally, define scenario-specific parameters that impact transmission, seasonality, case management, and other
interventions.

_Framework_     
Configure overarching settings, such as model selection, output specifications, and directory structures for storing
inputs and results.   
Cluster-specific parameters are also required to optimize simulation execution across computing environments.



<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>NOTE:</em></strong> 
   Not all parameters can be aligned, even though those parameters shared are likely aligned.
   A detailed checklist of how the models were aligned will be made available soon.   
</div>  


-------------------------------- 

## Malaria Parameters

These parameters are primarily defined in the `SimulationConfig` class within the `setup_sim.py` script.

| **Parameter**                                                      | **Description**                                                                                                                                                                                                                                              |
|--------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [seasonality](../guide/seasonality.md)                             | Seasonal variation in malaria transmission due to climatic  factors.                                                                                                                                                                                         |
| [case_management](../guide/case_management.md)                     | Diagnosis and treatment for uncomplicated and severe malaria cases.                                                                                                                                                                                          |
| [intervention_list](../guide/scenarios.md#intervention_list)       | List of interventions to include. Note case management is per default included. Options i.e. 'ccstep'                                                                                                                                                        |
| [importation_rate](../guide/model_specificities.md#importation)    | Introduction of malaria cases from external sources (e.g., travel, migration).                                                                                                                                                                               |
| [entomology_mode](../guide/model_specificities.md#entomology-mode) | Mosquito population dynamics, biting behavior, and vector control strategies.                                                                                                                                                                                |
| [sweep_list](../guide/scenarios.md)                                | Creates a full factorial design of the selected <span title="The sweep defines all combinations of parameter values to simulate every possible scenario." style="color: #007BFF; text-decoration: underline; cursor: pointer;">sweep</span> parameter values |
| ...                                                                | ...                                                                                                                                                                                                                                                          |

_Parameter names with an asteriks (*) denote model-specific parameters_

## Simulation Parameters

These parameters are primarily defined in the `SimulationConfig` class within the `setup_sim.py` script.

| **Parameter**                                                           | **Description**                                                                                                                                                                                                                                                                                                          |
|-------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [start_year, end_year](../guide/time.md)                                | Start year of the <span title="Simulation period during which outcomes are recorded" style="color: #007BFF; text-decoration: underline; cursor: pointer;">monitoring period</span>                                                                                                                                       |
| [burnin*](../guide/time.md)                                             | Initial period for reaching an  <span title="Transmission reaches a stable state and immunity in the population has been established" style="color: #007BFF; text-decoration: underline; cursor: pointer;">equilibrium</span>.                                                                                           |
| [seed](../guide/uncertainty.md)                                         | Random seed(s) for stochastic replications.                                                                                                                                                                                                                                                                              |
| [pop_size*](../guide/age_demography.md)                                 | Simulated number of individuals.                                                                                                                                                                                                                                                                                         |
| [agebins](../guide/age_demography.md)                                   | <span title="Age limits at which simulation outputs are recorded" style="color: #007BFF; text-decoration: underline; cursor: pointer;">Age bins</span> to simulate.                                                                                                                                                      |
| [age_groups_aggregates](../guide/age_demography.md)                     | <span title="One or more overlapping age bins for output aggregation" style="color: #007BFF; text-decoration: underline; cursor: pointer;">Age groups</span> for output aggregation.                                                                                                                                     |
| [run_mode](../getting_started/usage.md)                                 | Simulation execution mode, supporting testing and production configurations.                                                                                                                                                                                                                                             |
| [emodstep*](../guide/model_specificities.md)                                | EMOD: use <span title="Saves the population state at a specific time, allowing simulations to start from that point instead of re-running the burn-in period" style="color: #007BFF; text-decoration: underline; cursor: pointer;">serialization</span>  to separate burn-in and pickup simulation, or run all together. |
| [emod_calib_params*](../guide/model_specificities.md)                       | EMOD: run simulations with alternative within-host calibration.                                                                                                                                                                                                                                                          |
| [mpv*](../guide/model_specificities.md)                                 | malariasimulation parameter variation.                                                                                                                                                                                                                                                                                   |
| [target_output_name, target_output_values](../getting_started/usage.md) | Output type and target location for CM 0 and 15% simulations using EMOD (pop: 1,000), OpenMalaria (pop: 50,000), and malariaSimulation (pop: 50,000) under seasonal and perennial profiles.                                                                                                                              |
| [test](../getting_started/usage.md)                                     | Reduces the computational demand by lowering pop_size, burn-in and seeds                                                                                                                                                                                                                                                 |
| ...                                                                     | ...                                                                                                                                                                                                                                                                                                                      |

_Parameter names with an asteriks (*) denote model-specific parameters_

## Framework Parameters

These parameters are primarily defined through the arguments provided when launching simulations
via `python launch_sim.py <args>`.
They are specified in the `parse_launch_args` function within the `utility/helper.py` script.

| **Parameter**                                  | **Description**                                                                                                                    |
|------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| [directory](../getting_started/usage.md)             | Specifies the directory for storing simulation inputs, config, and model outputs.                                                  |
| [suite](../getting_started/usage.md)                 | Suite (collection of) of simulation experiments.                                                                                   |
| [expname, exp_name](../getting_started/usage.md)     | Name of the simulation experiment.                                                                                                 |
| [models](../getting_started/usage.md) | Specifies which models to run (one or multiple).                                                                                   |
| [user](../getting_started/usage.md)                  | Creates a user-specific directory for storing experiments and simulation outputs.                                                  |
| [rownum](../getting_started/usage.md)                | If running from CSV, defines row of the simulation scenario to run.                                                                |
| [memory_per_sim*](../getting_started/usage.md)       | Memory allocation per simulation, ensuring appropriate resources.                                                                  |
| [time_per_sim*](../getting_started/usage.md)         | Max time for each simulation to manage computational time and resources                                                            |
| [analyzer_list](../getting_started/usage.md)           | Type of standardized outputs to generate (i.e. select default or custom ones)                                                      |
| [analyzer_script](../getting_started/usage.md) | Name of the analyzer script (default, optional for advanced users)                                                                 |
| [plots_to_run](../getting_started/usage.md)    | Plots to generate (allows custom plots for advanced users)                                                                         |
| [sim_params_list](../getting_started/usage.md)       | Lists the simulation parameters to be used across the models, allowing for consistent configuration of the simulation environment. |
| ...                                            | ...                                                                                                                                |

_Parameter names with an asteriks (*) denote model-specific parameters_  

**Next up** : Go to [building scenarios](../guide/scenarios.md) to learn how to specify parameters.
