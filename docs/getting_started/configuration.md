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

### MultiMalModPy universal configurations

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

    emod_input_path = os.path.join(os.path.expanduser('~'), 'MultiMalModPy/EMOD/inputs')
    openmalaria_input_path = os.path.join(os.path.expanduser('~'), 'MultiMalModPy/OpenMalaria/')
    malariasimulation_input_path = os.path.join(os.path.expanduser('~'), 'MultiMalModPy/malariasimulation/')
    interp_path = os.path.join(os.path.expanduser('~'), 'MultiMalModPy/target_calibration/')
    interp_csv = 'interpolation_data.csv'
```


## Overview of modifiable parameters

Parameter specifications for framework and simulation setup:

- [ ] **Simulation experiment name, infrastructure, directories and models to run**
    - `mem_increase_factor`: scaling factor on default memory requested, which usually can be left at 1 for test
      simulation, but may have to be
      4 or 8 for larger simulations. The default memory requested also differs for the slurm job submission to run
      versus to analyze a simulation.
    - `custom_subdir`:  If `None`, no i.e. user specific subdir created, default `os.getlogin()`
    - `SUITEname`: overall subdir to declare a group of simulations to run, default is `f'{entomology_mode}EIR'`
    - `exp_name`: name of
      simulation experiment to run, default is `f'sim_{dt.now().strftime("%Y_%m_%d_%H_%M_%S")}'`, whereas a more
      meaningful name might be choosen for simulation experiments to use outputs for some result description rather than
      just for testing.
    - `models_to_run`: Name of models to run (case-sensitive), options are **EMOD** , **OpenMalaria** and/or  **MalSim**
    - `om_scaffold`: name of **OpenMalaria** input XML to use
    - `MalSim_script`: name of **malariasimulation** R script to use

- [ ] **Population size, agebins and seeds**
    - `pop_size`: number of individuals to simulate for human population, default for testing `1000`, which should not
      be used for actual
      simulations to generate results
    - `agebins`: age groups to monitor (select finest age groups required, can be further combined in postprocessing)
    - `age_groups_aggregates`: Age groups to aggregate to in postprocessing
    - `num_seeds_burnin`: EMOD specific (even if not declared as such), number of seeds to run for burnin if run
      separately
    - `num_seeds`: number of
      seeds to run for simulation (applies to all models)

- [ ] **Simulation time and reporting intervals**
    - `start_year`: Calendar year at which monitoring period should start (after burnin)
    - `end_year`: Calendar year at which monitoring period should end
    - `burnin`: Number of years to run prior to monitoring period (from these the simulation start year will be
      calculated) - 80 years is recommended for all models to establish immunity in the simulated population
    - `om_survey_step`: survey intervals for which outcomes are reported in OpenMalaria, default is `30d`. Note, in
      EMOD, monthly reports are per default included in monitored simulation period.
    - `emod_step`: EMOD allows to run burnin separate from the monitoring period (here equivalent to `pickup`),
      if `None` both similation times
      are run together, which can be computational and time-wise too extensive when running long burnin, large
      populations and high EIRs.
    - `emod_serialized_id`: ID of EMOD burnin experiment to pickup from, if `emod_step ='pickup'`

- [ ] **Transmission intensity and seasonality**
    - `entomology_mode`:    select whether to run with vectors (`dynamic`) or without (`forced`)
    - `seasonality`: name of pre-defined transmission seasonality profile to simulate (current options
      are `["perennial", "seasonal"]`)
    - `eir`: annual input EIR (or equivalent, depending on model and entomology mode)


- [ ] **Case management parameters**
    - `cm_start`: do not change, can be removed, case managament would always start on day 1, except of having multiple
      intervention
      deployments to simulate coverage increase over time (not applicable here)
    - `cm_clinical`: clinical case management coverage
    - `cm_severe`: do not change, will be adapted depending on clinical case management, but to be at least 48%
    - `detectionLimit`: detection limit for parasites per micoliter blood for detection of prevalent malaria infections

- [ ] **CC step parameters**
    - `carrying_capacity_step`: Defined the step change from to in a list,
      example `['10%-25%', '10%-50%', '25%-10%', '25%-50%', '50%-10%', '50%-25%']`
    - `eir_scalar_emod`: defines the scalar for each carrying_capacity_step defined that will achieve the desired step
      change for EMOD
    - `eir_scalar_malsim`: defines the scalar for each carrying_capacity_step defined that will achieve the desired step
      change for malariasimulation
    - `eir_scalar_om`: defines the scalar for each carrying_capacity_step defined that will achieve the desired step
      change for OpenMalaria

- [ ] **Simulation experiment setup of sweeps and postprocessing**
    - `sweep_list`: List of parameter names that together uniquely identify a simulation scenario (and will be written
      into `scenarios.csv`)
    - `plots_to_run`: List of types of plots to run automatically after the simulations finished



