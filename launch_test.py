import logging
from functools import partial
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from datetime import datetime as dt
import emodpy_malaria.malaria_config as malaria_config
import manifest
from EMOD.utils import *
from helper import *

# Setting up variables and flags for the simulation
log = logging.getLogger(__name__)
loaded_attr = set(dir())  # Non experiiment specific objects to be excluded from exp.obj

# Flag to select whether to run with (dynamic) or without vector model (forced)
entomology_mode = 'forced'  # dynamic, forced
mem_increase_factor = 1.0  # scaling factor on default memory requested

# Name and location of simulation, a SUITE may contain multiple experiments that belong to a shared objective
custom_subdir = os.getlogin()  # If None, no subdir created
SUITEname = f'test_sims'  # Can be changed depending on objective to run simulations, in subdir if not None
exp_name = f'test_sims_{dt.now().strftime("%Y_%m_%d_%H_%M_%S")}'  # Can be changed depending on simulation purpose, in SUITE

# EMOD flags for how to run simulations (in one run or separated into burnin + pickup)
# In EMOD, running 'burnin' and 'pickup' time in one simulation (Default) can take very long in EMOD depending on burnin time and population size.
emod_step = None  # emod_step expects a string, either None, 'burnin' or 'pickup'. Default None will run 'burnin' and 'pickup' time in one simulation.
emod_serialized_id = 'c6849b29-1d9c-4bb5-8af4-4f6537384c09'  # example, insert your exp_id!

# Define which models to run
models_to_run = ['MalSim', 'OpenMalaria', 'EMOD']  # 'EMOD','OpenMalaria', 'MalSim'

# Specify OpenMalaria XML and survey step
# Note, XMLs need to exist in OpenMalaria/inputs
om_scaffold = "R0000GA"
om_survey_step = '30d'

# Define simulation population and seeds
pop_size = 10000  # 1000 for testing
agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # Note, keep these to ensure smooth postprocessing

num_seeds_burnin = 1  # used only if emod_step=='burnin', for EMOD
num_seeds = 3  # suggested minimum 3
start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
end_year = 2005  # end of pickup and monitoring period
burnin = 5  # Duration of burnin (pre-monitoring) period

# Simulation duration, start and end configuration
sim_start_year_em, monitoring_years, sim_dur_years = get_emod_time_param(start_year, end_year, burnin, models_to_run, emod_step)
sim_start_year_om = start_year - burnin

# Name of parameters to vary
sweep_list = ['eir', 'cm_clinical', 'seasonality']

# EMOD burn-in and pickup configuration
if emod_step == 'burnin' and 'EMOD' in models_to_run:
    print('Message: Running burnin for EMOD')
    exp_name = f'{exp_name}_burnin{burnin}'
    models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
    num_seeds = num_seeds_burnin
    sweep_list = ['eir', 'cm_clinical', 'seasonality']  # If running fewer sweeps in past than in pickup to be set up
if emod_step != 'pickup':
    emod_serialized_id = ''

# Define case management start and coverage
# 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
cm_start = 1
cm_clinical = [0.2]  # [0, 0.2, 0.4, 0.6, 0.8, 1]  #[0.2029544]
cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15
detectionLimit = 40

# Transmission and seasonality configuration
seasonality = ["seasonal"]  # ["perennial", "seasonal"]
eir = [0.1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512]  # [0.1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

# Entomology mode: Dynamic EIR configuration if selected
season_daily, season_month, seasonal, perennial = get_seasonal_eir()

# Directory setup and analyzer scripts
suite_directory, job_directory, sim_out_dir = make_dirs(manifest, SUITEname, exp_name, custom_subdir)
emod_analyzer = ['analyze_sim.py']
openmalaria_analyzer = ['analyze_sim.py']

# Set platform and associated values, such as the maximum number of jobs to run at one time
platform = Platform(manifest.selected_platform, job_directory=suite_directory,
                    mem_per_cpu=int(1000 * mem_increase_factor), partition=manifest.sh_hpc_config['p'],
                    time='03:00:00', account=manifest.sh_hpc_config['A'],
                    modules=[manifest.sh_hpc_config['em_modules']], max_running_jobs=50)  # mem_per_cpu default: 2048

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
exp.sim_out_dir = sim_out_dir
exp.job_directory = job_directory

