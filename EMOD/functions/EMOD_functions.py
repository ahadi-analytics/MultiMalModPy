import os
import copy
from typing import List, Dict, Any
import pandas as pd
import numpy as np
from COMPS import AuthManager
from EMOD.functions.forcedEIR import *
from EMOD.functions.interventions import *
from emodpy_malaria.interventions.scale_larval_habitats import add_scale_larval_habitats
from emodpy_malaria.interventions.outbreak import add_outbreak_individual
from emodpy_malaria.reporters.builtin import *
import emodpy_malaria.malaria_config as malaria_config
from idmtools.core import ItemType
from idmtools.entities.iplatform import IPlatform
from idmtools.entities.simulation import Simulation
import sys

sys.path.append('../../')
import manifest


def build_burnin_df(exp_id: str, platform, serialize_days):
    """
    Builds a DataFrame containing information about serialized files and simulation configurations
    for the burn-in process of the experiment.
    The serialized population filenames are in the format: `state-{step}-{core}.dtk`, where `{step}` refers to
    the serialization timestep and `{core}` refers to the core number.
    The `Serialized_Population_Filenames` field varies based on the number of cores used. For example,
    if `Num_Cores = 2`, the filenames will look like this: `state-00050-000.dtk` and `state-00050-001.dtk`.

    Args:
        exp_id (str): The unique experiment identifier for which the burn-in DataFrame is being created.
        platform (object): The platform object that represents the high-performance computing environment.
                           Used to retrieve core count and other platform-related information.
        serialize_days (int): The number of days over which serialization occurs. This is used to determine
                               the length of time steps for the serialized population.

    Returns:
        pd.DataFrame: A DataFrame containing the following columns:
            - `Run_Number`: The simulation run number.
            - `Serialization_Time_Steps`: The number of time steps for serialization.
            - `task_type`: Type of the task being run (e.g., simulation).
            - `sweep_tag`: The tag associated with the current simulation sweep.
            - `simid`: The unique simulation ID.
            - `serialized_file_path`: Path to the serialized files for the simulation.
            - `Num_Cores`: The number of cores allocated for the simulation.
            - `Serialized_Population_Filenames`: The filenames of the serialized population files.

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


def all_campaigns(camp, exp=None, row=None, intervention_list=[]):
    """
    Defines and adds various interventions and campaigns to be included in the `campaigns.json` for EMOD.
    The function serves as a wrapper that conditionally applies different campaigns based on the values in
    the provided `row` (e.g., from a scenario DataFrame), experiment configuration (`exp`), and the
    `intervention_list` parameter.

    Args:
        camp (object): The campaign object to which the interventions will be applied.
        exp (object, optional): The experiment configuration containing simulation parameters (default is None).
        row (pandas.Series, optional): A row of data containing scenario parameters for the campaign (default is None).
        intervention_list (list, optional): List of interventions to be included in the simulation (default is empty list).

    Returns:
        dict: A dictionary containing the scenario ID (scen_id) associated with the campaign.
              Example: {'scen_id': 1}

    """

    ## If forced EIR, treated as campaign in EMOD
    if row.entomology_mode == 'forced':
        set_inputEIR_seasonality(camp, float(row.transmission_intensity_EMOD), row.seasonality)

    # Case management
    treatment_camp_simple(camp, cm_start=row.cm_start, cm_clinical=row.cm_clinical, cm_severe=row.cm_severe)

    ## Carrying capacity step change
    if 'cc_step' in intervention_list and (exp.emod_step == 'pickup' or exp.emod_step is None):  
    # Make sure to include the cc_step change only at pickup simulations.
        camp = carrying_capacity(camp, row)
        
    if exp.emod_importation_rate != 0:
        ncases_per_year_per1000pop = (exp.emod_importation_rate * exp.emod_pop_size) / 1000
        add_outbreak_individual(camp, start_day=1, target_num_individuals=ncases_per_year_per1000pop,
                                repetitions=-1, timesteps_between_repetitions=365)

    # SMC currently not supported
    # SMC using PKPD model
    #if 'smc' in intervention_list and exp.emod_step == 'pickup':
    #    print(row.smc_coverage)
    #    if row.transmission_intensity_EMOD == 4:
    #        start_array = [366, 731, 1096, 1461, 1826]
    #    elif row.transmission_intensity_EMOD == 8:
    #        start_array = [366, 731, 1096, 1461, 1826]
    #    else:
    #        start_array = [335, 700, 1065, 1430, 1795]
    #        # add_drug_campaign(camp, campaign_type = "SMC", start_days = [396,761,1126,1491,1856],
    #    smc_campaign(camp, row, start_array)

    return {'scen_id': int(row.scen_id)}


def habitat_setup(config, exp, row):
    """
    Sets up the habitat parameters for malaria vector species in EMOD, based on the climate seasonality
    and experiment configuration. The function configures different habitat types ("CONSTANT" or "TEMPORARY_RAINFALL")
    and larval capacity based on the seasonality condition ('perennial' or 'seasonal') for the specified malaria species (gambiae).

    Args:
        config (object): The configuration object that holds the simulation settings and parameters.
        exp (object): The experiment object containing the population size and other simulation configurations.
        row (pandas.Series): A row of data containing scenario-specific information, such as seasonality.

    Returns:
        None
    """

    # Parameter configurations on climate for dynamic EIR
    malaria_config.add_species(config, manifest, ["gambiae"])  # , "arabiensis", "funestus"
    max_capacity_multiplier = (exp.emod_pop_size / 1000)
    import emod_api.config.default_from_schema_no_validation as dfs
    if row.seasonality == 'perennial':
        habitat1 = dfs.schema_to_config_subnode(manifest.schema_file, ["idmTypes", "idmType:VectorHabitat"])
        habitat1.parameters.Habitat_Type = "CONSTANT"
        habitat1.parameters.Max_Larval_Capacity = 10000000 * max_capacity_multiplier
        habitat_list = [{"Habitat_Type": habitat1.parameters.Habitat_Type,
                         "Max_Larval_Capacity": habitat1.parameters.Max_Larval_Capacity}]
        malaria_config.set_species_param(config, 'gambiae', parameter="Habitats", value=habitat_list, overwrite=True)
    else:
        habitat1 = dfs.schema_to_config_subnode(manifest.schema_file, ["idmTypes", "idmType:VectorHabitat"])
        habitat1.parameters.Habitat_Type = "TEMPORARY_RAINFALL"
        habitat1.parameters.Max_Larval_Capacity = 90000000 * max_capacity_multiplier
        habitat_list = [{"Habitat_Type": habitat1.parameters.Habitat_Type,
                         "Max_Larval_Capacity": habitat1.parameters.Max_Larval_Capacity}]
        malaria_config.set_species_param(config, 'gambiae', parameter="Habitats", value=habitat_list, overwrite=True)
        habitat2 = dfs.schema_to_config_subnode(manifest.schema_file, ["idmTypes", "idmType:VectorHabitat"])
        habitat2.parameters.Habitat_Type = "CONSTANT"
        habitat2.parameters.Max_Larval_Capacity = 2850000 * max_capacity_multiplier
        habitat_list = [{"Habitat_Type": habitat2.parameters.Habitat_Type,
                         "Max_Larval_Capacity": habitat2.parameters.Max_Larval_Capacity}]
        malaria_config.set_species_param(config, 'gambiae', parameter="Habitats", value=habitat_list, overwrite=False)


def climate_setup(task, seasonality=None):
    """
    The function sets up the climate input filenames for EMOD.

    Args:
        task (object): The task object that holds the configuration and parameters for the simulation.
        seasonality (str, optional): The seasonality type (e.g., 'perennial' or 'seasonal') that determines the climate files.
                                      If not provided, defaults to None.

    Returns:
        None
    """
    task.config.parameters.Climate_Model = "CLIMATE_BY_DATA"
    task.config.parameters.Air_Temperature_Filename = os.path.join('climate',
                                                                   f'{seasonality}_air_temperature_daily.bin')
    task.config.parameters.Land_Temperature_Filename = os.path.join('climate',
                                                                    f'{seasonality}_air_temperature_daily.bin')
    task.config.parameters.Rainfall_Filename = os.path.join('climate', f'{seasonality}_rainfall_daily.bin')
    task.config.parameters.Relative_Humidity_Filename = os.path.join('climate',
                                                                     f'{seasonality}_relative_humidity_daily.bin')


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


def get_burnin_exp_name(serialized_df):
    """
    Retrieve the name of the EMOD burnin experiment from the metadata.json file
    Args:
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

    Args:
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


class SwpFn:
    """
    Sweeping utility: works for sweeping on report, demographics, migrations and climate, etc.
    Requirements:
     - func is a method that takes task as first parameter
     - func return a dict
    Returns:
        dict
    """

    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def __call__(self, simulation: Simulation):
        md = self.func(simulation.task, *self.args, **self.kwargs)
        # Make sure we cast numpy types into normal system types
        if md:
            for k, v in md.items():
                if isinstance(v, (np.int64, np.float64, np.float32, np.uint32, np.int16, np.int32)):
                    md[k] = v.item()
        return md
