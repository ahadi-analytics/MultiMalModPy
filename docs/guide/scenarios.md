# Building scenarios 
_Implementation in MultiMalModPy_

## Scenarios  

Scenarios in MultiMalModPy are created by defining multiple values for selected parameters. 
The parameters that vary across different scenarios are specified in two lists:

- `sweep_list`
- `intervention_list`


These lists define the parameters that will change during the simulation.
Below, it is explained how to configure and use these lists to generate scenario-based simulations.

## sweep_list

In the current version of MultiMalModPy, the parameters that can vary include:  
- `seasonality`
- `case_management`
- `target_output_values`


You can define the parameters in one of two ways:  
- Python Script: Modify the [setup_sim.py](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/setup_sim.py) file.
- CSV File: Store parameter values in a CSV file within the [scenario_csv](https://github.com/ahadi-analytics/MultiMalModPy/tree/main/scenario_csv) folder.

**Full factorial combinations**  
To specify which parameters should be varied in a full factorial combination (i.e., generating all possible combinations of the selected parameter values), 
list them in the sweep_list.  Exception is case_management, which includes a tuble for clinical and severe case management as the values are linked to each other.
Once the parameters are defined, the script generates a scenario CSV file, referred to as scen_df, 
which contains the parameter combinations for the simulation.

The CSV files are saved as:

- `scenarios.csv` 
- `scenarios_wseeds.csv`.


Example of `scenarios.csv`   

| index | scen_id | target_output_values | seasonality | entomology_mode | num_seeds | cm_clinical | cm_severe | cm_start | transmission_intensity_malariasimulation | transmission_intensity_OpenMalaria |
|-------|---------|----------------------|-------------|-----------------|-----------|-------------|-----------|----------|------------------------------------------|------------------------------------|
| 1     | 1       | 0.25                 | perennial   | dynamic         | 3         | 0           | 0         | 1        | 3.264134                                 | 2.139504                           |
| 2     | 2       | 0.5                  | perennial   | dynamic         | 3         | 0           | 0         | 1        | 15.11231                                 | 6.370761                           | 


Example of `scenarios_wseeds.csv`   

| index | scen_id | target_output_values | seasonality | entomology_mode | num_seeds | cm_clinical | cm_severe | cm_start | transmission_intensity_malariasimulation | transmission_intensity_OpenMalaria | seed | malariasimulation_pv |
|-------|---------|----------------------|-------------|-----------------|-----------|-------------|-----------|----------|------------------------------------------|------------------------------------|------|----------------------|
| 1     | 1       | 0.25                 | perennial   | dynamic         | 3         | 0           | 0         | 1        | 3.264134                                 | 2.139504                           | 1    | 287                  |
| 2     | 1       | 0.25                 | perennial   | dynamic         | 3         | 0           | 0         | 1        | 3.264134                                 | 2.139504                           | 2    | 153                  |
| 3     | 1       | 0.25                 | perennial   | dynamic         | 3         | 0           | 0         | 1        | 3.264134                                 | 2.139504                           | 3    | 216                  |
| 4     | 2       | 0.5                  | perennial   | dynamic         | 3         | 0           | 0         | 1        | 15.11231                                 | 6.370761                           | 1    | 287                  |
| 5     | 2       | 0.5                  | perennial   | dynamic         | 3         | 0           | 0         | 1        | 15.11231                                 | 6.370761                           | 2    | 153                  |
| 6     | 2       | 0.5                  | perennial   | dynamic         | 3         | 0           | 0         | 1        | 15.11231                                 | 6.370761                           | 3    | 216                  |


## intervention_list   

In addition to the parameters defined in sweep_list, the intervention_list can be used to specify interventions that will be applied during the simulation. 
This list is critical if you wish to model different intervention strategies as part of your scenarios.
You can modify the intervention parameters directly in the Python script or use an external CSV file, as described above.

`intervention_list = [] #can be empty or 'ccstep'`