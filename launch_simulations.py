import logging
from datetime import datetime as dt
import manifest
from idmtools.core.platform_factory import Platform
from helper import *
from EMOD.utils import get_scendf_burnin
import os
import argparse

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
    exp.SUITEname = args.suite

    ## Update arguments
    exp.exp_name = args.expname
    exp.models_to_run = args.models
    exp.emod_serialized_id = args.serializedid
    exp.burnin_directory = args.directory
    
    if args.emodstep == 'new_pickup':
      exp_scen_df = pd.read_csv(os.path.join(f'scenario_inputs/{args.csv}.csv'))
      exp_scen_df = exp_scen_df[exp_scen_df['rownum'] == args.rownum]
      exp.exp_name =  f'{exp_scen_df.exp_name.iat[0]}_{dt.now().strftime("%H_%M_%S")}'

      
else:
    ### Experiment scenario parameter definitions
    exp_scen_df = pd.read_csv(os.path.join(f'scenario_inputs/{args.csv}.csv'))
    exp_scen_df = exp_scen_df[exp_scen_df['rownum'] == args.rownum]

    # Creating an Experiment object and setting its attributes, saved as exp.obj
    exp = initialize_exp(args, manifest)

    exp.SUITEname =  f'{args.csv}_{dt.now().strftime("%Y%m%d")}'
    exp.exp_name = f'{exp_scen_df.exp_name.iat[0]}_{dt.now().strftime("%H_%M_%S")}'

    ## Overwriting default parameters with parameters specific in scenario csv file
    not_param_columns = ['rownum', 'exp_short', 'exp_name', 'py_script']
    for col in exp_scen_df.columns:
        if col not in not_param_columns:
            setattr(exp, col, get_param_from_dataframe(exp_scen_df,col))

    # Entomology mode: Dynamic EIR configuration if selected
    exp = get_seasonal_eir(exp)
    
    # EMOD burn-in and pickup configuration
    exp.emod_serialized_id = ''
    if exp.emod_step == 'burnin':
        print('Message: Running burnin for EMOD')
        exp.exp_name = f'{exp.exp_name}_burnin{exp.burnin}'
        exp.models_to_run_pickup = exp.models_to_run  # Models to run in pickup
        exp.models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
        exp.sweep_list = ['eir', 'cm_clinical',  'seasonality']  # If running fewer sweeps in past than in pickup to be set up
        exp.plots_to_run = []

## Add intervention params, note, for some interventions this might come only in  pickup, not yet setup
exp = get_intervention_params(exp)  # if empty, uses defaults for a simple baseline run (OM scaffolds etc)

## Arguments that chage for pickup
exp = make_dirs(exp, overwrite=exp.overwrite)

# Simulation duration, start and end configuration
exp = get_simulation_time_params(exp)

# Check whether defined input parameter are all valid
#check_exp_inputs(exp)

# Parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, exp.sweep_list)
exp.nexps = len(scen_df) * exp.num_seeds

# Set platform and associated values, such as the maximum number of jobs to run at one time
platform = Platform(manifest.selected_platform, job_directory=exp.suite_directory,
                    mem_per_cpu=int(5000 * exp.mem_increase_factor), partition=manifest.sh_hpc_config['p'],
                    time='03:00:00', account=manifest.sh_hpc_config['A'],
                    modules=[manifest.sh_hpc_config['em_modules']], max_running_jobs=300)  # mem_per_cpu default: 2048

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
            submit_run_pyscript(exp, pyscript='launch_simulations.py', shname='launch_pickup.sh',
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

    ## Submit plotters to run using wrapper function in helper.py
    if exp.emod_step != 'burnin':
        submit_run_plotters(exp)
