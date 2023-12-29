import logging
from idmtools.entities.experiment import Experiment
from datetime import datetime as dt
import manifest
from idmtools.core.platform_factory import Platform
from helper import *
from EMOD.utils import get_scendf_burnin
import os
import argparse

# Setting up variables and flags for the simulation
log = logging.getLogger(__name__)
loaded_attr = set(dir())  # Non experiiment specific objects to be excluded from exp.obj

# Flag to select whether to run with (dynamic) or without vector model (forced)
entomology_mode = 'dynamic'  # dynamic, forced
seasonality = ["seasonal"]  # ["perennial", "seasonal"]  #"Current framework support only 1 seasonality patten per experiment"
mem_increase_factor = 3.0  # scaling factor on default memory requested

# Name and location of simulation, a SUITE may contain multiple experiments that belong to a shared objective
user = os.environ.get('USER')
custom_subdir = user  # If None, no subdir created


# EMOD flags for how to run simulations (in one run or separated into burnin + pickup)
# In EMOD, running 'burnin' and 'pickup' time in one simulation (Default) can take very long in EMOD depending on burnin time and population size.
# emod_step expects a string, either None, 'burnin' or 'pickup'. Default None will run 'burnin' and 'pickup' time in one simulation.


def parse_launch_args():
    parser = argparse.ArgumentParser(description="Description of your script.")

    # Define command-line arguments with default values
    parser.add_argument("-d", "--directory",
                        type=str,
                        required=False,
                        help="dummy, not required but automatically generated in submission script")
    parser.add_argument('--suite',
                        type=str,
                        default=f'test_sims_{dt.now().strftime("%Y%m%d")}',
                        help='Description of SUITEname')
    parser.add_argument('--expname',
                        type=str,
                        default=f'sims_{entomology_mode}_{seasonality}_{dt.now().strftime("%H_%M_%S")}',
                        help='Description of exp_name')
    parser.add_argument('--emodstep',
                        type=str,
                        default=None,
                        help='Description of emod_step')
    parser.add_argument('--serializedid',
                        type=str,
                        default='',
                        help='Description of emod_serialized_id')
    parser.add_argument('--models',
                        nargs='+',
                        default=['EMOD', 'OpenMalaria', 'MalSim'],
                        help='Description of models_to_run')

    return parser.parse_args()


# Retrieve parsed arguments
args = parse_launch_args()

# Access arguments directly
SUITEname = args.suite
exp_name = args.expname
emod_step = args.emodstep
emod_serialized_id = args.serializedid
models_to_run = args.models

# Specify OpenMalaria XML and survey step
om_scaffold = "R0000GA"  # defining which OpenMalaria XML scaffold to use
om_survey_step = '30d'

# Specify MalSim simulation setup, interventions etc to run
MalSim_script = 'malsim_benchmarking_exercise.R'
MalSim_run_burnin = True

# Define simulation population and seeds
pop_size = 1000  # 1000 for testing
agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # Note, keep these to ensure smooth postprocessing

num_seeds_burnin = 1  # used only if emod_step=='burnin', for EMOD
num_seeds = 5  # suggested minimum 3, in production 5-10
start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
end_year = 2005  # end of pickup and monitoring period
burnin = 80  # Duration of burnin (pre-monitoring) period, should be 80 years to establish immunity in the population

# Simulation duration, start and end configuration
sim_start_year_em, monitoring_years, sim_dur_years = get_emod_time_param(start_year, end_year, burnin, models_to_run,
                                                                         emod_step)
sim_start_year_om = start_year - burnin
sim_start_year_ms = sim_start_year_om

if not MalSim_run_burnin:
    sim_start_year_ms = start_year

# Name of parameters to vary
sweep_list = ['eir', 'cm_clinical', 'seasonality']

# EMOD burn-in and pickup configuration
if emod_step == 'burnin' and 'EMOD' in models_to_run:
    print('Message: Running burnin for EMOD')
    exp_name = f'{exp_name}_burnin{burnin}'
    models_to_run_pickup = models_to_run  # Models to run in pickup
    models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
    num_seeds = num_seeds_burnin
    sweep_list = ['eir', 'cm_clinical', 'seasonality']  # If running fewer sweeps in past than in pickup to be set up
if emod_step != 'pickup':
    emod_serialized_id = ''

# Define case management start and coverage
# 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
cm_start = 1
cm_clinical = [0.0]  # [0, 0.2, 0.4, 0.6, 0.8, 1]  #[0.2029544]
cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15
detectionLimit = 40

# Transmission and seasonality configuration
# eir = [0.1,0.18,0.31,0.55,0.98,1.72,3.05,5.39,9.52,16.82,29.73,
# 52.36,92.85,164.09,290.00,512.52,905.79,1600.82,2829.15,5000.00] #np.logspace(-1,3.69897000434,20) This is for x_temp_larval
# eir = [0.1, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 22, 25,
# 30, 35, 40, 45, 50, 65, 70, 80, 90, 100, 120, 150, 200, 250, 500, 750, 1000] #Aurelien's suggested EIRS
eir = [1, 128, 256]

# Entomology mode: Dynamic EIR configuration if selected
season_daily, season_month, seasonal, perennial = get_seasonal_eir()

