import logging
from functools import partial
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from datetime import datetime as dt
import emodpy_malaria.malaria_config as malaria_config
import manifest
from EMOD.scaffolds.forcedEIR import *
from EMOD.scaffolds.interventions import treatment_camp_simple
from EMOD.utils import *
from helper import *


# Setting up variables and flags for the simulation
log = logging.getLogger(__name__)
loaded_attr = set(dir())  # Non experiiment specific objects to be excluded from exp.obj

# Flag to select whether to run with (dynamic) or without vector model (forced)
# TODO enable dynamic seasonal EIR  once calibrated
entomology_mode = 'forced'  # dynamic, forced
mem_increase_factor = 1.0  # scaling factor on default memory requested

# Name and location of simulation, a SUITE may contain multiple experiments that belong to a shared objective
custom_subdir = os.getlogin() # If None, no subdir created
SUITEname = f'{entomology_mode}EIR'  # Can be changed depending on objective to run simulations, in subdir if not None
exp_name = f'sim_{dt.now().strftime("%Y_%m_%d_%H_%M_%S")}' # Can be changed depending on simulation purpose, in SUITE

# EMOD flags for how to run simulations (in one run or separated into burnin + pickup)
# In EMOD, running 'burnin' and 'pickup' time in one simulation (Default) can take very long in EMOD depending on burnin time and population size.
emod_step = None  # emod_step expects a string, either None, 'burnin' or 'pickup'. Default None will run 'burnin' and 'pickup' time in one simulation.
emod_serialized_id = '6ad52475-082a-413a-b35f-15be265a325e' # example, insert your exp_id!

# Define which models to run
models_to_run = ['EMOD', 'OpenMalaria']  # 'EMOD','OpenMalaria'

# Specify OpenMalaria XML and survey step
# Note, XMLs need to exist in OpenMalaria/inputs
om_scaffold = "R0000GA"
om_survey_step = '30d'

# Define simulation population and seeds
pop_size = 1000
agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # Note, keep these to ensure smooth postprocessing

num_seeds_burnin = 1  #used only if emod_step=='burnin', for EMOD
num_seeds = 3  # used for all other simulations except EMOD burnin
start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
end_year = 2010  # end of pickup and monitoring period
burnin = 5  # Duration of burnin (pre-monitoring) period

# Simulation duration, start and end configuration
sim_start_year_em, monitoring_years, sim_dur_years = get_emod_time_param(start_year, end_year, burnin, emod_step)
sim_start_year_om = start_year - burnin

# Name of parameters to vary
sweep_list = ['eir', 'cm_clinical', 'seasonality'] + ['seed']

# EMOD burn-in and pickup configuration
if emod_step == 'burnin' and 'EMOD' in models_to_run:
    print('Message: Running burnin for EMOD')
    exp_name = f'{exp_name}_burnin{burnin}'
    models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
    num_seeds = num_seeds_burnin
    sweep_list = ['eir', 'cm_clinical', 'seasonality'] + ['seed']  # If running fewer sweeps in past than in pickup
if emod_step != 'pickup':
    emod_serialized_id = ''

# Define case management start and coverage
# 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
cm_start = 1
cm_clinical = [0.2029544] # [0.2, 0.6, 0.8]
cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15
detectionLimit = 40

# Transmission and seasonality configuration
seasonality = ["seasonal"]  # ["perennial", "seasonal"]
eir = [8]  # [0.1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

# Entomology mode: Dynamic EIR configuration if selected
season_daily, season_month, seasonal, perennial = get_seasonal_eir()
if entomology_mode == 'dynamic':
    # TODO function to map LHS to annual input EIR values, derives from EMOD simulation
    lhs = np.logspace(-2, 3, len(eir))
    print('Dynamic EIR has not yet been aligned between EMOD and OpenMalaria')

# Directory setup and analyzer scripts
suite_directory, job_directory, sim_out_dir = make_dirs(manifest, SUITEname, exp_name, custom_subdir)
emod_analyzer = ['analyze_sim.py']
openmalaria_analyzer = ['analyze_sim.py']
seed = list(range(num_seeds))  # required for scenarios csv used in generating OpenMalaria scenarios

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
# Update for cm_severe based on cm_clinical, cm_severe should always be higher than cm_clinical
scen_df['cm_clinical'] = pd.to_numeric(scen_df['cm_clinical'], errors='coerce')
scen_df['cm_severe'] = np.where(scen_df['cm_clinical'] * 1.15 > cm_severe,
                                np.minimum(scen_df['cm_clinical'] * 1.15, 1), cm_severe)
