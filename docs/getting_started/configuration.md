# First time user configurations (manifest.py)

MultiMalModPy is designed to run simulations on a Linux-based high-performance computing (HPC) cluster and is not
optimized for local execution (test runs only).
Before running your first simulation, open and edit the `manifest.py` file to configure HPC specifications and default
directories.
This script defines input file locations and computational settings for running all of the models included in
MultiMalModPy.
Modify these parameters to match your HPC environment and simulation requirements.

## Directories and dependencies

The `manifest.py` facilitates the setup for running epidemiological simulations by allowing users to customize file
paths and configurations, making it adaptable to different computing environments.

1. Adjust parameter values to fit your system configuration and workflow preferences.
2. Ensure that necessary directories (i.e. `experiments`, and `simulation_output`) are created if they do not exist.

<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>📝 NOTE:</em></strong> 
 Modify HPC settings and file paths to align with your specific computational resources..
</div>  

## Configuration parameters

### MultiMalModPy universel configurations

| Parameter           | Description                                         |
|---------------------|-----------------------------------------------------|
| `hpc`               | Selected cluster name (e.g., NUCLUSTER or SCICORE). |
| `selected_platform` | Selected computing platform for job scheduling.     |
| `ROOT_DIR`          | Root directory of the current script's location.    |
| `input_dir`         | Directory where input files are located.            |
| `job_directory`     | Storage location for simulations and outputs.       |
| `interp_path`       | Path for target calibration data.                   |
| `interp_csv`        | Filename for the interpolation data CSV file.       |

### EMOD-specific configurations

| Parameter          | Description                                                                        |
|--------------------|------------------------------------------------------------------------------------|
| `emod_build`       | EMOD build version.                                                                |
| `sif_id`           | Location of the file containing AssetCollection id for the dtk sif (use defaults). |
| `schema_file`      | Location to store the downloaded schema file.                                      |
| `eradication_path` | Location to store the downloaded Eradication binary.                               |
| `assets_input_dir` | Directory for input assets (uploaded via idmtools).                                |
| `plugins_folder`   | Path to the directory for reporter plugins (use defaults).                         |
| `SIF_PATH`         | Path to the Singularity Image (SIF) used for EMOD.                                 |
| `EMOD_venv`        | Name of the Python virtual environment including EMOD to activate.                 |
| `emod_input_path`  | Path to EMOD-specific input files (fixed, relative to repository root).            |

### OpenMalaria-specific configurations

| Parameter                | Description                                                           |
|--------------------------|-----------------------------------------------------------------------|
| `openmalaria_version`    | Version of OpenMalaria to be used.                                    |
| `OPENMALARIA_PATH`       | Path to OpenMalaria dependencies.                                     |
| `openmalaria_input_path` | Path to OpenMalaria input files (fixed, relative to repository root). |

### malariasimulation-specific configurations

| Parameter                     | Description                                                                  |
|-------------------------------|------------------------------------------------------------------------------|
| `malariasimulation_input_path` | Path to Malaria Simulation input files (fixed, relative to repository root). |
| `r_local` | Path to R binary, only for local run.                                        |


## Example HPC

``` python 
if hpc == 'NUCLUSTER':
    sh_hpc_config = {'A': 'b1139', 'p': 'b1139', 'em_modules': 'singularity', 'buyin': True}
    projdir = os.path.join('/projects/b1139/emod-om/')
    job_directory = os.path.join(projdir, 'experiments')
    output_directory = os.path.join(projdir, 'simulation_outputs')
    
    SIF_PATH = "--bind /projects /projects/b1139/images/dtk_run_rocky_py39.sif"
    if openmalaria_version == 43:
        OPENMALARIA_PATH = "/projects/b1139/OpenMalaria/om_v43/"
    elif openmalaria_version == 46:
        OPENMALARIA_PATH = "/projects/b1139/OpenMalaria/om_v46/"
    else:
        raise ValueError(f'{openmalaria_version} not a valid OpenMalaria version, available versions: 43, 46')
    OPENMALARIA_venv = f'\n\nmodule use {OPENMALARIA_PATH}/modules/ \nmodule load openmalaria\n'

    EMOD_venv_modules = os.path.join('\n\nml singularity/3.8.1 \nml python/3.8.4')
    EMOD_venv_path = os.path.join('\nsource /projects/b1139/environments/emodpy_om/bin/activate\n')
    EMOD_venv = f'{EMOD_venv_modules} {EMOD_venv_path}'

    emod_input_path = os.path.join(os.path.expanduser('~'), 'model-characterization/EMOD/inputs')
    openmalaria_input_path = os.path.join(os.path.expanduser('~'), 'model-characterization/OpenMalaria/')
    malariasimulation_input_path = os.path.join(os.path.expanduser('~'), 'model-characterization/malariasimulation/')
    interp_path = os.path.join(os.path.expanduser('~'), 'model-characterization/target_calibration/')
    interp_csv = 'interpolation_data.csv'
```