# Directory setup and analyzer scripts
suite_directory, job_directory, sim_out_dir = make_dirs(manifest, SUITEname, exp_name,
                                                        custom_subdir)  # we are currenlty only going to run one seasonality at a time
emod_analyzer = ['analyze_sim.py']
openmalaria_analyzer = ['analyze_sim.py']

# Creating an Experiment object and setting its attributes, saved as exp.obj
my_obj = set(dir()) - loaded_attr
exp = Experiment()
exp.my_obj = my_obj
exp.hpc = manifest.hpc
exp.sh_hpc_config = manifest.sh_hpc_config
exp.selected_platform = manifest.selected_platform
exp.om_version = manifest.om_version
exp.emod_build = manifest.emod_build
exp.om_path = manifest.OM_PATH
exp.om_input_path = manifest.om_input_path
exp.suite_directory = suite_directory
exp.job_directory = job_directory
exp.sim_out_dir = sim_out_dir
# exp.seasonal = seasonal
# exp.perennial = perennial

# Assigning attributes to the Experiment object and creating scenarios
for obj_name in my_obj:
    if hasattr(locals().get(obj_name), '__call__'):
        setattr(exp, obj_name, locals().get(obj_name))
    elif obj_name in locals():
        setattr(exp, obj_name, locals().get(obj_name))
    else:
        print(f"Object {obj_name} not found in the locals environment.")

# Check whether defined input parameter are all valid
check_exp_inputs(exp)  # TODO add more validity checks as needed

# Parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, sweep_list)
exp.nexps = len(scen_df) * num_seeds
exp.num_seeds = num_seeds  # needed so MalSim doesn't do additional jobs

# Set platform and associated values, such as the maximum number of jobs to run at one time
platform = Platform(manifest.selected_platform, job_directory=suite_directory,
                    mem_per_cpu=int(5000 * mem_increase_factor), partition=manifest.sh_hpc_config['p'],
                    time='03:00:00', account=manifest.sh_hpc_config['A'],
                    modules=[manifest.sh_hpc_config['em_modules']], max_running_jobs=300)  # mem_per_cpu default: 2048

if emod_step == 'pickup':
    scen_df = get_scendf_burnin(exp, emod_serialized_id, manifest, platform,
                                burnin)  # FIXME expand on it when additional parameter values to run in future
save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])
save_scen(rep_scen_df(scen_df), fname='scenarios_wseeds.csv', save_dirs=[exp.job_directory, exp.sim_out_dir])

# Write out simulation setup (required for MalSim)
create_simsetup_csv(exp)

# The emod_exp object helps transfer necessary emod inputs from launch_test.py to EMOD/utils.py
emod_exp = Experiment()
emod_exp.user = user
emod_exp.pop_size = pop_size
emod_exp.sim_dur_years = sim_dur_years
emod_exp.detectionLimit = detectionLimit
emod_exp.entomology_mode = entomology_mode
emod_exp.seasonality = seasonality
emod_exp.emod_step = emod_step
emod_exp.burnin = burnin
emod_exp.num_seeds = num_seeds
emod_exp.platform = platform
emod_exp.agebins = agebins
emod_exp.sim_start_year_em = sim_start_year_em
emod_exp.mem_increase_factor = mem_increase_factor

if __name__ == '__main__':

    print(f' --------| Running {exp_name} for {", ".join(models_to_run)}: {len(sweep_list)} '
          f'varying parameters: {", ".join(sweep_list)} |--------')

    # Submit EMOD simulation as SLURM job, including scheduled analyzer
    if 'EMOD' in models_to_run:
        import emod_malaria.bootstrap as dtk
        import pathlib

        dtk.setup(pathlib.Path(manifest.eradication_path).parent)
        from EMOD.utils import submit_run_EMOD

        emod_exp = submit_run_EMOD(exp, emod_exp, scen_df)

        if emod_step == 'burnin':
            exp_name_pickup = exp_name.replace(f'_burnin{burnin}', '')
            submit_run_pyscript(exp, pyscript='launch_test.py', shname='launch_pickup.sh',
                                custom_args=f"--suite {SUITEname} --expname {exp_name_pickup} "
                                            f"--emodstep pickup --serializedid {emod_exp.id} "
                                            f"--models {' '.join([m for m in models_to_run_pickup])} ",
                                job_id_EMOD='job_id_EMODanalyze', job='pickup_launch')

    # Submit OpenMalaria simulation as SLURM job, including scheduled analyzer
    if 'OpenMalaria' in models_to_run:
        from OpenMalaria.utils import submit_run_OpenMalaria

        submit_run_OpenMalaria(exp, scen_df)  # Includes creating XML files

    if 'MalSim' in models_to_run:
        from MalSim.utils import submit_run_MalSim

        submit_run_MalSim(exp)

    # Optionally, create submission script for standardized plots and run after last simulations finished
    if 'OpenMalaria' in models_to_run and 'EMOD' in models_to_run and 'MalSim' in models_to_run:
        submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh',
                            job_id_EMOD='job_id_EMODanalyze', job_id_MalSim='job_id_MalSim_analyze',
                            job='benchmark_plots')
    else:
        if emod_step != 'burnin':
            submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh',
                                custom_args=f"--emodom {' '.join([x for x in models_to_run])}",
                                job='benchmark_plots')
        else:
            pass
