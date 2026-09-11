import os

# This is a user-modifiable Python file designed to customize input file and directory settings.
openmalaria_version = 46
emod_build = 220405
SUPPORTED_OM_VERSIONS = {43, 46}

# Select cluster name
hpc = 'NUCLUSTER'
#hpc = 'SCICORE'
selected_platform = 'SLURM_LOCAL'
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

# Detect environment
IS_WINDOWS = os.name == "nt"
IS_DOCKER = os.path.exists("/.dockerenv")
IS_HPC = os.path.exists("/hpc") and not IS_DOCKER

# Initialize
use_container = False
platform = 'SLURM_LOCAL'

if IS_WINDOWS:
    hpc = "LOCAL"
    selected_platform = 'Container'
    use_container = False

## Currently not supported on HPC
elif IS_DOCKER:
    hpc = "LOCAL"
    selected_platform = "Container"
    use_container = True

elif IS_HPC:
    hpc = "NUCLUSTER"
    selected_platform = "SLURM_LOCAL"
    use_container = False

else:
    hpc = "LOCAL"
    selected_platform = "Container"
    use_container = False

platform  = selected_platform
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


# ----------------------------- Framework and cluster specific settings start -----------------------------
# job_directory is where your simulations and outputs will be stored
# SIF_PATH is the path to the sif image used to run EMOD
# OPENMALARIA_PATH is the location of the OpenMalaria dependencies (xsd schema, densities.csv, ...)
# openmalaria_input_path is location of OpenMalaria input files, scaffolds specific to project

if openmalaria_version in SUPPORTED_OM_VERSIONS:
    OPENMALARIA_PATH = os.path.join(ROOT_DIR, f'dependencies/OpenMalaria/om_v{openmalaria_version}')
else:
    raise ValueError(
        f"OpenMalaria version '{openmalaria_version}' is not supported. "
        f"Available versions: {sorted(SUPPORTED_OM_VERSIONS)}"
    )

# ----------------------------- User-defined input -----------------------------
if hpc == 'NUCLUSTER':
    sh_hpc_config = {'A': 'b1139', 'p': 'b1139', 'em_modules': 'singularity', 'buyin': True}
    #sh_hpc_config = {'A': 'p32714', 'p':'normal', 'em_modules': 'singularity', 'buyin': True}
    projdir = os.path.join('/gpfs/projects/b1139/emod-om/')

    SIF_PATH = "--bind /gpfs/projects /gpfs/projects/b1139/images/dtk_run_rocky_py39.sif"
    OPENMALARIA_PATH = os.path.join(f'/gpfs/projects/b1139/OpenMalaria/om_v{openmalaria_version}/')
    OPENMALARIA_venv = f'\n\nmodule use {OPENMALARIA_PATH}modules/ \nmodule load openmalaria\n'

    EMOD_venv_modules = os.path.join('\n\nml singularity/3.8.1 \nml python/3.9.16')
    EMOD_venv_path = os.path.join('\nsource /gpfs/projects/b1139/environments/mmmpy_dev/bin/activate\n')
    EMOD_venv = f'{EMOD_venv_modules} {EMOD_venv_path}'
    
    ## When running inside a container
    image_path = "/gpfs/projects/b1139/emod-om/emodpy4.1-OM46-R4.4.1.sif"
    image_venv_name = "emodpy39"
    OPENMALARIA_venv_container = f'/openmalaria-schema-46.0/build/'
    EMOD_venv_container = f'source /opt/envs/{image_venv_name}/bin/activate'
    bind_path = '/gpfs/projects:/projects'

elif hpc == 'SCICORE':
    sh_hpc_config = {'A': 'penny', 'p': 'scicore', 'em_modules': '', 'buyin': True}
    projdir = os.path.join('/scicore/home/scicore/cavelan/git/model-characterization')

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
    
    ## When running inside a container
    image_path = ''
    image_venv_name = ''
    OPENMALARIA_venv_container = ''
    EMOD_venv_container =''
    bind_path = ''

elif hpc == 'LOCAL':
    sh_hpc_config = {'A': 'Local', 'p': None, 'em_modules': [], 'buyin': None}
    projdir = os.path.join(ROOT_DIR, 'simulations_local')
    os.makedirs(projdir, exist_ok=True)
    selected_platform = 'Container'

    SIF_PATH = ""
    OPENMALARIA_venv = ''
    r_local = "C:/Program Files/R/R-4.2.3/bin"
    OPENMALARIA_venv_container = f'/openmalaria-schema-{openmalaria_version}.0/build/'

    EMOD_venv_modules = os.path.join('')
    EMOD_venv_path = os.path.join(f'\nsource {ROOT_DIR}/dependencies/mmmpy_venv/bin/activate\n')
    EMOD_venv = f'{EMOD_venv_modules} {EMOD_venv_path}'
    
    image_path = 'mmmpy_local:rocky8'
    image_venv_name = ''
    EMOD_venv_container ='source /opt/envs/mmmpy_local/bin/activate'
    bind_path = ROOT_DIR

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

if use_container:
    ROOT_DIR_local = os.path.dirname(ROOT_DIR)
    OPENMALARIA_PATH = os.path.join(ROOT_DIR, f'dependencies/OpenMalaria/om_v{openmalaria_version}')
    if IS_DOCKER:
        OPENMALARIA_PATH = os.path.join( f'/openmalaria-schema-{openmalaria_version}.0/unittest/')
    # Required only when running inside docker, locally
    OPENMALARIA_venv = OPENMALARIA_venv_container
    EMOD_venv = EMOD_venv_container
    
# ----------------------------- Framework and cluster specific settings end -----------------------------
