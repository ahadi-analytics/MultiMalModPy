import logging
from idmtools.entities.experiment import Experiment
import manifest
from idmtools.core.platform_factory import Platform
from helper import *
import os

# Setting up variables and flags for the simulation
log = logging.getLogger(__name__)


# EMOD flags for how to run simulations (in one run or separated into burnin + pickup)
# In EMOD, running 'burnin' and 'pickup' time in one simulation (Default) can take very long in EMOD depending on burnin time and population size.
# emod_step expects a string, either None, 'burnin' or 'pickup'. Default None will run 'burnin' and 'pickup' time in one simulation.


# Retrieve parsed arguments
args = parse_launch_args()


if args.emodstep =='pickup':
    file = open(os.path.join(args.directory, "exp.obj"), "rb")
    exp = pickle.load(file)

    ## Update arguments
    exp.SUITEname = args.suite
    exp.exp_name = args.expname
    exp.emod_step = args.emodstep
    exp.models_to_run = args.models
    exp.emod_serialized_id = args.serializedid
else:
    # Creating an Experiment object and setting its attributes, saved as exp.obj
    exp = Experiment()

    exp.SUITEname = args.suite
    exp.exp_name = args.expname
    exp.emod_step = args.emodstep
    exp.models_to_run = args.models

    exp.hpc = manifest.hpc
    exp.sh_hpc_config = manifest.sh_hpc_config
    exp.selected_platform = manifest.selected_platform
    exp.om_version = manifest.om_version
    exp.emod_build = manifest.emod_build
    exp.om_path = manifest.OM_PATH
    exp.om_input_path = manifest.om_input_path
    exp.job_directory_manifest = manifest.job_directory
    exp.output_directory_manifest = manifest.output_directory

    # Flag to select whether to run with (dynamic) or without vector model (forced)
    exp.entomology_mode = 'dynamic'  # dynamic, forced
    exp.seasonality = ['perennial']  # ["perennial", "seasonal"]  #"Current framework support only 1 seasonality patten per experiment"
    exp.mem_increase_factor = 5.0  # scaling factor on default memory requested

    # Name and location of simulation, a SUITE may contain multiple experiments that belong to a shared objective
    exp.user = os.environ.get('USER')
    exp.custom_subdir = exp.user  # If None, no subdir created

    # Specify OpenMalaria XML and survey step
    exp.om_scaffold = "R0000GA_CC_STEP"  # defining which OpenMalaria XML scaffold to use
    exp.om_survey_step = '5d'

    # Specify MalSim simulation setup, interventions etc to run
    exp.MalSim_script = 'malsim_benchmarking_exercise.R'
    exp.MalSim_run_burnin = True

    # Define simulation population and seeds
    exp.pop_size = 10000  # 1000 for testing
    exp.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # Note, keep these to ensure smooth postprocessing

    exp.num_seeds_burnin = 1  # used only if emod_step=='burnin', for EMOD
    exp.num_seeds = 20  # suggested minimum 3, in production 5-10
    exp.start_year = 1995  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
    exp.end_year = 2080  # end of pickup and monitoring period
    exp.burnin = 80  # Duration of burnin (pre-monitoring) period, should be 80 years to establish immunity in the population
    #Set up intervention list (for launch_cc_step.py this will only include cc_step for now)
    exp.intervention_list = ['cc_step'] #As we add interventions we now need this list.
    
    # Name of parameters to vary
    exp.sweep_list = ['eir','cm_clinical', 'seasonality']
    exp.emod_calib_params = False #A new function in the framework, are we passing along our within host framework recalibrated parameters, default will be false.

    # Define case management start and coverage
    # 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
    exp.cm_start = 1
    exp.cm_clinical = [0.0]  # [0, 0.2, 0.4, 0.6, 0.8, 1]  #[0.2029544]
    exp.cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15
    exp.detectionLimit = 40

    # Transmission and seasonality configuration for eir step, each model requires different eirs to reflect 
    # prevalences of 0.1, 0.25, and 0.50 respectively.
    exp.eir = [1.5, 1.5,3,3,9,9]
    exp.eir_scalar_emod = [2,6,0.5,3,0.1667,0.3333]
    exp.eir_malsim = [1,1,3,3,16,16]
    exp.eir_scalar_malsim = [3,16,0.333,5.3333,0.0625,0.1875]
    exp.eir_om = [0.8,0.8,2.2,2.2,7,7]
    #exp.eir_scalar_om = [2.5,8,0.4,3.2,0.125,0.3125] om requires negative values to increase, and values (1-x) to decrease
    exp.eir_scalar_om = [-1.75,-7.75,0.636,-2.182,0.886,0.686]
    exp.eir_scalar_timestep_5day = int((73*(exp.burnin + 5))) # 5 Years in to the pickup time OpenMalaria
    exp.eir_scalar_timestep_daily = int(1825) # 5 years in to the pickup time EMOD and Malsim 
    exp.carrying_capacity_step = [f'10%-25%',f'10%-50%',f'25%-10%',f'25%-50%',f'50%-10%',f'50%-25%']
    # Entomology mode: Dynamic EIR configuration if selected
    exp = get_seasonal_eir(exp)

    # EMOD burn-in and pickup configuration
    exp.emod_serialized_id = ''
    if exp.emod_step == 'burnin':
        print('Message: Running burnin for EMOD')
        exp.exp_name = f'{exp.exp_name}_burnin{exp.burnin}'
        exp.models_to_run_pickup = exp.models_to_run  # Models to run in pickup
        exp.models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
        exp.sweep_list = ['eir', 'cm_clinical', 'seasonality']  # If running fewer sweeps in past than in pickup to be set up


    # Update exp_name
    exp.exp_name = exp.exp_name.replace('seasonality', exp.seasonality[0])
    exp.exp_name = exp.exp_name.replace('entomologymode', exp.entomology_mode)

    # Directory setup and analyzer scripts
    exp.emod_analyzer = ['analyze_sim.py']
    exp.openmalaria_analyzer = ['analyze_sim.py']


