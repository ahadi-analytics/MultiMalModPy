import copy
import os
from typing import List, Dict, Any
import emod_api.demographics.PreDefinedDistributions as Distributions
import emodpy_malaria.demographics.MalariaDemographics as Demographics
import pandas as pd
import numpy as np
from COMPS import AuthManager
from emodpy_malaria.reporters.builtin import *
from idmtools.core import ItemType
from idmtools.entities.iplatform import IPlatform
from idmtools.entities.simulation import Simulation
from EMOD.scaffolds.forcedEIR import *
from EMOD.scaffolds.dynamicEIR import *
from EMOD.scaffolds.interventions import treatment_camp_simple
from EMOD.utils import *


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


def build_standard_campaign_object(manifest):
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


def all_campaigns(camp, row):
    """
    Wrapper functions to define all campaigns to go into the campaigns.json
    To be expanded with SMC and other interventions as needed, and use if's to define applicability
    """

    if row.entomology_mode == 'forced':
        set_inputEIR_seasonality(camp, float(row.eir), row.seasonality)
    treatment_camp_simple(camp, cm_start=row.cm_start, cm_clinical=row.cm_clinical, cm_severe=row.cm_severe)

    return {'scen_id': int(row.scen_id)}


def add_monthly_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                        yr_plusone=True, age_bins=[0.25, 2, 5, 10, 125],
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
    if tot_year is None: tot_year = num_year
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
                       yr_plusone=True, age_bins=[0.25, 2, 5, 10, 125],
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
    if tot_year is None: tot_year = num_year
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
    # print(list(df.columns))
    # print(df.head())

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
    from pathlib import Path
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
    scen_df_burnin_path = os.path.join(manifest.job_directory, exp.custom_subdir,  exp.SUITEname,exp_name_burnin)
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

