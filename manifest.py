import os

# This is a user-modifiable Python file designed to be a set of simple input file and directory settings that you can choose and change.
om_version = 43
emod_build = 220405

# Select cluster name
hpc = 'NUCLUSTER'
#hpc = 'SCICORE'
selected_platform = 'SLURM_LOCAL'

# the location of the file containing AssetCollection id for the dtk sif (singularity image)
sif_id = os.path.join(os.pardir, 'dtk_sif.id')

# The script is going to use this to store the downloaded schema file. Create 'download' directory or change to your preferred (existing) location.
schema_file = os.path.join(os.path.expanduser('~'), "download/schema.json")

# The script is going to use this to store the downloaded Eradication binary. Create 'download' directory or change to your preferred (existing) location.
eradication_path = os.path.join(os.path.expanduser('~'), "download/Eradication")

# Create 'Assets' directory or change to a path you prefer. idmtools will upload files found here.
assets_input_dir = "Assets"
plugins_folder = "download/reporter_plugins"

# This is where your inputs are located
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
input_dir = os.path.join(ROOT_DIR, "EMOD/inputs")

# ep4_path="python_scripts"
# requirements = "./requirements.txt"

# job_directory is where your simulations and outputs will be stored
# SIF_PATH is the path to the sif image used to run EMOD
# OM_PATH is the location of the OpenMalaria dependencies (xsd schema, densities.csv, ...)
# om_input_path is location of OpenMalaria input files, scaffolds specific to project
if hpc == 'NUCLUSTER':
    sh_hpc_config = {'A': 'b1139', 'p': 'b1139', 'em_modules': 'singularity', 'buyin': True}
    projdir = os.path.join('/projects/b1139/emod-om/')
    job_directory = os.path.join(projdir, 'experiments')
    output_directory = os.path.join(projdir, 'simulation_outputs')
    SIF_PATH = "--bind /projects /projects/b1139/images/dtk_run_rocky_py39.sif"
    if om_version == 43:
        OM_PATH = "/projects/b1139/OpenMalaria/"
    elif om_version == 45:
        OM_PATH = "/projects/b1139/OpenMalaria/om_v45/"
    else:
        raise ValueError(f'{om_version} not a valid OpenMalaria version, available versions: 43, 45')
    om_input_path = '/projects/b1139/emod-om/model-characterization/OpenMalaria/'
    if os.name != 'posix':
        output_directory = os.path.join(os.environ['USERPROFILE'],
                                        'NU Malaria Modeling Dropbox/projects/EMOD_OM/simulation_outputs')
        print(f"Setting output_directory for local use: {output_directory}")
elif hpc == 'SCICORE':
    sh_hpc_config = {'A': 'penny', 'p': 'scicore', 'em_modules': '', 'buyin': True}
    projdir = os.path.join('/scicore/home/scicore/cavelan/git/model-characterization')
    job_directory = os.path.join(projdir, 'experiments')
    SIF_PATH = "/scicore/home/scicore/cavelan/git/emodpy/dtk_run_rocky_py39.sif"
    OM_PATH = "/scicore/home/penny/GROUP/OpenMalaria/OM_schema43/"
    om_input_path = '/scicore/home/scicore/cavelan/git/model-characterization/OpenMalaria/'
    output_directory = os.path.join(projdir, 'simulation_outputs')
else:
    job_directory = os.path.join(os.path.expanduser('~'), 'experiments/')
    SIF_PATH = ""

os.makedirs(job_directory, exist_ok=True)
