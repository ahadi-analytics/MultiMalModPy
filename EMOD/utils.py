import copy
import os
import sys
import subprocess
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from COMPS import AuthManager
from functools import partial
from EMOD.scaffolds.forcedEIR import *
from EMOD.scaffolds.dynamicEIR import *
from EMOD.scaffolds.interventions import treatment_camp_simple
import emod_api.demographics.PreDefinedDistributions as Distributions
from emodpy_malaria.reporters.builtin import *
import emodpy_malaria.demographics.MalariaDemographics as Demographics
import emodpy_malaria.malaria_config as malaria_config
from emodpy_malaria.interventions.scale_larval_habitats import add_scale_larval_habitats
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.core import ItemType
from idmtools.entities.iplatform import IPlatform
from idmtools.entities.simulation import Simulation
from idmtools.entities.experiment import Experiment

sys.path.append('../')
import manifest
from helper import shell_header_quest, emodpy_module, write_txt


def set_param(simulation, param, value):
    """
    Set specific parameter value
    Args:
        simulation: idmtools Simulation
        param: parameter
        value: new value
    Returns:
        dict
    """
    return simulation.task.set_parameter(param, value)


def build_demog():
    """
    Builds the demographic structure for the EMOD simulation.
    """
    # Create a Demographics object and set location and population size
    demog = Demographics.from_template_node(lat=1, lon=2, pop=1000, name="Example_Site")
    demog.SetEquilibriumVitalDynamics()

    # Set the age distribution for the population
    age_distribution = Distributions.AgeDistribution_SSAfrica
    demog.SetAgeDistribution(age_distribution)

    return demog


def build_standard_campaign_object():
    """
    Builds a standard campaign object for the simulation.
    Args:
        manifest: The manifest object containing the schema file.
    Returns:
        campaign_obj: The built campaign object.
    """
    import emod_api.campaign as camp
    camp.set_schema(manifest.schema_file)
    return camp


def all_campaigns(camp, emod_step = None, row = None, intervention_list = []):
    """
    Wrapper functions to define all campaigns to go into the campaigns.json
    To be expanded with SMC and other interventions as needed, and use if's to define applicability
    """

    if row.entomology_mode == 'forced':
        set_inputEIR_seasonality(camp, float(row.eir), row.seasonality)
    treatment_camp_simple(camp, cm_start=row.cm_start, cm_clinical=row.cm_clinical, cm_severe=row.cm_severe)
    if 'cc_step' in intervention_list and emod_step == 'pickup': #Make sure to include the cc_step change only at pickup simulations.
        eir_df = pd.DataFrame({'WATER_VEGETATION':[row.eir_scalar_emod]}) #TODO: Change our habitat type from water_veg to constant
        add_scale_larval_habitats(camp, df=eir_df,
                                  start_day=row.eir_scalar_timestep_daily,
                                  repetitions = 1)
    return {'scen_id': int(row.scen_id)}


def add_daily_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                        yr_plusone=True, age_bins=[0.5, 1, 2, 5, 10, 15,20, 125],
                        prefix='Daily_'):
    """
    Adds daily reports to the simulation task.
    Args:
        task: The simulation task object.
        manifest: The manifest object containing the necessary information.
        sim_start_year: The starting year of the simulation.
        num_year: The number of years to add monthly reports for.
        tot_year: The total number of years of the simulation.
                  If None, it is set to num_year.
        yr_plusone: Whether to add an extra year to the reporting.
                    If True, reports will cover num_year + 1 years.
                    If False, reports will cover num_year years.
        age_bins: The age bins for reporting.
        prefix: The prefix to be used for the report filenames.
    Raises:
        ValueError: If num_year is greater than tot_year.
    Returns:
        None
    """
    if tot_year is None:
        tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')

    # Write separate monthly reports for each year
    for year in range(num_year):
        sim_year = tot_year - num_year + year
        start = yr_plusone + 365 * sim_year
        desc = prefix + '%d' % (sim_year + sim_start_year)
        add_malaria_summary_report(task, manifest, start_day=start, end_day=start + 365 - 1, age_bins=age_bins,
                                   max_number_reports = 366, reporting_interval=1, filename_suffix=desc, pretty_format=False)

