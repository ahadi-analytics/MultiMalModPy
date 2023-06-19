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
from EMOD.scaffolds.interventions import treatment_camp
from EMOD.utils import *
from helper import *

# Setting up variables and flags for the simulation
log = logging.getLogger(__name__)
loaded_attr = set(dir())  # Non experiiment specific objects to be excluded from exp.obj

# Flag to select whether to run with (dynamic) or without vector model (forced)
# TODO enable dynamic seasonal EIR  once calibrated
entomology_mode = 'forced'  # dynamic, forced

# Name and location of simulation, a SUITE may contain multiple experiments that belong to a shared objective
custom_subdir = os.getlogin() # If None, no subdir created
SUITEname = f'{entomology_mode}EIR'  # Can be changed depending on objective to run simulations, in subdir if not None
exp_name = f'sim_{dt.now().strftime("%Y_%m_%d_%H_%M_%S")}' # Can be changed depending on simulation purpose, in SUITE

# EMOD serialization or pickup flags
emod_serialize = False
emod_pickup = False

# Define which models to run
models_to_run = ['EMOD', 'OpenMalaria']  # 'EMOD','OpenMalaria'

# Specify OpenMalaria XML and survey step
# Note, XMLs need to exist in OpenMalaria/inputs
om_scaffold = "R0000GA"
om_survey_step = '30d'

# Define simulation population and seeds
pop_size = 10000
agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # Note, keep these to ensure smooth postprocessing
num_seeds = 3
seed = list(range(num_seeds)) # required for scenarios csv used in generating OpenMalaria scenarios
start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
end_year = 2020  # end of pickup and monitoring period
burnin = 10  # Duration of burnin (pre-monitoring) period

# Simulation duration, start and end configuration
sim_start_year_em, monitoring_years, sim_dur_years = get_emod_time_param(start_year, end_year, burnin, emod_serialize,
                                                                         emod_pickup)
sim_start_year_om = start_year - burnin

# Name of parameters to vary
sweep_list = ['eir', 'access', 'seasonality'] + ['seed']

# EMOD burn-in and pickup configuration
# TODO different for SciCore and Quest, user specific
if entomology_mode == 'forced':
    emod_burnin_id = 'c32c30e5-d822-4854-8dd1-ba17f954a892'  # forced EIR
else:
    emod_burnin_id = '1b5781b0-3d51-4d00-956b-c963fab53046'  # dynamic EIR

if emod_serialize and 'EMOD' in models_to_run:
    print('Message: Running burnin for EMOD')
    exp_name = f'{exp_name}_burnin{burnin}'
    emod_burnin_id = ''
    models_to_run = ['EMOD']  # Run burnin only for EMOD, pickup for both models
    sweep_list = ['eir', 'access', 'seasonality', 'seed'] # If running fewer sweeps in past than in pickup
if not emod_pickup:
    emod_burnin_id = None


# Define case management start and coverage
# 0.2029544 in OpenMalaria corresponds to 5-day probability already converted from 2 weeks coverage, use same for EMOD?
cm_start = 1
access = [0.2029544]

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

# Creating an Experiment object and setting its attributes, saved as exp.obj
my_obj = set(dir()) - loaded_attr
exp = Experiment()
exp.my_obj = my_obj
exp.hpc = manifest.hpc
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
exp.nexps = len(scen_df)  # * seeds ## not needed when included in sweep_list
save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])


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
    if emod_serialize:
        config.parameters.Serialized_Population_Writing_Type = "TIMESTEP"
        config.parameters.Serialization_Time_Steps = [sim_dur_years * 365]
        config.parameters.Serialization_Mask_Node_Write = 0
        config.parameters.Serialization_Precision = "REDUCED"

    # Burnin configuration (when reading from serialized file)
    if emod_burnin_id and not emod_serialize:
        config.parameters.Serialized_Population_Reading_Type = "READ"
        config.parameters.Serialization_Mask_Node_Read = 0
        config.parameters.Serialization_Time_Steps = [burnin * 365]
    return config


