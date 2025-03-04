# Building scenarios 
_Implementation in MultiMalModPy_

Scenarios are created by defining multiple values for selected parameters.
In the current version, the parameters that can have varying values include:
- `seasonality`
- `case_management` 
- `target_output_values`


You can define the parameters in one of two ways:  
- Python Script: Modify the [setup_sim.py](https://github.com/ahadi-analytics/model-characterization/blob/main/setup_sim.py) file.
- CSV File: Store parameter values in a CSV file within the [scenario_csv](https://github.com/ahadi-analytics/model-characterization/tree/main/scenario_csv) folder.


To specify which parameters should be used for a full factorial combination, list them in `sweep_list`. This list determines which parameters will vary in the simulation.
Once defined, the script generates a scenario CSV file, referred to as scen_df, which is saved as:
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