def add_monthly_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                        yr_plusone=True, age_bins=[0.5,1, 2, 5, 10, 15,20,125],
                        prefix='Monthly_'):
    """
    Adds monthly reports to the simulation task.
    Args:
        task: The simulation task object.
        manifest: The manifest object containing the necessary information.
        sim_start_year: The starting year of the simulation.
        num_year: The number of years to add monthly reports for.
        tot_year: The total number of years of the simulation.
                  If None, it is set to num_year.
        yr_plusone: Whether to add an extra year to the reporting.
                    If True, reports will cover num_year + 1 years.
                    If False, reports will cover num_year years.
        age_bins: The age bins for reporting.
        prefix: The prefix to be used for the report filenames.
    Raises:
        ValueError: If num_year is greater than tot_year.
    Returns:
        None
    """
    if tot_year is None:
        tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')

    # Write separate monthly reports for each year
    for year in range(num_year):
        sim_year = tot_year - num_year + year
        start = yr_plusone + 365 * sim_year
        desc = prefix + '%d' % (sim_year + sim_start_year)
        add_malaria_summary_report(task, manifest, start_day=start, end_day=start + 365 - 1, age_bins=age_bins,
                                   reporting_interval=30, filename_suffix=desc, pretty_format=False)


def add_annual_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                       yr_plusone=True, age_bins=[0.5,1, 2, 5, 10, 15, 20, 125],
                       prefix='Annual_', ipfilter=''):
    """
    Adds annual reports to the simulation task.
    Args:
        task: The simulation task object.
        manifest: The manifest object containing the necessary information.
        sim_start_year: The starting year of the simulation.
        num_year: The number of years to add monthly reports for.
        tot_year: The total number of years of the simulation.
                  If None, it is set to num_year.
        yr_plusone: Whether to add an extra year to the reporting.
                    If True, reports will cover num_year + 1 years.
                    If False, reports will cover num_year years.
        age_bins: The age bins for reporting.
        prefix: The prefix to be used for the report filenames.
    Raises:
        ValueError: If num_year is greater than tot_year.
    Returns:
        None
    """
    if tot_year is None:
        tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')
    sim_year = tot_year - num_year
    start = yr_plusone + 365 * sim_year
    desc = prefix + '%dto%d' % (sim_year + sim_start_year, tot_year + sim_start_year - 1)

    # All years in one report file
    add_malaria_summary_report(task, manifest, start_day=start, end_day=start + (num_year * 365) - 1,
                               age_bins=age_bins, reporting_interval=365,
                               filename_suffix=desc, pretty_format=False)


def _get_serialized_filenames(num_cores, timesteps):
    """
    Generates a list of serialized filenames based on the number of cores and timesteps.
    Args:
        num_cores: The number of cores used for parallel simulation.
        timesteps: The number of timesteps.
    Returns:
        A list of serialized filenames.
    """
    if num_cores == 1:
        # For single-core simulation, use a single serialized file
        serialized_list = [f"state-{str(timesteps).zfill(5)}.dtk"]
    else:
        # For multi-core simulation, generate serialized files for each core
        serialized_list = [f"state-{str(timesteps).zfill(5)}-{str(core_count).zfill(3)}.dtk"
                           for core_count in range(num_cores)]
    return serialized_list


def _get_core_counts(sim_id, platform):
    # TODO, get num_cores from simulation in slurm
    # sim = platform.get_item(sim_id, ItemType.SIMULATION, raw=True)
    # sim.refresh(QueryCriteria().select_children('hpc_jobs'))
    # num_cores = int(sim.hpc_jobs[-1].configuration.max_cores)
    num_cores = 1
    return num_cores