# Assigning attributes to the Experiment object and creating scenarios
for obj_name in my_obj:
    if hasattr(locals().get(obj_name), '__call__'):
        setattr(exp, obj_name, locals().get(obj_name))
    elif obj_name in locals():
        setattr(exp, obj_name, locals().get(obj_name))
    else:
        print(f"Object {obj_name} not found in the locals environment.")

# Parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, sweep_list)
exp.nexps = len(scen_df) * num_seeds

if emod_step == 'pickup':
    scen_df = get_scendf_burnin(exp, emod_serialized_id, manifest, platform,
                                burnin)  # FIXME expand on it when additional parameter values to run in future
save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])

# Check whether defined input parameter are all valid
check_exp_inputs(exp)  # TODO add more validity checks as needed


def config_task(platform):
    print("Creating EMODTask (from files)...")
    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=build_standard_campaign_object,
        schema_path=manifest.schema_file,
        param_custom_cb=set_config_parameters,
        ep4_custom_cb=None,
        demog_builder=build_demog,
        plugin_report=None
    )
    task.set_sif(manifest.SIF_PATH, platform)
    return task


def build_standard_campaign_object():
    import emod_api.campaign as camp
    camp.set_schema(manifest.schema_file)
    return camp


def set_config_parameters(config):
    """
    This function is a callback that is passed to emod-api.config to set config parameters,
    including the malaria defaults.
    Parameters:
        config (object): The configuration object to be modified.
    Returns:
        object: The modified configuration object.
    """
    config = malaria_config.set_team_defaults(config, manifest)
    config.parameters.x_Base_Population = pop_size / 1000
    config.parameters.Simulation_Duration = sim_dur_years * 365
    config.parameters.Report_Detection_Threshold_Blood_Smear_Parasites = detectionLimit
    config.parameters.Report_Detection_Threshold_Blood_Smear_Gametocytes = detectionLimit

    # Parameter configurations on climate for dynamic EIR
    if entomology_mode == 'dynamic':
        malaria_config.add_species(config, manifest, ["gambiae"])  # , "arabiensis", "funestus"

        seasonality_type = seasonality[0]  # 'perennial'  # 'seasonal', 'example'  #FIXME enable sweeping
        config.parameters.Air_Temperature_Filename = os.path.join('climate',
                                                                  f'{seasonality_type}_air_temperature_daily.bin')
        config.parameters.Land_Temperature_Filename = os.path.join('climate',
                                                                   f'{seasonality_type}_air_temperature_daily.bin')
        config.parameters.Rainfall_Filename = os.path.join('climate', f'{seasonality_type}_rainfall_daily.bin')
        config.parameters.Relative_Humidity_Filename = os.path.join('climate',
                                                                    f'{seasonality_type}_relative_humidity_daily.bin')

    # Serialization configuration
    if emod_step == 'burnin':
        config.parameters.Serialized_Population_Writing_Type = "TIMESTEP"
        config.parameters.Serialization_Time_Steps = [sim_dur_years * 365]
        config.parameters.Serialization_Mask_Node_Write = 0
        config.parameters.Serialization_Precision = "REDUCED"
    if emod_step == 'pickup':
        config.parameters.Serialized_Population_Reading_Type = "READ"
        config.parameters.Serialization_Mask_Node_Read = 0
        config.parameters.Serialization_Time_Steps = [burnin * 365]
    return config


def config_sweep_builder_pickup(scen_df_pickup):
    builder = SimulationBuilder()
    if entomology_mode == 'forced':
        matAP = 0.1327
        sweeps = [[
            ItvFn(all_campaigns, row=row),
            partial(set_param, param='Serialized_Population_Path',
                    value=os.path.join(row["serialized_file_path"], "output")),
            partial(set_param, param='Serialized_Population_Filenames', value=row["Serialized_Population_Filenames"]),
            partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.eir)),
            partial(set_param, param='Run_Number', value=s)]
            for i, row in scen_df_pickup.iterrows()
            for s in range(num_seeds)]

    elif entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, row=row),
                   partial(set_param, param='Serialized_Population_Path',
                           value=os.path.join(row["serialized_file_path"], "output")),
                   partial(set_param, param='Serialized_Population_Filenames',
                           value=row["Serialized_Population_Filenames"]),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.x_Temporary_Larval_Habitat),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df_pickup.iterrows()
                  for s in range(num_seeds)]
    else:
        raise ValueError(f'{entomology_mode} not valid')

    builder.add_sweep_definition(sweep_functions, sweeps)

    return [builder]


