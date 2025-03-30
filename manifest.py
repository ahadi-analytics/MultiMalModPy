import os

# This is a user-modifiable Python file designed to customize input file and directory settings.
openmalaria_version = 46
emod_build = 220405

# Select cluster name
hpc = 'NUCLUSTER'
#hpc = 'SCICORE'
selected_platform = 'SLURM_LOCAL'
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# ----------------------------- EMOD generic settings start -----------------------------
# Location of the file containing AssetCollection id for the dtk sif (singularity image)
sif_id = os.path.join(os.pardir, 'dtk_sif.id')

# Create 'Assets' directory or change to a path you prefer. idmtools will upload files found here.
assets_input_dir = "Assets"
plugins_folder = "download/reporter_plugins"

# This is where your inputs are located
input_dir = os.path.join(ROOT_DIR, "EMOD/inputs")

# The script is going to use this to store the downloaded schema file. Create 'download' directory or change to your preferred (existing) location.
schema_file = os.path.join(os.path.expanduser('~'), "download/schema.json")
# The script is going to use this to store the downloaded Eradication binary. Create 'download' directory or change to your preferred (existing) location.
eradication_path = os.path.join(os.path.expanduser('~'), "download/Eradication")
# ----------------------------- EMOD generic settings end -----------------------------
if os.name != 'posix':
    hpc ='LOCAL'
    print("Running the framework locally. Note: Local execution is supported only for OpenMalaria and malariasimulation.")

# ----------------------------- Framework and cluster specific settings start -----------------------------
# job_directory is where your simulations and outputs will be stored
# SIF_PATH is the path to the sif image used to run EMOD
# OPENMALARIA_PATH is the location of the OpenMalaria dependencies (xsd schema, densities.csv, ...)
# openmalaria_input_path is location of OpenMalaria input files, scaffolds specific to project

# ----------------------------- User-defined input -----------------------------
if hpc == 'NUCLUSTER':
    sh_hpc_config = {'A': 'b1139', 'p': 'b1139', 'em_modules': 'singularity', 'buyin': True}
    projdir = os.path.join('/projects/b1139/emod-om/')

    SIF_PATH = "--bind /projects /projects/b1139/images/dtk_run_rocky_py39.sif"
    if openmalaria_version == 43:
        OPENMALARIA_PATH = "/projects/b1139/OpenMalaria/om_v43/"
    elif openmalaria_version == 46:
        OPENMALARIA_PATH = "/projects/b1139/OpenMalaria/om_v46/"
    else:
        raise ValueError(f'{openmalaria_version} not a valid OpenMalaria version, available versions: 43, 46')
    OPENMALARIA_venv = f'\n\nmodule use {OPENMALARIA_PATH}/modules/ \nmodule load openmalaria\n'

    EMOD_venv_modules = os.path.join('\n\nml singularity/3.8.1 \nml python/3.9.16')
    EMOD_venv_path = os.path.join('\nsource /projects/b1139/environments/mmmpy_dev/bin/activate\n')
    EMOD_venv = f'{EMOD_venv_modules} {EMOD_venv_path}'

elif hpc == 'SCICORE':
    sh_hpc_config = {'A': 'penny', 'p': 'scicore', 'em_modules': '', 'buyin': True}
    SIF_PATH = "/scicore/home/scicore/cavelan/git/emodpy/dtk_run_rocky_py39.sif"
    OPENMALARIA_PATH = "/scicore/home/penny/GROUP/OpenMalaria/OM_schema46/"

    if openmalaria_version == 43:
        OPENMALARIA_venv = '\n\nmodule load OpenMalaria/43.1-iomkl-2019.01\n'
    elif openmalaria_version == 46:
        OPENMALARIA_venv = '\n\nmodule load OpenMalaria/46.0-iomkl-2019.01\n'
    else:
        raise ValueError(f'{openmalaria_version} not a valid OpenMalaria version, available versions: 43, 46')

    EMOD_venv_modules = os.path.join('\n\nml Python/3.9.6-GCCcore-11.2.0-bare')
    #source /scicore/home/scicore/cavelan/git/MultiMalModPy/emodenv/bin/activate
    EMOD_venv_path = os.path.join(f'\nsource {ROOT_DIR}/emodenv/bin/activate\n')
    EMOD_venv = f'{EMOD_venv_modules} {EMOD_venv_path}'

elif hpc == 'LOCAL':
    sh_hpc_config = {'A': 'Local', 'p': None, 'em_modules': None, 'buyin': None}
    projdir = os.path.join(ROOT_DIR, 'simulations_local')
    os.makedirs(projdir, exist_ok=True)

    SIF_PATH = ""
    OPENMALARIA_venv = ''
    r_local = "C:/Program Files/R/R-4.2.3/bin"

    if openmalaria_version == 43:
        OPENMALARIA_PATH = os.path.join(ROOT_DIR, 'dependencies/OpenMalaria/om_v43')
    elif openmalaria_version == 46:
        OPENMALARIA_PATH = os.path.join(ROOT_DIR, 'dependencies/OpenMalaria/om_v46')
    else:
        raise ValueError(f'{openmalaria_version} not a valid OpenMalaria version, available versions: 43, 46')

    EMOD_venv_modules = os.path.join('')
    EMOD_venv_path = os.path.join(f'\nsource {ROOT_DIR}/dependencies/mmmpy_venv/bin/activate\n')
    EMOD_venv = f'{EMOD_venv_modules} {EMOD_venv_path}'

else:
    raise ValueError('HPC specification not available')

## ----------------------------- User-defind input end -----------------------------

emod_input_path = os.path.normpath(os.path.join(ROOT_DIR, 'EMOD/inputs'))
openmalaria_input_path = os.path.normpath(os.path.join(ROOT_DIR, 'OpenMalaria/'))
malariasimulation_input_path = os.path.normpath(os.path.join(ROOT_DIR, 'malariasimulation/'))
interp_path = os.path.normpath(os.path.join(ROOT_DIR, 'target_calibration/'))

job_directory = os.path.normpath(os.path.join(projdir, 'experiments'))
output_directory = os.path.normpath(os.path.join(projdir, 'simulation_outputs'))
interp_csv = 'interpolation_data.csv'
os.makedirs(job_directory, exist_ok=True)
# ----------------------------- Framework and cluster specific settings end -----------------------------