def get_workdir_from_simulations(platform: 'IPlatform', comps_simulations: List[Simulation]) -> Dict[str, str]:
    """
    Get COMPS filepath
    Args:
        platform: idmtools Platform
        comps_simulations: COMPS Simulations
    Returns: dictionary with simid as key and filepath as value
    """

    if platform.environment.upper() == "SLURMSTAGE" or platform.environment.upper() == "CALCULON":
        mounts = AuthManager.get_environment_macros(platform.environment)['DOCKER_MOUNTS']
        mounts = {v[0]: v[1:4] for v in [m.split(';') for m in mounts.split('|')]}
        # pretend I'm on Linux and set the Linux mapping environment variables
        for k, v in mounts.items():
            os.environ[k] = ';'.join([v[0], v[2]])
    sim_work_dir = {str(sim.id): sim.hpc_jobs[-1].working_directory for sim in comps_simulations if sim.hpc_jobs}

    return sim_work_dir


def create_sim_directory_map(exp_id: str, platform: 'IPlatform'):
    """
        Return a dataframe which contains simulation's working_path and tags.
    Args:
        exp_id: experiment id
        platform: idmtools platform
    Returns:
        dataframe
    """
    # Get idmtools Experiment
    exp = platform.get_item(exp_id, ItemType.EXPERIMENT, raw=False)

    tags_list = []
    for sim in exp.simulations:
        tags = copy.deepcopy(sim.tags)
        tags.update(dict(simid=sim.id))
        tags_list.append(tags)
    df = pd.DataFrame(tags_list)

    if len(df) != len(exp.simulations):
        print(f'Warning: not all jobs in {exp_id} succeeded', ':', )
        print(len(exp.simulations) - len(df), 'unsucceeded')

    simulations = exp.simulations
    dir_list = []
    for sim in simulations:
        dir_dict = {"simid": str(sim.id), "serialized_file_path": platform._op_client.get_directory(sim)}
        dir_list.append(dir_dict)

    df_dir = pd.DataFrame(dir_list)
    df = pd.merge(left=df, right=df_dir, on='simid')

    return df


def build_burnin_df(exp_id: str, platform, serialize_days):
    """
    return dataframe which contains serialized_file_path, serialized_population_filenames
    Args:
        exp_id:
        platform:
    Returns:
        dataframe:
        Run_Number | Serialization_Time_Steps | task_type | sweep_tag | simid | serialized_file_path|Num_Cores|Serialized_Population_Filenames
    Note, Serialized_Population_Filenames depends on n_cores. if n_cores = 2, Serialized_Population_Filenames look
    like these: state-00050-000.dtk, state-00050-001.dtk
    """

    df = create_sim_directory_map(exp_id, platform)
    # add Num_Cores to df
    df["Num_Cores"] = df["simid"].apply(_get_core_counts, platform=platform)

    # try:
    burnin_length_in_days = serialize_days  # int(df["Serialization_Time_Steps"].iloc[0].strip('[]'))
    # except AttributeError:
    # different versions of pandas save this as either a string or a list
    # burnin_length_in_days = df["Serialization_Time_Steps"].iloc[0][-1]

    df["Serialized_Population_Filenames"] = df["Num_Cores"].apply(_get_serialized_filenames,
                                                                  timesteps=burnin_length_in_days)
    df = df.reset_index(drop=True)
    return df


def get_burnin_exp_name(serialized_df):
    """
    Retrieve the name of the EMOD burnin experiment from the metadata.json file
    Parameters:
    serialized_df (DataFrame): A pandas DataFrame containing serialized data information.
    Returns:
    str: The name of the burnin experiment as defined in the serialization df from emod_serialized_id.
    """

    import json
    metadata_path = serialized_df.serialized_file_path[0].parent / 'metadata.json'
    with open(metadata_path, 'r') as json_file:
        metadata = json.load(json_file)
    return metadata['name']


