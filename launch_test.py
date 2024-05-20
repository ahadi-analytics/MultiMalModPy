import logging
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


if args.emodstep in ['pickup', 'new_pickup']:
    file = open(os.path.join(args.directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    exp.emod_step = 'pickup'
    exp.burnin_directory = args.directory
    
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
        exp = get_intervention_params(exp)
        

    ##  Note: to simply run a new pickup in same folder and suite, simply change expname
    exp.SUITEname = args.suite
    exp.exp_name = args.expname

else:
    # Creating an Experiment object and setting its attributes, saved as exp.obj
    exp = initialize_exp(args, manifest)
    # Define simulation population and seeds
    if exp.overwrite:
        exp.pop_size = 10000  # 1000 for testing
        exp.num_seeds = 20  # suggested minimum 3, in production 5-10
        exp.start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
        exp.end_year = 2008 # end of pickup and monitoring period
        exp.burnin = 80  # Duration of burnin (pre-monitoring) period, should be 80 years to establish immunity in the population
        
    # Define case management start and coverage
    # 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
    exp.cm_start = 1
    exp.cm_clinical = [0.0]  # [0, 0.2, 0.4, 0.6, 0.8, 1]  #[0.2029544]
    exp.cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15

    # Entomology mode: Dynamic EIR configuration if selected
    exp = get_seasonal_eir(exp)

    # EMOD burn-in and pickup configuration
    exp.emod_serialized_id = ''
    if exp.emod_step == 'burnin':
        print('Message: Running burnin for EMOD')
        exp.exp_name = f'{exp.exp_name}_burnin{exp.burnin}'
        exp.models_to_run_pickup = exp.models_to_run  # Models to run in pickup
        exp.models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
        exp.plots_to_run = []

    # Update exp_name
    exp.exp_name = exp.exp_name.replace('seasonality', exp.seasonality[0])
    exp.exp_name = exp.exp_name.replace('entomologymode', exp.entomology_mode)
    exp.exp_name = exp.exp_name.replace('intervention', '_'.join(exp.intervention_list)) # if empty, the 'intervention' gets removed
    ## Add intervention params, note, for some interventions this might come only in  pickup, not yet setup
    exp = get_intervention_params(exp)  # if empty, uses defaults for a simple baseline run (OM scaffolds etc)

## Arguments that chage for pickup
exp = make_dirs(exp, overwrite=exp.overwrite)

# Simulation duration, start and end configuration
exp = get_simulation_time_params(exp)


# Check whether defined input parameter are all valid
#check_exp_inputs(exp)  # TODO add more validity checks as needed

# Parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, exp.sweep_list)
exp.nexps = len(scen_df) * exp.num_seeds

# Set platform and associated values, such as the maximum number of jobs to run at one time
platform = Platform(manifest.selected_platform, job_directory=exp.suite_directory,
                    mem_per_cpu=int(2400 * exp.mem_increase_factor), partition=manifest.sh_hpc_config['p'],
                    time='04:30:00', account=manifest.sh_hpc_config['A'],
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
                                job_id_EMOD='job_id_EMODanalyze',memG=1, job='pickup_launch')

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

