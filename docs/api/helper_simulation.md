# helper_simulation.py 

Several custom functions are defined for processing simulations:

[output_target_to_xTemp](#`output_target_to_xTemp`)  
[output_target_to_eir](#`output_target_to_eir`)  
[get_intervention_params](#`get_intervention_params`)  
[get_simulation_time_params](#`get_simulation_time_params`)
[param_variation](#`param_variation`)  
[get_seasonal_eir](#`get_seasonal_eir`)  
[monthly_to_daily_EIR](#`monthly_to_daily_EIR`)  


-----------

## `output_target_to_xTemp`
Interpolates target values based on experimental data and model specifications.

### Arguments
- `df` (`pandas.DataFrame`): A DataFrame containing the scenario data with relevant attributes for interpolation.
- `exp` (`Experiment`): An object containing experiment specifications, including paths and parameters.
- `model` (`str`): The name of the model for which the interpolation is being performed.

### Returns
- `list`: A list of interpolated values based on the provided target output and model specifications.

### Description
This function reads an interpolation CSV file specific to the provided model and interpolates values based on the `output_target` specified in the input DataFrame `df`. The output is adjusted based on the population size defined in the experiment.

### Steps  
1. Constructs the path to the interpolation CSV file based on the `interp_path` and `model` from the `exp` object.  
2. Reads the interpolation data from the CSV file.  
3. Determines the relevant output type column based on the `output_type` specified in the `exp` object.  
4. Iterates over each row in the input DataFrame:  
    - Filters the interpolation data based on clinical management, seasonality, model name, and population size.  
    - Interpolates the corresponding values based on the specified `output_target`.  
    - Adjusts the interpolated values based on the experiment's population size.  
5. Applies constraints to ensure the interpolated values are within reasonable limits (minimum of 0.01 and maximum of 10,000).  
6. Returns the list of interpolated values.  

### Example  
``` 
# Example usage of output_target_to_xTemp
scenario_df = pd.DataFrame({
    'cm_clinical': [0.45, 0.30],
    'seasonality': ['seasonal', 'perennial'],
    'output_target': [1, 2]
})

experiment = Experiment()  # Assume this is properly initialized
model_name = 'EMOD'

interpolated_results = output_target_to_xTemp(scenario_df, experiment, model_name)
``` 


----------------------------

## `output_target_to_eir`
Interpolates target values based on experimental data to estimate the Entomological Inoculation Rate (EIR).

### Arguments
- `df` (`pandas.DataFrame`): A DataFrame containing the scenario data with relevant attributes for interpolation.
- `exp` (`Experiment`): An object containing experiment specifications, including paths and parameters.
- `model` (`str`): The name of the model for which the interpolation is being performed.

### Returns
- `list`: A list of interpolated EIR values based on the provided target output and model specifications.

### Description
This function reads an interpolation CSV file specific to the provided model and estimates EIR values based on the `output_target` specified in the input DataFrame `df`. The output is adjusted according to the population size defined in the experiment.

### Steps
1. Constructs the path to the interpolation CSV file based on the `interp_path` and `model` from the `exp` object.  
2. Reads the interpolation data from the CSV file.  
3. Determines the relevant output type column based on the `output_type` specified in the `exp` object.  
4. Iterates over each row in the input DataFrame:  
    - Filters the interpolation data based on clinical management, seasonality, model name, and population size.  
    - Interpolates the corresponding EIR values based on the specified `output_target`.  
    - Adjusts the interpolated values based on the experiment's population size.  
5. Applies constraints to ensure the interpolated values are within reasonable limits (minimum of 0.01 and maximum of 1,000).  
6. Returns the list of interpolated EIR values.  

### Example  
``` 
# Example usage of output_target_to_eir
scenario_df = pd.DataFrame({
    'cm_clinical': [0.45, 0.30],
    'seasonality': ['seasonal', 'perennial'],
    'output_target': [1, 2]
})

experiment = Experiment()  # Assume this is properly initialized
model_name = 'malariasimulation'

interpolated_eir_results = output_target_to_eir(scenario_df, experiment, model_name)

``` 


-------------------------------------

## `get_intervention_params`
Retrieves intervention parameters for a specific experiment.

### Parameters
- `exp` (`Experiment`): An object representing the experiment containing the relevant specifications and attributes.

### Returns
- `dict`: A dictionary containing the intervention parameters based on the specified experiment.

### Description
This function imports the `exp_params_to_update` function from the `scenario_inputs.intervention_params` module and uses it to retrieve the intervention parameters relevant to the provided `exp` object. This allows for the appropriate configuration of interventions based on the experiment's specifications.

### Example
``` 
# Example usage of get_intervention_params
experiment = Experiment()  # Assume this is properly initialized
intervention_parameters = get_intervention_params(experiment)

print(intervention_parameters)  # Outputs the intervention parameters for the experiment
``` 


-------------------------------------------------


## `get_simulation_time_params`
Calculates simulation time parameters for EMOD, malariasimulation, and OpenMalaria based on the provided experiment specifications.

### Parameters
- `exp` (`Experiment`): An object representing the experiment containing the following specifications:
  - `start_year` (`int`): The monitoring start year (required by OpenMalaria utilities).
  - `end_year` (`int`): The monitoring and simulation end year (required by OpenMalaria utilities).
  - `burnin` (`int`): Duration of pre-monitoring years to run.
  - `emod_step` (`str`): Indicates whether EMOD runs in one or two steps ('None' for a single run, 'burnin' for the burn-in phase, or 'pickup' for two separate runs).

### Returns
  - `exp` (`Experiment`): The updated experiment object with the following simulation time parameters:
  - `sim_start_year` (`int`): The simulation start year.
  - `monitoring_years` (`int`): The number of years to monitor (required in the EMOD analyzer).
  - `sim_dur_years` (`int`): The total simulation duration in years.

### Description
This function calculates various time-related parameters for the simulation based on the experiment's start and end years, burn-in duration, and the specified EMOD step. It updates the `exp` object with these calculated parameters and provides necessary logging for clarity.

### Example
``` 
# Example usage of get_simulation_time_params
experiment = Experiment()  # Assume this is properly initialized
experiment.start_year = 2025
experiment.end_year = 2030
experiment.burnin = 2
experiment.emod_step = 'None'  # Can also be 'burnin' or 'pickup'

updated_experiment = get_simulation_time_params(experiment)

print(updated_experiment.sim_start_year_emod)  # Outputs the simulation start year for EMOD
print(updated_experiment.monitoring_years)      # Outputs the number of monitoring years
print(updated_experiment.sim_dur_years)         # Outputs the total simulation duration

``` 


----------------------------- 

## `param_variation`
Performs parameter variation for malariasimulation simulations based on the given scenario DataFrame and experiment object.

### Parameters
- `df` (`pandas.DataFrame`): A DataFrame containing data from `scenarios.csv`.
- `exp` (`Experiment`): An object representing the experiment containing specifications related to malariasimulation.

### Returns
- `pandas.DataFrame`: The original DataFrame with an additional column named `malariasimulation_pv` that represents the malariasimulation parameter variation values.

### Description
This function introduces variation in parameters for malariasimulation based on the specified number of seeds. If the number of seeds exceeds 1000, the function will use repeat values to ensure compatibility. The resulting parameter variations are stored in a new column in the DataFrame.

### Example
``` 
# Example usage of param_variation
import pandas as pd

# Create a sample DataFrame
data = {'seed': [1, 2, 3, 4, 5]}
df = pd.DataFrame(data)

# Create an Experiment object with necessary attributes
experiment = Experiment()  # Assume this is properly initialized
experiment.models_to_run = ['malariasimulation']
experiment.malariasimulation_parameter_variation = True
experiment.num_seeds = 10  # Example value

# Perform parameter variation
result_df = param_variation(df, experiment)

# Display the modified DataFrame
print(result_df)


``` 

-----------------------------

## `get_seasonal_eir`
Generates seasonal EIR (Entomological Inoculation Rate) values.

### Parameters
- `exp` (`Experiment`, optional): An object representing the experiment containing specifications related to seasonal EIR values.

### Returns
- `tuple` or `Experiment`: 
  - If `exp` is provided, the function returns the updated `Experiment` object with seasonal EIR attributes.
  - If `exp` is `None`, it returns a tuple containing:
    - `season_daily` (`list`): The defined seasonal shape of daily EIR values.
    - `season_month` (`list`): The calculated monthly EIR values from the seasonal pattern.
    - `seasonal` (`list`): Seasonal EIR values rescaled to sum to 1.
    - `perennial` (`list`): Perennial EIR values per month.

### Description
This function computes seasonal EIR values based on predefined monthly patterns. If an `Experiment` object is provided, it updates the object with calculated seasonal attributes. If not, it returns the calculated values for further use.

### Examples
```
# Example usage when no Experiment object is provided
season_daily, season_month, seasonal, perennial = get_seasonal_eir()

# Example usage with an Experiment object
exp = Experiment()  # Assume this is properly initialized
updated_exp = get_seasonal_eir(exp)
```  

-----------------------------

## `monthly_to_daily_EIR`
Converts monthly EIR values to daily values using cubic spline interpolation.

### Parameters
- `monthly_EIR` (`list of floats`): A list containing monthly EIR values. It should have either 12 or 13 values.

### Returns
- `list of floats`: A list containing daily EIR values.

### Description
This function takes a list of monthly EIR values and converts them to daily EIR values through cubic spline interpolation. If the list contains exactly 12 monthly values, an average of the first and last values is appended to create a complete cycle of 13 values. The resulting daily EIR values are normalized to reflect a daily average.

### Raises
- `Exception`: If the input list does not have 12 or 13 values, an exception is raised indicating that the monthly EIR should have either 12 or 13 values.

### Examples
``` 
# Example usage
monthly_EIR = [2.0, 1.5, 1.2, 0.8, 0.5, 0.3, 0.2, 0.1, 0.4, 1.0, 1.8, 2.5]
daily_EIR = monthly_to_daily_EIR(monthly_EIR)

``` 

