import logging
import manifest
import os
import sys
from utility.helper import *
from utility.helper_slurm import *
from utility.helper_simulation import *
from utility.experiment import LoadExperiment
# Setting up variables and flags for the simulation
log = logging.getLogger(__name__)


# EMOD flags for how to run simulations (in one run or separated into burnin + pickup)
# In EMOD, running 'burnin' and 'pickup' time in one simulation (Default) can take very long in EMOD depending on burnin time and population size.
# emod_step expects a string, either None, 'burnin' or 'pickup'. Default None will run 'burnin' and 'pickup' time in one simulation.

# Retrieve parsed arguments 
if __name__ == "__main__" and any(arg.endswith("launch_sim.py") for arg in sys.argv):
    args = parse_launch_args()
else:
    from utility.helper_local import LoadLaunchArgs
    args = LoadLaunchArgs()

if args.emodstep in ['pickup', 'new_pickup']:
    file = open(os.path.join(args.directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    exp.emod_step = 'pickup'
    exp.burnin_directory = args.directory
    exp.models = args.models
    exp.emod_serialized_id = args.serializedid
    if args.emodstep == 'new_pickup': ## Allows to run a independent pickup from burnin
        ## USER SPECIFIC PARAMETER EDITS
        ## Optional parameters to update in new run
        exp.sweep_list = ['target_output_values', 'case_management', 'seasonality']

    # ensure intervention parameters are correctly setup (some may get updated between burnin and pickup run)
    exp = get_intervention_params(exp)

    ##  Note: to run a new pickup in same folder and suite, simply change expname
    exp.SUITEname = args.suite
    exp.exp_name = args.expname
    
    if exp.run_mode == 'csv':
        exp_scen_df = pd.read_csv(os.path.join(f'scenario_csv/{exp.csv}.csv'))
        exp_scen_df = exp_scen_df[exp_scen_df['rownum'] == exp.rownum]
        if 'plots_to_run' in exp_scen_df.columns:
            exp.plots_to_run = get_param_from_dataframe(exp_scen_df, 'plots_to_run', exp.sim_params_list)
    else: 
        exp.plots_to_run = ['relationship', 'timeseries', 'agecurves'] # For pickup, this needs to be defined again, as for burnin set to empty


else:
    # Creating an Experiment object and setting its attributes, saved as exp.obj
    exp = LoadExperiment(args, manifest)

    if exp.emod_calib_params:
        calib_config_df = pd.read_csv(os.path.join(exp.emod_input_path, 'emod_calibration_parameters', exp.emod_calib_type)+'.csv')
        exp.calib_config_pointer = range(0, len(calib_config_df))  # define rows from calib_params df to run
        del calib_config_df


    # Entomology mode: Dynamic EIR configuration if selected
    exp = get_seasonal_eir(exp)

    ## Add intervention params, note, for some interventions this might come only in  pickup, not yet setup
    exp = get_intervention_params(exp)  # if empty, uses defaults for a simple baseline run

    exp.models_pickup = exp.models  # Models to run in pickup
    # EMOD burn-in and pickup configuration
    exp.emod_serialized_id = ''
    if exp.emod_step == 'burnin':
        print('Message: Running burnin for EMOD')
        exp.exp_name = f'{exp.exp_name}_burnin{exp.emod_burnin}'
        exp.models = ['EMOD']  # Run burnin only for EMOD, pickup for both models
        exp.plots_to_run = []

    # Update exp_name
    exp.exp_name = exp.exp_name.replace('seasonality', '_'.join(exp.seasonality))
    exp.exp_name = exp.exp_name.replace('entomologymode', exp.entomology_mode)
    if exp.intervention_list != []:
        exp.exp_name = exp.exp_name.replace('intervention',
                                        '_'.join(exp.intervention_list))  
    else:
        exp.exp_name = exp.exp_name.replace('_intervention','')
    if exp.exp_name_note != '':
        exp.exp_name = f'{exp.exp_name}_{exp.exp_name_note}'

## Create the directories for experiment and simulation_output folders
exp = make_dirs(exp)

# Simulation duration, start and end configuration
exp = get_simulation_time_params(exp)

# Check whether defined input parameter are all valid
check_exp_inputs(exp)

# Parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, exp.sweep_list)
exp.nexps = len(scen_df) * exp.num_seeds
exp.max_running_jobs = min(exp.nexps,300)

save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.output_directory])
save_scen(param_variation(rep_scen_df(scen_df), exp), fname='scenarios_wseeds.csv', save_dirs=[exp.job_directory, exp.output_directory])

# Write out simulation setup (required for malariasimulation)
create_simsetup_csv(exp)


if __name__ == '__main__':
    print(f' --------| Running {exp.exp_name} for {", ".join(exp.models)}: {len(exp.sweep_list)} '
          f'varying parameters: {", ".join(exp.sweep_list)}. Run mode:  {exp.run_mode} |--------')

    # Submit EMOD simulation as SLURM job, including scheduled analyzer
    if 'EMOD' in exp.models:
        from EMOD.utils import submit_run_EMOD
        submit_run_EMOD(exp, manifest, scen_df)

    # Submit malariasimulation as SLURM job, including scheduled analyzer
    if 'malariasimulation' in exp.models:
        from malariasimulation.utils import submit_run_malariasimulation
        submit_run_malariasimulation(exp)

    # Submit OpenMalaria simulation as SLURM job, including scheduled analyzer
    if 'OpenMalaria' in exp.models:
        from OpenMalaria.utils import submit_run_OpenMalaria
        submit_run_OpenMalaria(exp, scen_df)  # Includes creating XML files

    ## Submit plotters to run using wrapper function in utility.helper.py
    if exp.emod_step != 'burnin':
        submit_run_plotters(exp)

    if exp.selected_platform == 'Container' and 'EMOD' in exp.models:
        from EMOD.utils import run_analyze_EMOD_local_with_polling
        run_analyze_EMOD_local_with_polling(exp, exp.container_id)