def get_scendf_burnin(exp, emod_serialized_id, manifest, platform, burnin):
    """
    Load the scenarios.csv file associated with the EMOD burnin experiment.
    Parameters:
    exp (Experiment): An experiment object containing information about the experiment.
    emod_serialized_id (str): The serialized ID for the EMOD input data.
    manifest (Manifest): A manifest object containing job directory information.
    platform (Platform): A platform object specifying the execution platform.
    burnin (int): The duration of the burnin period in days.
    Returns:
    pandas.DataFrame: A DataFrame containing scenarios from the burn-in experiment.
    """

    serialized_df = build_burnin_df(emod_serialized_id, platform, burnin * 365)
    exp_name_burnin = get_burnin_exp_name(serialized_df)
    scen_df_burnin_path = os.path.join(exp.suite_directory, exp_name_burnin)
    scen_df_burnin = pd.read_csv(os.path.join(scen_df_burnin_path, 'scenarios.csv'))
    return scen_df_burnin


def sweep_functions(simulation: Simulation, func_list: List) -> Dict[str, Any]:
    """
    Obtained from IDM's emodpy-snt framework that had been modified for bf-seasonal
    https://github.com/numalariamodeling/bf-seasonal/blob/main/sweeping.py

    Apply funcs on simulation.
    Args:
        simulation: idmtools Simulation
        func_list: a list of functions

    Returns:
        dict of parameters
    """
    tags_updated = {}
    for func in func_list:
        tags = func(simulation)
        if tags:
            tags_updated.update(tags)
    return tags_updated


class ItvFn:
    """
    Obtained from IDM's emodpy-snt framework that had been modified for bf-seasonal
    https://github.com/numalariamodeling/bf-seasonal/blob/main/sweeping.py

    Sweeping utility: works for sweeping on interventions.
    Requirements:
     - func is a method that takes campaign as first parameter
     - func return a dict

    Returns:
        dict
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, simulation: Simulation):
        import emod_api.campaign as campaign
        campaign.reset()
        md = self.func(campaign, *self.args, **self.kwargs)

        # add events
        events = campaign.campaign_dict["Events"]
        simulation.task.campaign.add_events(events)

        # update config for adhoc events
        adhoc_events = campaign.get_adhocs()
        if len(adhoc_events) > 0:
            print("Found adhoc events in campaign. Needs some special processing behind the scenes.")
            if "Custom_Individual_Events" in simulation.task.config.parameters:
                ev_exist = set(simulation.task.config.parameters.Custom_Individual_Events)
                ev_addhoc = set(adhoc_events.keys())
                simulation.task.config.parameters.Custom_Individual_Events = list(ev_exist.union(ev_addhoc))
            else:
                simulation.task.config.parameters.Custom_Individual_Events = list(set(adhoc_events.keys()))

        # Make sure we cast numpy types into normal system types
        if md:
            for k, v in md.items():
                if isinstance(v, (np.int64, np.float64, np.float32, np.uint32, np.int16, np.int32)):
                    md[k] = v.item()

        return md


class CfgFn:
    """
    Obtained from IDM's emodpy-snt framework that had been modified for bf-seasonal
    https://github.com/numalariamodeling/bf-seasonal/blob/main/sweeping.py

    Sweeping utility: works for sweeping on config parameters.
    Requirements:
     - func is a method that takes config as first parameter
     - func return a dict

    Returns:
        dict
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, simulation: Simulation):
        md = self.func(simulation.task.config, *self.args, **self.kwargs)

        # Make sure we cast numpy types into normal system types
        if md:
            for k, v in md.items():
                if isinstance(v, (np.int64, np.float64, np.float32, np.uint32, np.int16, np.int32)):
                    md[k] = v.item()

        return md


def config_task(platform, exp):
    print("Creating EMODTask (from files)...")
    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=build_standard_campaign_object,
        schema_path=manifest.schema_file,
        param_custom_cb=set_config_parameters,  # (config = config, exp = exp),
        ep4_custom_cb=None,
        demog_builder=build_demog,
        plugin_report=None
    )
    set_emod_exp_parameters(task.config, exp)
    task.set_sif(manifest.SIF_PATH, exp.platform)
    return task


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
    return config
 

