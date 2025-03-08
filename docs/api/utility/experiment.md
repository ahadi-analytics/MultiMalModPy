# experiment.py 


## Overview

The `LoadExperiment` class is responsible for initializing and managing simulation settings for 
different experimental runs based on user-defined arguments and a manifest configuration. 
It facilitates the setup for various models including EMOD and OpenMalaria.
The constructor initializes the LoadExperiment object with basic settings, user configurations,
and manifest-related attributes.
It also configures the run mode and parameters to vary based on the provided arguments.

### Import Statements

``` 
import manifest
from utility.helper import *
import warnings
``` 

### Methods 
1. configure_run_mode()   
Configures settings based on the specified run mode (calibrun, test, productionrun, or simulation).  

2. configure_calibration() 
Configures calibration settings if the emod_calib_params attribute is enabled.  


3. update(**kwargs)  
Updates the attributes of the LoadExperiment instance with new values provided as keyword arguments. 


## Attributes
- **`SUITEname`**: The name of the suite for the experiment.   
- **`exp_name`**: Name of the experiment.  
- **`emod_step`**: Specifies the EMOD step.  
- **`models_to_run`**: List of models to run.  
- **`intervention_list`**: List of interventions to be applied.  
- **`run_mode`**: Specifies the run mode of the experiment.  
- **`emod_calib_params`**: Calibration parameters for EMOD.  
- **`malariasimulation_parameter_variation`**: Indicates whether parameter variation for malariasimulation is enabled.  
- **`output_typ`e**: Type of output expected from the simulation.  
- **`user`**: User-related settings.  
- **`custom_subdir`**: Subdirectory for user-specific data.  
- **`hpc`**: High-Performance Computing settings from the manifest.  
- **`job_directory_manifest`**: Directory for job outputs as specified in the manifest.  
- **`output_directory_manifest`**: Directory for experiment outputs as specified in the manifest.  
- **`interp_path`**: Path for interpolation data.  
- **`interp_csv`**: Interpolation CSV file name.  
- **`burnin_directory`**: Directory for burn-in outputs (default is None).

## Example

```
import argparse
from manifest import Manifest
from load_experiment import LoadExperiment

# Example of argument parsing
parser = argparse.ArgumentParser(description='Load Experiment Settings')
parser.add_argument('--suite', required=True, help='Suite name for the experiment')
parser.add_argument('--expname', required=True, help='Name of the experiment')
# Add additional arguments as necessary
args = parser.parse_args()

# Load manifest
manifest = Manifest()  # Initialize the manifest with appropriate configurations

# Create LoadExperiment object
experiment = LoadExperiment(args, manifest)

# Accessing attributes
print(experiment.SUITEname)
print(experiment.output_type)

```