scen_df['cm_severe'] = np.where(scen_df['cm_clinical'] == 0, 0, scen_df['cm_severe'])

exp.nexps = len(scen_df)  # * seeds ## not needed when included in sweep_list
save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])

# Check whether defined input parameter are all valid
check_exp_inputs(exp)  #TODO add more validity checks as needed

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

        # TO DO enable seasonality sweep via habitat multiplier
        seasonality_type = 'example'
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


def build_campaign(seasonality=None, EIR_scale_factor=None, cm_cov=0.2029544, cm_severe_cov=0.48, cm_start=1):
    """
    Build and configure a campaign object for an EMOD simulation.
    Parameters:
        seasonality (list or None): List of seasonality values.
        EIR_scale_factor (float or None): Scaling factor for the input EIR.
        cm_cov (float): Coverage of clinical case management for all ages.
        cm_severe_cov (float): Coverage of severe case management for all ages.
        cm_start (int): Start day for case management interventions.
    Returns:
        object: The campaign object.
    """
    camp = build_standard_campaign_object(manifest)
    treatment_camp_simple(camp, cm_start=cm_start, cm_clinical=cm_cov, cm_severe=cm_severe_cov)
    if EIR_scale_factor is not None:
        set_inputEIR_seasonality(camp, EIR_scale_factor, seasonality)
    return camp

def update_campaign_multiple_parameters(simulation, cm_cov, cm_severe_cov, cm_start):
    build_camp_partial = partial(build_campaign, cm_cov=cm_cov, cm_severe_cov=cm_severe_cov, cm_start=cm_start)
    rdic = {"cm_clinical": cm_cov, "cm_severe": cm_severe_cov, 'cm_start': cm_start}
    simulation.task.create_campaign_from_callback(build_camp_partial)
    return rdic


def update_campaign_multiple_parameters_wEIR(simulation, cm_cov, cm_severe_cov, cm_start, EIR_scale_factor, season):
    update_mab(simulation, mAb_vs_EIR(EIR_scale_factor))  # eir default = 1
    build_camp_partial = partial(build_campaign,
                                 seasonality=season, EIR_scale_factor=EIR_scale_factor,
                                 cm_cov=cm_cov, cm_severe_cov=cm_severe_cov, cm_start=cm_start)
    rdic = {"EIR_scale_factor": EIR_scale_factor, "seasonality": season, "cm_clinical": cm_cov,
            "cm_severe": cm_severe_cov, 'cm_start': cm_start}
    simulation.task.create_campaign_from_callback(build_camp_partial)
    return rdic


def update_eir_scale(simulation, value, svalue):
    """
    Updates the EIR scale factor and seasonality parameters for an EMOD simulation.
    Args:
        simulation: The EMOD simulation object.
        value: The new value for the EIR scale factor.
        svalue: The new value for the seasonality parameter.
    """
    build_campaign_partial = partial(build_campaign, EIR_scale_factor=value, seasonality=svalue)
    simulation.task.create_campaign_from_callback(build_campaign_partial)
    return {"EIR_scale_factor": value, "seasonality": svalue}


def sweep_burnin_simulations(simulation, df, x: int, entomology_mode='dynamic'):
    """
    Updates campaign parameters and serialization configuration for the EMOD simulation
    Is run if emod_step = 'pickup' (pickup from serialized burnin simulation).
    Args:
        simulation: The EMOD simulation object.
        df: The DataFrame containing simulation data from burnin (see build_burnin_df in EMOD_utils.py).
        x: The index of the simulation burnin data to use.
        entomology_mode: The mode for entomology settings ('dynamic' or 'forced'), default is forced.
    """
    path = df["serialized_file_path"][x]
    seed = int(df["Run_Number"][x])

    simulation.task.config.parameters.Serialized_Population_Path = os.path.join(path, "output")
    simulation.task.config.parameters.Serialized_Population_Filenames = df["Serialized_Population_Filenames"][x]
    simulation.task.config.parameters.Run_Number = seed

    if entomology_mode == 'dynamic':
        simulation.task.config.parameters.x_Temporary_Larval_Habitat = float(df["x_Temporary_Larval_Habitat"][x])
        transm_spec = ['x_Temporary_Larval_Habitat',
                       float(df["x_Temporary_Larval_Habitat"][x])]  # FIXME, enable seasonality once calibrated
    else:
        update_eir_scale(simulation, float(df["EIR_scale_factor"][x]), df["seasonality"][x])
        transm_spec = ['EIR_scale_factor', float(df["EIR_scale_factor"][x])]

    return {
        "Serialized_Population_Path": os.path.join(df["serialized_file_path"][x], "output"),
        "Serialized_Population_Filenames": df["Serialized_Population_Filenames"][x],
        "seasonality": df["seasonality"][x],
        "Run_Number": seed,
        transm_spec[0]: transm_spec[1],
        "cm_clinical": df["cm_clinical"][x]
    }