def config_sweep_builder():
    builder = SimulationBuilder()
    if entomology_mode == 'forced':
        matAP = 0.1327
        sweeps = [[ItvFn(all_campaigns, row=row),
                   partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.eir)),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(num_seeds)]
    elif entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, row=row),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.x_Temporary_Larval_Habitat),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(num_seeds)]
    else:
        raise ValueError(f'{entomology_mode} not valid')

    builder.add_sweep_definition(sweep_functions, sweeps)

    return [builder]


def submit_create_run_EMOD(exp, scen_df):
    """
    This function is designed to be a parameterized version of the sequence of things we do
    every time we run an emod experiment.
    """
    exp_name = exp.exp_name
    emod_serialized_id = exp.emod_serialized_id

    # create EMODTask
    print("Creating EMODTask (from files)...")
    task = config_task(platform)

    if entomology_mode == 'dynamic':
        task.common_assets.add_directory(os.path.join(manifest.input_dir, "example_weather"), relative_path="climate")

    if emod_step == 'pickup':
        serialized_df = build_burnin_df(emod_serialized_id, platform, burnin * 365)
        scen_df_pickup = scen_df.merge(serialized_df, on='scen_id',
                                       how='inner')  ## FIXME when running expanded pickup from burnin
        builder = config_sweep_builder_pickup(scen_df_pickup)
    else:
        builder = config_sweep_builder()

    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years)
    if emod_step != 'burnin':  # do not generate monthly reports for burnin
        add_monthly_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years)

    # Create experiment from builder and run
    experiment = Experiment.from_builder(builder, task, name=exp_name)
    experiment.run(wait_until_done=False, platform=platform)

    # Additional step to schedule analyzer
    experiment.hpc = exp.hpc
    experiment.sh_hpc_config = exp.sh_hpc_config
    experiment.mem_increase_factor = exp.mem_increase_factor
    experiment.analyzer = exp.emod_analyzer
    experiment.job_directory = exp.job_directory
    experiment.emod_step = exp.emod_step
    experiment.start_end = [sim_start_year_em, sim_start_year_em + sim_dur_years - 1]
    submit_analyze_EMOD(experiment, platform)
    print(f"Experiment submission {experiment.uid} succeeded.")


if __name__ == '__main__':

    print(f' --------| Running {exp_name} for {", ".join(models_to_run)}: {len(sweep_list)} '
          f'varying parameters: {", ".join(sweep_list)} |--------')

    # Submit EMOD simulation as SLURM job, including scheduled analyzer
    if 'EMOD' in models_to_run:
        import emod_malaria.bootstrap as dtk
        import pathlib

        dtk.setup(pathlib.Path(manifest.eradication_path).parent)
        submit_create_run_EMOD(exp, scen_df)

    # Submit OpenMalaria simulation as SLURM job, including scheduled analyzer
    if 'OpenMalaria' in models_to_run:
        from OpenMalaria.utils import *
        submit_run_OpenMalaria(exp, scen_df)  # Includes creating XML files
        
    if 'MalSim' in models_to_run:
        from MalSim.utils import *
        submit_run_MalSim(exp)

    # Optionally, after both models aran, generate combined results
    # Note, if dataframes are very large, per default saving a combined df might not be desired to do
    if 'OpenMalaria' in models_to_run and 'EMOD' in models_to_run and 'MalSim' in models_to_run:
        #    #submit_combine_results(exp)  # combined benchmarking.csv
        submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh',
                            job_id_EMOD='job_id_EMODanalyze', job_id_MalSim = 'job_id_MalSim_analyze')