def set_emod_exp_parameters(config, exp):
    config.parameters.x_Base_Population = exp.pop_size / 1000
    config.parameters.Simulation_Duration = exp.sim_dur_years * 365
    config.parameters.Report_Detection_Threshold_Blood_Smear_Parasites = exp.detectionLimit
    config.parameters.Report_Detection_Threshold_Blood_Smear_Gametocytes = exp.detectionLimit


    # Parameter configurations on climate for dynamic EIR
    if exp.entomology_mode == 'dynamic':
        malaria_config.add_species(config, manifest, ["gambiae"])  # , "arabiensis", "funestus"

        seasonality_type = exp.seasonality[0]  # 'perennial'  # 'seasonal', 'example'  #FIXME enable sweeping
        config.parameters.Air_Temperature_Filename = os.path.join('climate',
                                                                  f'{seasonality_type}_air_temperature_daily.bin')
        config.parameters.Land_Temperature_Filename = os.path.join('climate',
                                                                   f'{seasonality_type}_air_temperature_daily.bin')
        config.parameters.Rainfall_Filename = os.path.join('climate', f'{seasonality_type}_rainfall_daily.bin')
        config.parameters.Relative_Humidity_Filename = os.path.join('climate',
                                                                    f'{seasonality_type}_relative_humidity_daily.bin')

    # Serialization configuration
    if exp.emod_step == 'burnin':
        config.parameters.Serialized_Population_Writing_Type = "TIMESTEP"
        config.parameters.Serialization_Time_Steps = [exp.sim_dur_years * 365]
        config.parameters.Serialization_Mask_Node_Write = 0
        config.parameters.Serialization_Precision = "REDUCED"
    if exp.emod_step == 'pickup':
        config.parameters.Serialized_Population_Reading_Type = "READ"
        config.parameters.Serialization_Mask_Node_Read = 0
        config.parameters.Serialization_Time_Steps = [exp.burnin * 365]


def config_sweep_builder_pickup(exp, scen_df_pickup):
    builder = SimulationBuilder()
    nseeds = exp.num_seeds
    if exp.entomology_mode == 'forced':
        matAP = 0.1327
        sweeps = [[
            ItvFn(all_campaigns, emod_step = exp.emod_step, row=row, intervention_list = exp.intervention_list),
            partial(set_param, param='Serialized_Population_Path',
                    value=os.path.join(row["serialized_file_path"], "output")),
            partial(set_param, param='Serialized_Population_Filenames', value=row["Serialized_Population_Filenames"]),
            partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.eir)),
            partial(set_param, param='Run_Number', value=s)]
            for i, row in scen_df_pickup.iterrows()
            for s in range(nseeds)]

    elif exp.entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, emod_step = exp.emod_step, row=row, intervention_list = exp.intervention_list),
                   partial(set_param, param='Serialized_Population_Path',
                           value=os.path.join(row["serialized_file_path"], "output")),
                   partial(set_param, param='Serialized_Population_Filenames',
                           value=row["Serialized_Population_Filenames"]),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.x_Temporary_Larval_Habitat),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df_pickup.iterrows()
                  for s in range(nseeds)]
    else:
        raise ValueError(f'{exp.entomology_mode} not valid')
        
    if exp.emod_calib_params: #This will allow us to vary EMOD parameters associated with  NU's within-host calibration efforts.
        from EMOD.scaffolds.calib_params import get_emod_calib_params
        calib_params = get_emod_calib_params(exp,scen_df_pickup)
        sweeps = sweeps + calib_params


    builder.add_sweep_definition(sweep_functions, sweeps)

    return [builder]