def build_campaign(seasonality=None, EIR_scale_factor=None, cm_cov=0.5, cm_start=1):
    """
    Build and configure a campaign object for an EMOD simulation.
    Parameters:
        seasonality (list or None): List of seasonality values.
        EIR_scale_factor (float or None): Scaling factor for the input EIR.
        cm_cov (float): Coverage of case management interventions.
        cm_start (int): Start day for case management interventions.
    Returns:
        object: The campaign object.
    """
    camp = build_standard_campaign_object(manifest)
    treatment_camp(camp, cm_start=cm_start, cm_clinical_U5=cm_cov)
    if EIR_scale_factor is not None:
        set_inputEIR_seasonality(camp, EIR_scale_factor, seasonality)
    return camp


def update_campaign_multiple_parameters_ser(simulation, df, cm_cov, cm_start, x: int):
    """
    Updates campaign parameters and serialization configuration for the EMOD simulation
    Args:
        simulation: The EMOD simulation object.
        df: The dataframe containing simulation parameters.
        cm_cov: The coverage for clinical management interventions.
        cm_start: The start day for clinical management interventions.
        x: The index of the dataframe entry to use.
    Returns:
        A dictionary containing the updated campaign parameters.
    """
    path = df["serialized_file_path"][x]
    seed = int(df["Run_Number"][x])
    if entomology_mode == 'forced':
        eir = float(df["EIR_scale_factor"][x])
        season = float(df["seasonality"][x])
        eir_dic = {"EIR_scale_factor": eir, "seasonality": season}
        build_campaign_partial = partial(build_campaign, seasonality=season, EIR_scale_factor=eir, cm_cov=cm_cov,
                                         cm_start=cm_start)
    else:
        lhs = float(df["x_Temporary_Larval_Habitat"][x])
        eir_dic = {"x_Temporary_Larval_Habitat": lhs,
                   "seasonality": 'perennial'}  # FIXME, enable seasonality sweep via habitat multiplier
        build_campaign_partial = partial(build_campaign, cm_cov=cm_cov, cm_start=cm_start)
    simulation.task.create_campaign_from_callback(build_campaign_partial)

    if emod_serialize:
        simulation.task.set_parameter("Serialized_Population_Filenames", df["Serialized_Population_Filenames"][x])
        simulation.task.set_parameter('Serialized_Population_Path', os.path.join(path, 'output'))
        simulation.task.set_parameter('Run_Number', seed)

    return {**eir_dic, **{"cm_cov": cm_cov, "Run_Number": seed}}


def update_campaign_multiple_parameters(simulation, cm_cov, cm_start):
    build_camp_partial = partial(build_campaign, cm_cov=cm_cov, cm_start=cm_start)
    rdic = {"cm_clinical_U5": cm_cov, 'cm_start': cm_start}
    simulation.task.create_campaign_from_callback(build_camp_partial)
    return rdic


def update_campaign_multiple_parameters_wEIR(simulation, cm_cov, cm_start, EIR_scale_factor, season):
    update_mab(simulation, mAb_vs_EIR(EIR_scale_factor))  # eir default = 1
    build_camp_partial = partial(build_campaign, seasonality=season, EIR_scale_factor=EIR_scale_factor, cm_cov=cm_cov,
                                 cm_start=cm_start)
    rdic = {"EIR_scale_factor": EIR_scale_factor, "seasonality": season, "cm_clinical_U5": cm_cov, 'cm_start': cm_start}
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
    Args:
        simulation: The EMOD simulation object.
        df: The DataFrame containing simulation data.
        x: The index of the simulation data to use.
        entomology_mode: The mode for entomology settings ('dynamic' or other).
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
        update_eir_scale(simulation, float(df["EIR_scale_factor"][x]), float(df["seasonality"][x]))
        transm_spec = ['EIR_scale_factor', float(df["EIR_scale_factor"][x])]

    return {
        "Serialized_Population_Path": os.path.join(df["serialized_file_path"][x], "output"),
        "Serialized_Population_Filenames": df["Serialized_Population_Filenames"][x],
        "seasonality": df["seasonality"][x],
        "Run_Number": seed,
        transm_spec[0]: transm_spec[1]
    }


