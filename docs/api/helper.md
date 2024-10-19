# helper.py 

Several custom functions are defined for facilitating processes of the framework: 

[parse_launch_args](#`parse_launch_args`)  
[parse_args](#`parse_args`)  
[get_param_from_dataframe](#`get_param_from_dataframe`)  
[make_dirs](#`make_dirs`)  
[check_exp_inputs](#`check_exp_inputs`)  
[save_scen](#`save_scen`)  
[save_exp_scen](#`save_exp_scen`)  
[rep_scen_df](#`rep_scen_df`)  
[create_simsetup_csv](#`create_simsetup_csv`)
[create_scenarios_csv](#`create_scenarios_csv`)
[as_list](#`as_list`)  
[write_txt](#`write_txt`)  
[str_to_digit](#`str_to_digit`)  

------------------------------

## `parse_launch_args`
Parses command-line arguments for the launch of the simulation script.

### Returns
- `argparse.Namespace`: Parsed command-line arguments.

### Arguments
- `-d`, `--directory` (str, optional): Job directory of burnin; ignored if no EMOD burnin.
- `--suite` (str, optional): Description of the suite name (default: current date and "test").
- `--expname` (str, optional): Description of the experiment name (default: "sims_entomologymode_seasonality_intervention" with current time).
- `--emodstep` (str, optional): Description of EMOD step (choices: None, 'burnin', 'pickup', 'new_pickup').
- `--serializedid` (str, optional): Description of EMOD serialized ID (default: empty string).
- `--models` (list of str, optional): Models to run (default: ['EMOD', 'malariasimulation', 'OpenMalaria']).
- `--user` (str, optional): Subdirectory for simulations by user (default: current user from environment).
- `--csv` (str, optional): Name of scenario CSV.
- `-i`, `--interventions` (list of str, optional): Specify interventions to run (choices: ['cc_step', 'smc']).
- `--rownum` (int, optional): Row number of specified scenario CSV.
- `-r`, `--run_mode` (str, optional): Specify run mode (choices: None, 'test', 'calibrun', 'productionrun').
- `--emod_calib_params` (bool, optional): Whether to include calibration parameters as a sweep variable (EMOD only).
- `--mpv` (bool, optional): Specify whether to run malariasimulation with parameter variation (default: True).
- `--output_type` (str, optional): Type of output to align transmission in each model (choices: ['prevalence_2to10', 'eir']).

---

## `parse_args`
Parses command-line arguments for simulation specifications.

### Returns
- `argparse.Namespace`: Parsed command-line arguments.

### Arguments
- `-d`, `--directory` (str, required): Job Directory where exp.obj is located.

------------------------------

## `get_param_from_dataframe`
Retrieves a parameter value from a DataFrame and returns it in the correct format for storage in an experiment object (exp).

### Arguments
- `df` (pandas.DataFrame): The DataFrame containing the parameter value.
- `name` (str): The name of the parameter.

### Returns
- `Union[list, str]`: The parameter value, either as a list or a string based on the parameter's requirements.

### Example
``` 
exp.seasonality = get_param_from_dataframe(exp_scen_df, 'seasonality', listparam=True)
```


----------------------------------

## `make_dirs`
Creates the necessary directories for a simulation experiment, based on the provided experiment object.

### Arguments
- `exp` (Experiment): The experiment object that contains project directory information, including:
  - `custom_subdir` (str, optional): A custom subdirectory name for organizing directories.
  - `SUITEname` (str): The name of the suite under which directories will be organized.
  - `job_directory_manifest` (str): The base directory for job-related files.
  - `exp_name` (str): The name of the experiment.
  - `output_directory_manifest` (str): The base directory for output files.
  - `models_to_run` (list of str): A list of simulation models to be executed (e.g., 'EMOD', 'OpenMalaria', 'malariasimulation').
  - `emod_step` (str): Specifies the EMOD step being executed (e.g., 'burnin', 'pickup').
  - `overwrite` (bool, optional): If set to `True`, existing directories will be overwritten. Defaults to `False`.

### Returns
- `exp` (Experiment): The updated experiment object with the paths for various directories populated.

### Description
This function defines and creates the following directories based on the experiment parameters:

1. **Suite Directory**: A grouping folder for simulation experiments, determined by the `SUITEname` and `custom_subdir` if provided.
2. **Job Directory**: The directory where simulation files related to the specific experiment will be stored.
3. **Simulation Output Directory**: The directory for storing result CSV files and figures.

### Directory Structure
The function creates the following structure:
- `<job_directory_manifest>/<SUITEname>/<exp_name>/`
  - `log/` (for storing logs related to the simulation)
  - `<sim_out_dir>/`
    - `EMOD/` (if 'EMOD' is in `models_to_run`)
    - `OpenMalaria/` (if 'OpenMalaria' is in `models_to_run` and `emod_step` is not 'burnin')
    - `malariasimulation/` (if 'malariasimulation' is in `models_to_run` and `emod_step` is not 'burnin')

### Example
```  
# Assuming 'exp' is an instance of the Experiment class with necessary attributes set
exp = make_dirs(exp, overwrite=True)
``` 


-----------------------------------------------------


## `check_exp_inputs`
Validates the inputs for a simulation experiment, ensuring all parameters are set correctly before execution.

### Arguments
- `exp` (Experiment): Custom object containing experiment specifications, including:
  - `openmalaria_survey_step` (str): The survey step interval for OpenMalaria.
  - `analyzer_list` (list of str): List of analyzers to use.
  - `num_seeds_burnin` (int): Number of seeds for EMOD burn-in.
  - `burnin` (int): Length of the burn-in period.
  - `age_groups_aggregates` (list): Aggregated age groups.
  - `agebins` (list): Age bins to be used.
  - `models_to_run` (list of str): Models to be executed (e.g., 'EMOD', 'OpenMalaria').
  - `entomology_mode` (str): The mode of entomology to be used ('dynamic' or other).
  - `output_type` (str): The type of output expected ('eir', 'prevalence_2to10', etc.).
  - `intervention_list` (list of str): List of interventions to be applied.
  - `start_year` (int): The starting year for the simulation.
  - `end_year` (int): The ending year for the simulation.
  - `step_in_years` (int): The number of years between steps in the simulation.

- `print_reminder` (bool, optional): If `True`, print reminders regarding potential issues (default: `True`).

- `intervention_checks` (bool, optional): If `True`, perform checks specific to interventions (default: `True`).

- `attribute_check` (bool, optional): If `True`, check attributes for inclusion in the sweep list (default: `False`).

### Raises
- `ValueError`: If any input parameters are invalid, with specific messages detailing the issue.

### Description
This function performs various checks on the experiment parameters, including:  
1. **Survey Steps and Analyzers**: Ensures compatibility between the survey steps and analyzers being used.  
2. **Burn-in Period**: Checks for an appropriate burn-in period, raising warnings or errors if conditions are not met.  
3. **Age Bins**: Validates that the specified age bins are adequate for the defined age groups and raises errors if necessary.  
4. **Model-Specific Validations**: Ensures that the parameters align with the requirements of specific models (e.g., EMOD).  
5. **Intervention Validations**: Checks the compatibility of interventions with the overall simulation setup.  
6. **Attribute Checks**: Validates that attributes with multiple values are included in the sweep list where required.  

### Example
``` 
# Assuming 'exp' is an instance of the Experiment class with necessary attributes set
try:
    check_exp_inputs(exp)
except ValueError as e:
    print(f"Input validation error: {e}")

``` 

-----------------------------------------------------


## `save_scen`
Saves a scenario DataFrame to a CSV file in the specified directories.

### Arguments
- `scen_df` (pandas.DataFrame): The DataFrame containing the scenario data to be saved.
  
- `fname` (str): The name of the CSV file to be created (e.g., `'scenario.csv'`).

- `save_dirs` (list of str, optional): A list of directories where the CSV file will be saved. If not provided, the function will not save the file.

### Description
This function iterates through the provided list of directories (`save_dirs`) and saves the specified DataFrame (`scen_df`) as a CSV file with the given filename (`fname`). Each directory in the list will receive a copy of the CSV file.

### Example

```
import pandas as pd

# Create a sample DataFrame
scenario_data = {
    'param1': [1, 2, 3],
    'param2': ['A', 'B', 'C']
}
scen_df = pd.DataFrame(scenario_data)

# Define the filename and directories
fname = 'scenario.csv'
directories = ['dir1', 'dir2']

# Save the scenario DataFrame to the specified directories
save_scen(scen_df, fname, save_dirs=directories)
``` 

-----------------------------------------------------

## `save_exp_scen`
Saves the experiment and scenario data to the specified save directories.

### Arguments  
- `exp` (Experiment): The experiment object containing experiment specifications.
- `scen_df` (pandas.DataFrame): The scenario data to be saved.
- `save_dirs` (list): List of directories to save the data.

### Description  
This function saves the experiment object and scenario DataFrame to specified directories. The scenario data is saved as a CSV file, and the experiment object is saved using the pickle format.

### Behavior  
- The function iterates over each directory in `save_dirs`.
- For each directory:
  - The `scen_df` DataFrame is saved as `scenarios.csv` without including the index.
  - The `exp` object is serialized and saved as `exp.obj` using the `pickle` module.

### Example  
``` 
# Assuming 'exp' is an Experiment object and 'scen_df' is a DataFrame of scenario data
save_dirs = ['path/to/save/directory1', 'path/to/save/directory2']
save_exp_scen(exp, scen_df, save_dirs)

``` 



-------------------------------------------

## `rep_scen_df`
Repeats scenario data in a DataFrame based on the number of seeds.

### Arguments  
- `df` (pandas.DataFrame): The DataFrame containing the scenario data.

### Returns  
- `pandas.DataFrame`: A DataFrame with repeated scenario data based on the number of seeds.

### Description  
This function takes a DataFrame containing scenario data and repeats each scenario based on the specified number of seeds. The resulting DataFrame will have multiple rows for each original scenario, corresponding to the number of seeds for that scenario.

### Behavior  
- The function first attempts to drop the `index` column from the DataFrame (if it exists).
- It uses `np.repeat` to create a new DataFrame (`rep_df`) where each row in the original DataFrame is repeated according to the value in the `num_seeds` column.
- The index of the new DataFrame is reset, and a new `seed` column is created, indicating the seed number for each repeated scenario.

### Example  
``` 
# Assuming 'df' is a DataFrame with scenario data including a 'num_seeds' column
repeated_df = rep_scen_df(df)
``` 

-------------------------------------------

## `create_simsetup_csv`
Creates a CSV file containing simulation setup parameters.

### Arguments  
- `exp` (Experiment): The experiment object containing experiment specifications.

### Description  
This function generates a CSV file that captures various setup parameters for a simulation experiment. The parameters are derived from the provided `exp` object and are structured in a way that allows for easy access and understanding.

### Behavior  
- The function constructs a dictionary (`setup_dic`) containing key simulation parameters, such as:
  - `run_mode`
  - `job_directory`
  - `sim_out_dir`
  - `emod_serialized_id`
  - `burnin_directory`
  - `nexps`
  - `sweep_list`
  - `monitoring_years`
  - `pop_size`
  - `agebins`
  - `seasonality`
  - Various seasonal and perennial settings, converted to a string format suitable for CSV.
  - `start_year` and `end_year`
  - `burnin` duration
  - Start years for different simulation models
  - List of interventions

- A DataFrame (`setup_df`) is created from this dictionary, with parameters and their corresponding values.

- The resulting DataFrame is saved as a CSV file named `exp_setup_df.csv` in the specified directories (both the job directory and simulation output directory).

### Example
``` 
# Assuming 'exp' is an instance of the Experiment class with the necessary attributes
create_simsetup_csv(exp)
```  


-----------------------------------------------------


## `create_scenarios_csv`
Creates a scenarios CSV file based on the provided experiment object and column list.

### Arguments  
- `exp` (Experiment): The experiment object containing the scenario attributes.
  
- `col_list` (list): A list of attribute names to include in the scenarios CSV file. 
  - **Example:** `['eirs', 'case_management', 'seasonality']`.

- `add_cols` (bool, optional): Whether to add additional columns such as `'entomology_mode'`, `'num_seeds'`, etc. 
  - **Default:** `True`.

### Returns  
- `pandas.DataFrame`: A DataFrame representing the scenarios.

### Description  
This function generates a DataFrame containing all possible combinations of the specified scenario attributes from the `exp` object. If the `add_cols` parameter is set to `True`, additional columns related to the experiment attributes are added to the DataFrame.

### Behavior  
- If `col_list` is not provided, it defaults to `['output_target', 'case_management', 'seasonality']`.
  
- Depending on the `run_mode` of the experiment (`'calibrun'`, `'test'`, or `None`), specific values for `importation_rate`, `output_target`, and other parameters are set.

- The function uses `itertools.product` to generate combinations of the specified attributes, while ensuring that combinations are valid according to the defined constraints.

### Example  
``` 
# Assuming 'exp' is an instance of the Experiment class with the necessary attributes
columns_to_include = ['output_target', 'case_management', 'seasonality']
scenarios_df = create_scenarios_csv(exp, columns_to_include)

# The resulting DataFrame can be saved to a CSV file or used for further analysis
print(scenarios_df.head())
``` 
-----------------------

## `as_list`
Converts the input `x` to a list if it is not already a list.

### Arguments
- `x`: The input to be converted to a list. This can be of any type.

### Returns
- `list`: If `x` is already a list, it returns `x`. Otherwise, it returns a new list containing `x` as its sole element.

### Description
This utility function checks the type of the input `x`. If `x` is not of type `list`, it wraps `x` in a list. If `x` is already a list, it returns `x` unchanged.

### Example
``` 
# Example usages of as_list
single_value = 42
result1 = as_list(single_value)
# result1 is now [42]

existing_list = [1, 2, 3]
result2 = as_list(existing_list)
# result2 is now [1, 2, 3], unchanged

empty_value = None
result3 = as_list(empty_value)
# result3 is now [None]

``` 

-----------------------

## `write_txt`
Writes a text object to a file.

### Arguments
- `txtobj` (`str`): The text object to write to the file.
- `path` (`str`): The directory path where the file will be saved.
- `fname` (`str`): The filename to use for the saved file.

### Description
This function takes a string `txtobj` and writes it to a specified file in the given directory. The function creates or overwrites the file if it already exists.

### Example
``` 
# Example usage of write_txt
text_content = "Hello, world!"
directory_path = "./"
filename = "greeting.txt"

write_txt(text_content, directory_path, filename)
```  



----------------------- 

## `str_to_digit`
Converts a string to a float if possible; otherwise, returns the original string.

### Arguments
- x (str): The input string to be converted.

### Returns
float or str: The converted float if the conversion is successful; otherwise, the original string.

### Description
This utility function attempts to convert the input string x into a float. If the conversion fails (for example, if x cannot be converted to a float), it returns the original string unchanged.

### Example
```  
# Example usages of str_to_digit
numeric_str = "3.14"
result1 = str_to_digit(numeric_str)
# result1 is now 3.14 (as a float)

non_numeric_str = "abc"
result2 = str_to_digit(non_numeric_str)
# result2 is now "abc" (unchanged)
``` 

