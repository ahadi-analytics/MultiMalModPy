# Configuration


When running for the first time, open and edit `manifest.py` to enter HPC specification and default directories

- `hpc`: name of cluster (str)
- `sh_hpc_config`: specification for slurm submission (dict),
  example `sh_hpc_config={'A': 'b1139', 'p': 'b1139', 'em_modules': 'singularity', 'buyin': True}`
- `projdir`: path to directory where to store experiment and simulation outputs
- `job_directory`: path to directory where to store experiments,
  i.e. `job_directory = os.path.join(projdir, 'experiments')`
- `SIF_PATH`: path to EMOD emodpy image (see EMOD installtion)
- `OM_PATH`: path to OpenMalaria requirements to run model (see OpenMalaria installation)
- `om_input_path`: path to OpenMalaria sub-directory of this git repository cloned on HPC
- `output_directory`: path to directory where to store simulation resultr (summarized outputs),
  i.e. `output_directory = os.path.join(projdir, 'simulation_outputs')`