def config_sweep_builder(exp, scen_df):
    builder = SimulationBuilder()
    nseeds = exp.num_seeds
    if exp.emod_step == 'burnin':
        nseeds = exp.num_seeds_burnin
    if exp.entomology_mode == 'forced':
        matAP = 0.1327
        sweeps = [[ItvFn(all_campaigns, emod_step = exp.emod_step, row=row, intervention_list = exp.intervention_list),
                   partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.eir)),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
    elif exp.entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, emod_step = exp.emod_step, row=row, intervention_list = exp.intervention_list),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.x_Temporary_Larval_Habitat),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
    else:
        raise ValueError(f'{exp.entomology_mode} not valid')
    
    if exp.emod_calib_params: #This will allow us to vary EMOD parameters associated with NU's within-host calibration efforts.
        from EMOD.scaffolds.calib_params import get_emod_calib_params
        calib_params = get_emod_calib_params(exp,scen_df)
        sweeps = sweeps + calib_params
    

    builder.add_sweep_definition(sweep_functions, sweeps)

    return [builder]


def submit_run_EMOD(exp, scen_df):
    """
    This function is designed to be a parameterized version of the sequence of things we do
    every time we run an emod experiment.
    """
    exp_name = exp.exp_name
    emod_serialized_id = exp.emod_serialized_id
    sim_dur_years = exp.sim_dur_years
    entomology_mode = exp.entomology_mode
    emod_step = exp.emod_step
    burnin = exp.burnin
    platform = exp.platform
    agebins = exp.agebins
    sim_start_year_em = exp.sim_start_year_em

    # create EMODTask
    print("Creating EMODTask (from files)...")
    task = config_task(platform, exp)

    if entomology_mode == 'dynamic':
        task.common_assets.add_directory(os.path.join(manifest.input_dir, "example_weather"), relative_path="climate")

    if emod_step == 'pickup':
        serialized_df = build_burnin_df(emod_serialized_id, platform, burnin * 365)
        serialized_df = serialized_df.drop(columns=['x_Temporary_Larval_Habitat'])
        scen_df_pickup = scen_df.merge(serialized_df, on=['scen_id'],
                                       how='inner')  ## FIXME when running expanded pickup from burnin
        builder = config_sweep_builder_pickup(exp, scen_df_pickup)
    else:
        builder = config_sweep_builder(exp, scen_df)

    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years)
    if emod_step != 'burnin':  # do not generate monthly reports for burnin
        if 'cc_step' in exp.intervention_list:
            add_daily_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_em, num_year=sim_dur_years) #We shouldn't generate daily reports unless necessary (and right now its only necessary with cc_step perterbation)
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
    return experiment


def submit_analyze_EMOD(experiment, platform, t='04:00:00', memG=20):
    """
    Submits a job to analyze EMOD simulation results.

    Args:
        experiment (object): The experiment object containing job directory and other information.
        platform (object): The platform object representing the HPC platform.

    """

    # Get the current working directory
    wdir = os.path.abspath(os.path.dirname(__file__))

    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(experiment.sh_hpc_config, t, memG, job_name='analyze_EMODsim',
                                     mem_scl=experiment.mem_increase_factor)

    # Get the EMODpy virtual environment path
    emodpy_venv = emodpy_module(experiment.hpc)

    # Generate the Python commands to run additional scripts
    # If any, add  python or R scripts to directly run after analyzer can be added below
    pycommand = '\n'.join(
        [f'\npython {scr} -d {experiment.job_directory} -i {experiment.id}' for scr in experiment.analyzer])

    # Write the shell script to a file
    script_path = os.path.join(experiment.job_directory, 'run_analyzer_EMOD.sh')
    file = open(script_path, 'w')
    file.write(header_post + emodpy_venv + f'\ncd {wdir}' + pycommand)
    file.close()

    # Get the job ID
    job_id = platform._op_client.get_job_id(experiment.id, experiment.item_type)[0]

    # Submit the job with dependency on the previous job
    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(experiment.job_directory))

    # Extract the SLURM job ID from the output
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]

    # Print the submitted job ID
    print(f'Submitted EMOD analyzer - job id: {slurm_job_id}')

    # Write out the job IDs and experiment ID to files
    write_txt(job_id, experiment.job_directory, 'job_id_EMODsim.txt')
    write_txt(experiment.id, experiment.job_directory, 'exp_id_EMODsim.txt')
    write_txt(slurm_job_id, experiment.job_directory, 'job_id_EMODanalyze.txt')
