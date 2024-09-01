import logging
import manifest
from helper.helper import *
from helper.helper_slurm import *
from helper.helper_simulation import *
from config_exp import *
import os

# Setting up variables and flags for the simulation
log = logging.getLogger(__name__)


# EMOD flags for how to run simulations (in one run or separated into burnin + pickup)
# In EMOD, running 'burnin' and 'pickup' time in one simulation (Default) can take very long in EMOD depending on burnin time and population size.
# emod_step expects a string, either None, 'burnin' or 'pickup'. Default None will run 'burnin' and 'pickup' time in one simulation.

# Retrieve parsed arguments
args = parse_launch_args()

if args.emodstep in ['pickup', 'new_pickup']:
    file = open(os.path.join(args.directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    exp.emod_step = 'pickup'
    exp.burnin_directory = args.directory
    exp.models_to_run = args.models
    exp.emod_serialized_id = args.serializedid
    if args.emodstep == 'new_pickup': ## Allows to run a independent pickup from burnin
        ## Optional parameters to update in new run
        exp.sweep_list = ['eir', 'cm_clinical', 'seasonality']
        # exp.eir = [8]  # note, needs to be one of the eir values included in the burnin
        # exp.cm = [0.4]  # note, depends on user which parameters desired to change and how
        # exp.num_seeds = ''
        # ...
        ## USER SPECIFIC PARAMETER EDITS
        # ...

    # ensure intervention parameters are correctly setup (some may get updated between burnin and pickup run)
    exp = get_intervention_params(exp)
    exp.plots_to_run = ['benchmark', 'timeseries', 'agecurves'] # For pickup, this needs to be defined again, as for burnin set to empty

    ## Add intervention params back - FIXME not all parameters should be overwritten per default?
    # exp = get_intervention_params(exp)

    if 'cc_step' in exp.intervention_list:
        exp.plots_to_run = ['ccstep']
        exp.analyzer_list = ['daily']

    ##  Note: to simply run a new pickup in same folder and suite, simply change expname
    exp.SUITEname = args.suite
    exp.exp_name = args.expname

else:
    # Creating an Experiment object and setting its attributes, saved as exp.obj
    #exp = initialize_exp(args, manifest)
    exp = LoadExperiment(args, manifest)

    if exp.run_mode == None or exp.run_mode == 'test':
        exp = update_exp(exp)

    if exp.run_mode == 'test':
        exp.pop_size = 1000
        exp.num_seeds = 1
        exp.start_year = 2000
        exp.end_year = 2005
        exp.burnin = 10

    if exp.emod_calib_params:
        calib_config_df = pd.read_csv(os.path.join(exp.emod_input_path, 'emod_best.csv'))
        exp.calib_config_pointer = range(0, len(calib_config_df))  # define rows from calib_params df to run
        del calib_config_df
        exp.sweep_list = exp.sweep_list + ['calib_config_pointer']

    if args.csv:
        ### Experiment scenario parameter definitions
        exp_scen_df = pd.read_csv(os.path.join(f'scenario_inputs/{args.csv}.csv'))
        exp_scen_df = exp_scen_df[exp_scen_df['rownum'] == args.rownum]
        exp.SUITEname = f'{args.csv}_{dt.now().strftime("%Y%m%d")}'
        exp.exp_name = f'{exp_scen_df.exp_name.iat[0]}_{dt.now().strftime("%H_%M_%S")}'

        ## Overwriting default parameters with parameters specific in scenario csv file
        not_param_columns = ['rownum', 'exp_short', 'exp_name']
        for col in exp_scen_df.columns:
            if col not in not_param_columns:
                setattr(exp, col, get_param_from_dataframe(exp_scen_df, col))

    # Entomology mode: Dynamic EIR configuration if selected
    exp = get_seasonal_eir(exp)

    ## Add intervention params, note, for some interventions this might come only in  pickup, not yet setup
    exp = get_intervention_params(exp)  # if empty, uses defaults for a simple baseline run (OM scaffolds etc)
    
    exp.models_to_run_pickup = exp.models_to_run  # Models to run in pickup
    # EMOD burn-in and pickup configuration
    exp.emod_serialized_id = ''
    if exp.emod_step == 'burnin':
        print('Message: Running burnin for EMOD')
        exp.exp_name = f'{exp.exp_name}_burnin{exp.burnin}'
        exp.models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
        exp.plots_to_run = []

    # Update exp_name - FIXME
    exp.exp_name = exp.exp_name.replace('seasonality', exp.seasonality[0])
    exp.exp_name = exp.exp_name.replace('entomologymode', exp.entomology_mode)
    exp.exp_name = exp.exp_name.replace('intervention',
                                        '_'.join(exp.intervention_list))  # if empty, the 'intervention' gets removed

## Arguments that chage for pickup
exp = make_dirs(exp)

# Simulation duration, start and end configuration
exp = get_simulation_time_params(exp)


# Check whether defined input parameter are all valid
check_exp_inputs(exp)

# Parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, exp.sweep_list)
exp.nexps = len(scen_df) * exp.num_seeds
exp.max_running_jobs = min(exp.nexps,150)

save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])
save_scen(param_variation(rep_scen_df(scen_df), exp), fname='scenarios_wseeds.csv', save_dirs=[exp.job_directory, exp.sim_out_dir])