## Arguments that chage for pickup
exp = make_dirs(exp)  # we are currenlty only going to run one seasonality at a time

# Simulation duration, start and end configuration
exp = get_emod_time_param(exp)


# Check whether defined input parameter are all valid
check_exp_inputs(exp)  # TODO add more validity checks as needed

# Parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, exp.sweep_list)
exp.nexps = len(scen_df) * exp.num_seeds

# Set platform and associated values, such as the maximum number of jobs to run at one time
platform = Platform(manifest.selected_platform, job_directory=exp.suite_directory,
                    mem_per_cpu=int(5000 * exp.mem_increase_factor), partition=manifest.sh_hpc_config['p'],
                    time='04:00:00', account=manifest.sh_hpc_config['A'],
                    modules=[manifest.sh_hpc_config['em_modules']], max_running_jobs=exp.nexps)  # mem_per_cpu default: 2048

save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])
save_scen(rep_scen_df(scen_df), fname='scenarios_wseeds.csv', save_dirs=[exp.job_directory, exp.sim_out_dir])

# Write out simulation setup (required for MalSim)
create_simsetup_csv(exp)
exp.platform = platform


if __name__ == '__main__':

    print(f' --------| Running {exp.exp_name} for {", ".join(exp.models_to_run)}: {len(exp.sweep_list)} '
          f'varying parameters: {", ".join(exp.sweep_list)} |--------')

    # Submit EMOD simulation as SLURM job, including scheduled analyzer
    if 'EMOD' in exp.models_to_run:
        import emod_malaria.bootstrap as dtk
        import pathlib

        dtk.setup(pathlib.Path(manifest.eradication_path).parent)
        from EMOD.utils import submit_run_EMOD

        emod_exp = submit_run_EMOD(exp, scen_df)
        exp.emod_id = emod_exp.id

        if exp.emod_step == 'burnin':
            exp.exp_name_pickup = exp.exp_name.replace(f'_burnin{exp.burnin}', '')
            submit_run_pyscript(exp, pyscript='launch_test.py', shname='launch_pickup.sh',
                                custom_args=f"--suite {exp.SUITEname} --expname {exp.exp_name_pickup} "
                                            f"--emodstep pickup --serializedid {emod_exp.id} "
                                            f"--models {' '.join([m for m in exp.models_to_run_pickup])} ",
                                job_id_EMOD='job_id_EMODanalyze', job='pickup_launch')

    # Submit malariasimulation as SLURM job, including scheduled analyzer
    if 'MalSim' in exp.models_to_run:
        from MalSim.utils import submit_run_MalSim

        submit_run_MalSim(exp)

    # Submit OpenMalaria simulation as SLURM job, including scheduled analyzer
    if 'OpenMalaria' in exp.models_to_run:
        from OpenMalaria.utils import submit_run_OpenMalaria

        submit_run_OpenMalaria(exp, scen_df)  # Includes creating XML files

    # Optionally, create submission script for standardized plots and run after last simulations finished
    if 'OpenMalaria' in exp.models_to_run and 'EMOD' in exp.models_to_run and 'MalSim' in exp.models_to_run:
        submit_run_pyscript(exp, pyscript='plot_benchmark.py', shname='run_benchmark_plots.sh',
                            job_id_EMOD='job_id_EMODanalyze', job_id_MalSim='job_id_MalSim_analyze',
                            job='benchmark_plots', memG=20)
    else:
        if exp.emod_step != 'burnin':
            submit_run_pyscript(exp, pyscript='plot_benchmark.py', shname='run_benchmark_plots.sh',
                                custom_args=f"--emodom {' '.join([x for x in exp.models_to_run])}",
                                job='benchmark_plots', memG=20)
        else:
            pass