def submit_create_run_EMOD(exp):
    """
    This function is designed to be a parameterized version of the sequence of things we do
    every time we run an emod experiment.
    """
    selected_platform = exp.selected_platform
    exp_name = exp.exp_name
    emod_burnin_id = exp.emod_burnin_id

    # Set platform and associated values, such as the maximum number of jobs to run at one time
    platform = Platform(selected_platform, job_directory=suite_directory,
                        mem_per_cpu=1000, partition='b1139', time='03:00:00', account='b1139',
                        modules=['singularity'], max_running_jobs=50)  # mem_per_cpu default: 2048

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
    if emod_burnin_id:
        burnin_df = build_burnin_df(emod_burnin_id, platform, burnin * 365)
        builder.add_sweep_definition(partial(sweep_burnin_simulations, df=burnin_df, entomology_mode=entomology_mode),
                                     range(len(burnin_df.index)))

    # builder.add_sweep_definition(update_eir_scale, eir)
    builder.add_sweep_definition(partial(set_param, param='Run_Number'), range(num_seeds))
    if entomology_mode == 'dynamic':
        builder.add_sweep_definition(partial(set_param, param='x_Temporary_Larval_Habitat'), lhs)
        builder.add_multiple_parameter_sweep_definition(update_campaign_multiple_parameters,
                                                        dict(cm_cov=access, cm_start=[1]))
    else:
        builder.add_multiple_parameter_sweep_definition(update_campaign_multiple_parameters_wEIR,
                                                        dict(cm_cov=access, cm_start=[1],
                                                             EIR_scale_factor=eir,
                                                             season=seasonality))

    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years)
    if not emod_serialize:
        add_monthly_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years)

    # Create experiment from builder and run
    # experiment = Experiment.from_task(task, name=exp_name)
    experiment = Experiment.from_builder(builder, task, name=exp_name)
    experiment.run(wait_until_done=False, platform=platform)

    # Additional step to schedule analyzer
    experiment.hpc = exp.hpc
    experiment.analyzer = exp.emod_analyzer
    experiment.job_directory = exp.job_directory
    experiment.emod_serialize = exp.emod_serialize
    experiment.start_end = [sim_start_year_em, sim_start_year_em + sim_dur_years - 1]
    submit_analyze_EMOD(experiment, platform)

    print(f"Experiment submission {experiment.uid} succeeded.")


if __name__ == '__main__':

    print(f' --------| Running {exp_name} for {", ".join(models_to_run)}: {len(sweep_list)} '
          f'varying parameters: {", ".join(sweep_list)} |--------')

    # Submit EMOD simulation as SLURM job, including scheduled analyzer
    if 'EMOD' in models_to_run:
        submit_create_run_EMOD(exp)

    # Submit OpenMalaria simulation as SLURM job, including scheduled analyzer
    if 'OpenMalaria' in models_to_run:
        from OpenMalaria.utils import *

        submit_run_OpenMalaria(exp, scen_df)  # Includes creating XML files

    # Optionally, after both models aran, generate combined results
    # Note, if dataframes are very large, per default saving a combined df might not be desired to do
    # if 'OpenMalaria' and 'EMOD' in models_to_run:
    #    #submit_combine_results(exp)  # combined benchmarking.csv
    #    submit_run_pyscript(exp, pyscript='benchmark_plots.py',
    #    shname='run_benchmark_plots.sh', job_id='job_id_EMODanalyze')
