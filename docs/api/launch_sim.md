# launch_sim.py 


This script is designed to set up and launch simulations, enabling users to easily customize 
and manage their simulation experiments:  
[Dependencies](#dependencies)
[Configuration Steps](#configuration)
[Execution](#execution)
[Custom Functions Overview ](#function_overview)

## Dependencies  

This script requires the following Python modules:
- `logging`
- `manifest`
- `utility.helper`
- `utility.helper_slurm`
- `utility.helper_simulation`
- `config_exp`
- `os`
- `pickle`
- `pandas`

The script sets up various EMOD flags to determine how simulations are run. 
It can execute in a single run or separate into burn-in and pickup phases, depending on the specified `emodstep`.
In addition, the script retrieves parsed arguments from the command line, allowing users to specify configurations such as the simulation directory, models to run, and specific scenarios.


## Configuration Steps

1. **Pickup or New Pickup**:  
   If the `emodstep` is set to `pickup` or `new_pickup`, the script loads an existing experiment object and updates it based on the parsed arguments. This allows for running simulations using pre-existing data.

2. **Experiment Initialization**:  
   If the `emodstep` is not pickup, an experiment object is created, and its attributes are initialized. This includes loading calibration parameters if specified.

3. **Scenario Configuration**:  
   Users can specify simulation parameters using a CSV file. The script reads the specified row and updates the experiment object with those parameters.

4. **Dynamic EIR Configuration**:  
   The script configures entomological inputs, allowing for seasonal variations if selected.

5. **Simulation Time Parameters**:  
   The script sets up the duration of the simulation based on user-defined parameters.


## Execution

To execute the script, run it directly from the command line.  
The script will:  
- Validate input parameters.  
- Create directories for storing simulation results.  
- Set up the simulation environment.  
- Submit jobs for running EMOD, malariasimulation, or OpenMalaria as specified in the experiment configuration.  




## Custom Functions Overview  
For further details on specific functions, refer to the relevant documentation within the imported modules.

### `parse_launch_args()`  
This function retrieves command-line arguments for the simulation setup. These arguments include settings for the simulation directory, models to run, and specific configurations like `emodstep`, `suite`, and `expname`.

### `pickle.load(file)`  
This function loads the previously saved experiment object (`exp.obj`) from the specified directory. This is used when the `emodstep` is set to `pickup` or `new_pickup`, allowing the script to continue a simulation from a saved state.

### `get_intervention_params(exp)`  
This function retrieves and configures intervention parameters for the experiment. It ensures that the parameters are updated correctly, especially between burn-in and pickup phases. This function is called for both pickup and new pickup scenarios.

### `LoadExperiment(args, manifest)`  
  This function initializes a new Experiment object, setting its attributes based on the parsed arguments and the manifest. It is called if the `emodstep` is not pickup, indicating a new simulation.

### `get_seasonal_eir(exp)`  
This function configures the seasonal entomological inoculation rate (EIR) if selected. It allows for dynamic adjustments based on seasonality, enhancing the realism of the simulation.

### `get_param_from_dataframe(exp_scen_df, col)`  
This function retrieves specific parameters from the scenario CSV file for the current simulation run. It updates the Experiment object with user-defined parameters from the CSV.

### `make_dirs(exp)`  
This function creates necessary directories for storing simulation results. It ensures that all required directories are set up before the simulation begins.

### `get_simulation_time_params(exp)`  
  This function sets the simulation duration, including start and end times. It prepares the timing parameters essential for running the simulation.

### `check_exp_inputs(exp)`  
This function validates all defined input parameters to ensure they are valid and compatible for the simulation. It raises errors if any issues are found.

### `create_scenarios_csv(exp, exp.sweep_list)`  
This function generates a DataFrame containing scenarios based on the parameters specified in `sweep_list`. It prepares for the various experimental scenarios to be executed during the simulation.

### `save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])`  
This function saves the experiment scenarios to CSV files in the specified directories, ensuring that all scenario configurations are recorded for future reference.

### `create_simsetup_csv(exp)`  
This function writes out the simulation setup required for running the malaria simulation. It prepares the necessary configuration files for the simulation engines.

### `submit_run_EMOD(exp, scen_df)`  
This function submits the EMOD simulation job to the SLURM job scheduler. It includes configurations for job management, such as memory allocation and job partition.

### `submit_run_malariasimulation(exp)`  
This function submits the malariasimulation job to the SLURM scheduler if included in the models to run. It prepares the job for execution.

### `submit_run_OpenMalaria(exp, scen_df)`  
This function submits the OpenMalaria simulation job, creating the necessary XML files for the simulation engine based on the experiment setup.

### `submit_run_plotters(exp)`  
This function submits jobs for generating plots after the main simulations have run. It ensures that visualization of results is scheduled appropriately.