# Write out simulation setup (required for MalSim)
create_simsetup_csv(exp)


if __name__ == '__main__':
    print(f' --------| Running {exp.exp_name} for {", ".join(exp.models_to_run)}: {len(exp.sweep_list)} '
          f'varying parameters: {", ".join(exp.sweep_list)} |--------')

    # Submit EMOD simulation as SLURM job, including scheduled analyzer
    if 'EMOD' in exp.models_to_run:
        from idmtools.core.platform_factory import Platform
        from idmtools.entities.experiment import Experiment
        import emod_malaria.bootstrap as dtk
        import pathlib

        # Set platform and associated values, such as the maximum number of jobs to run at one time
        platform = Platform(manifest.selected_platform, job_directory=exp.suite_directory,
                            mem_per_cpu=int(1800 * exp.mem_increase_factor), partition=manifest.sh_hpc_config['p'],
                            time='06:30:00', account=manifest.sh_hpc_config['A'],
                            modules=[manifest.sh_hpc_config['em_modules']],
                            max_running_jobs=exp.max_running_jobs)  # mem_per_cpu default: 2048
        exp.platform = platform

        dtk.setup(pathlib.Path(manifest.eradication_path).parent)
        from EMOD.utils import submit_run_EMOD
        emod_exp = submit_run_EMOD(exp, scen_df)
        exp.emod_id = emod_exp.id

        if exp.emod_step == 'burnin':
            exp.exp_name_pickup = exp.exp_name.replace(f'_burnin{exp.burnin}', '')
            submit_run_pyscript(exp, pyscript='launch_sim.py', shname='launch_pickup.sh',
                                custom_args=f"--suite {exp.SUITEname} --expname {exp.exp_name_pickup} "
                                            f"--emodstep pickup --serializedid {emod_exp.id} "
                                            f"--models {' '.join([m for m in exp.models_to_run_pickup])} ",
                                job_id_EMOD='job_id_EMODanalyze',memG=5, job='pickup_launch')

    # Submit malariasimulation as SLURM job, including scheduled analyzer
    if 'MalSim' in exp.models_to_run:
        from MalSim.utils import submit_run_MalSim

        submit_run_MalSim(exp)

    # Submit OpenMalaria simulation as SLURM job, including scheduled analyzer
    if 'OpenMalaria' in exp.models_to_run:
        from OpenMalaria.utils import submit_run_OpenMalaria

        submit_run_OpenMalaria(exp, scen_df)  # Includes creating XML files  

    ## Submit plotters to run using wrapper function in helper.py
    if exp.emod_step != 'burnin':
        submit_run_plotters(exp)
