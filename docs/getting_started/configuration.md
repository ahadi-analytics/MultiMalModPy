# Configuration

Simulations are assumed to run on a Linux based high performance cluster (HPC), the framework is not designed for  running simulations locally

When running for the first time, open and edit `manifest.py` to enter HPC specification and default directories

This Python script is designed for configuring input file and directory settings for running EMOD (Epidemiological Modeling Software). Users can modify settings to tailor the environment to their specific computational platform and requirements.

## Configuration parameters

| Parameter                     | Description                                                                                          | Default Value                            |
|-------------------------------|------------------------------------------------------------------------------------------------------|------------------------------------------|
| `openmalaria_version`         | Version of OpenMalaria to be used.                                                                  | 46                                       |
| `emod_build`                  | Build version of EMOD.                                                                               | 220405                                   |
| `hpc`                         | Selected cluster name (e.g., NUCLUSTER or SCICORE).                                                | `NUCLUSTER`                              |
| `selected_platform`           | Selected computing platform for job scheduling.                                                     | `SLURM_LOCAL`                            |
| `ROOT_DIR`                    | Root directory of the current script's location.                                                    | (automatically determined)               |
| `sif_id`                      | Path to the file containing the AssetCollection id for the DTK SIF (Singularity Image).            | `../dtk_sif.id`                         |
| `schema_file`                 | Location to store the downloaded schema file.                                                      | `~/download/schema.json`                |
| `eradication_path`            | Location to store the downloaded Eradication binary.                                               | `~/download/Eradication`                 |
| `assets_input_dir`           | Directory for input assets (uploads via idmtools).                                                 | `Assets`                                 |
| `plugins_folder`              | Path to the directory for reporter plugins.                                                         | `download/reporter_plugins`              |
| `input_dir`                   | Directory where input files are located.                                                            | `EMOD/inputs`                            |
| `job_directory`               | Directory for storing simulations and outputs.                                                      | `/projects/b1139/emod-om/experiments` (NUCLUSTER) or `/scicore/home/scicore/cavelan/git/model-characterization/experiments` (SCICORE) |
| `SIF_PATH`                    | Path to the SIF image used to run EMOD.                                                             | Varies by HPC selection                  |
| `OPENMALARIA_PATH`            | Path to OpenMalaria dependencies based on the selected version.                                    | Varies by version and HPC selection      |
| `EMOD_venv`                   | Commands for activating the EMOD virtual environment.                                               | Varies by HPC selection                  |
| `emod_input_path`             | Path to EMOD input files specific to the project.                                                  | Varies by HPC selection                  |
| `openmalaria_input_path`      | Path to OpenMalaria input files.                                                                     | Varies by HPC selection                  |
| `malariasimulation_input_path` | Path to Malaria Simulation input files.                                                             | Varies by HPC selection                  |
| `interp_path`                 | Path for target calibration data.                                                                    | Varies by HPC selection                  |
| `interp_csv`                  | Filename for the interpolation data CSV file.                                                       | `interpolation_data.csv`                 |

## Usage

1. Modify the values of the parameters to match your system configuration and preferences.
2. Ensure that necessary directories are created if they do not exist; the script automatically creates the `job_directory`.
3. The script will raise a `ValueError` if an unsupported OpenMalaria version is specified or if the current framework does not allow local runs.
4. Make sure to adjust the HPC settings and paths based on your specific computational resources.

This script facilitates the setup for running epidemiological simulations by allowing users to customize file paths and configurations, making it adaptable to different computing environments.