def submit_create_run_EMOD(exp):
    """
    This function is designed to be a parameterized version of the sequence of things we do
    every time we run an emod experiment.
    """
    selected_platform = exp.selected_platform
    exp_name = exp.exp_name
    emod_serialized_id = exp.emod_serialized_id

    # Set platform and associated values, such as the maximum number of jobs to run at one time
    platform = Platform(selected_platform, job_directory=suite_directory,
                        mem_per_cpu=int(1000 * exp.mem_increase_factor), partition=exp.sh_hpc_config['p'], time='03:00:00', account=exp.sh_hpc_config['A'],
                        modules=[exp.sh_hpc_config['em_modules']], max_running_jobs=50)  # mem_per_cpu default: 2048

    # create EMODTask
    print("Creating EMODTask (from files)...")
    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=build_campaign,
        schema_path=manifest.schema_file,
        param_custom_cb=set_config_parameters,
        ep4_custom_cb=None,
        demog_builder=build_demog,
        plugin_report=None
    )

    # Set the singularity image to be used when running this experiment
    task.set_sif(manifest.SIF_PATH, platform)
    if entomology_mode == 'dynamic':
        task.common_assets.add_directory(os.path.join(manifest.input_dir, "example_weather"), relative_path="climate")

    # Create experiment from builder
    builder = SimulationBuilder()

    # Create burnin df, retrieved from burnin ID (defined above)
    if emod_step == 'pickup':
        serialized_df = build_burnin_df(emod_serialized_id, platform, burnin * 365)
        builder.add_sweep_definition(partial(sweep_burnin_simulations, df=serialized_df, entomology_mode=entomology_mode),
                                     range(len(serialized_df.index)))
        if exp.burnin_num_seeds == 1:
            builder.add_sweep_definition(partial(set_param, param='Run_Number'), range(num_seeds))

    else:
        builder.add_sweep_definition(partial(set_param, param='Run_Number'), range(num_seeds))
        if entomology_mode == 'dynamic':
            builder.add_sweep_definition(partial(set_param, param='x_Temporary_Larval_Habitat'), lhs)
            builder.add_multiple_parameter_sweep_definition(update_campaign_multiple_parameters,
                                                        dict(cm_cov=cm_clinical, cm_severe_cov=[cm_severe],
                                                             cm_start=[cm_start]))
        else:
            builder.add_multiple_parameter_sweep_definition(update_campaign_multiple_parameters_wEIR,
                                                        dict(cm_cov=cm_clinical, cm_severe_cov=[cm_severe],
                                                             cm_start=[cm_start],
                                                             EIR_scale_factor=eir, season=seasonality))

    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years)
    if emod_step != 'burnin': # we want this for both pickup and none
        add_monthly_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years)

    # Create experiment from builder and run
    # experiment = Experiment.from_task(task, name=exp_name)
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
        submit_create_run_EMOD(exp)

    # Submit OpenMalaria simulation as SLURM job, including scheduled analyzer
    if 'OpenMalaria' in models_to_run:
        from OpenMalaria.utils import *

        submit_run_OpenMalaria(exp, scen_df)  # Includes creating XML files

    # Optionally, after both models aran, generate combined results
    # Note, if dataframes are very large, per default saving a combined df might not be desired to do
    if 'OpenMalaria' and 'EMOD' in models_to_run:
        #    #submit_combine_results(exp)  # combined benchmarking.csv
        submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh',
                            job_id='job_id_EMODanalyze')
