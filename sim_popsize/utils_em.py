import copy
import os
from typing import List, Dict
import emod_api.demographics.PreDefinedDistributions as Distributions
import emodpy_malaria.demographics.MalariaDemographics as Demographics
import pandas as pd
from COMPS import AuthManager
from emodpy_malaria.reporters.builtin import *
from idmtools.core import ItemType
from idmtools.entities.iplatform import IPlatform
from idmtools.entities.simulation import Simulation


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
    demog = Demographics.from_template_node(lat=1, lon=2, pop=1000, name="Example_Site")
    demog.SetEquilibriumVitalDynamics()

    age_distribution = Distributions.AgeDistribution_SSAfrica
    demog.SetAgeDistribution(age_distribution)

    return demog


def build_standard_campaign_object(manifest):
    import emod_api.campaign as campaign
    campaign.set_schema(manifest.schema_file)
    return campaign


def add_monthly_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                        yr_plusone=True, age_bins=[0.25, 2, 5, 10, 125],
                        prefix='Monthly_'):
    if tot_year is None: tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')
    for year in range(num_year):
        sim_year = tot_year - num_year + year
        start = yr_plusone + 365 * sim_year
        desc = prefix + '%d' % (sim_year + sim_start_year)
        add_malaria_summary_report(task, manifest, start_day=start, end_day=start + 365 - 1, age_bins=age_bins,
                                   reporting_interval=30, filename_suffix=desc, pretty_format=False)


def add_annual_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                       yr_plusone=True, age_bins=[0.25, 2, 5, 10, 125],
                       prefix='Annual_', ipfilter=''):
    if tot_year is None: tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')
    sim_year = tot_year - num_year
    start = yr_plusone + 365 * sim_year
    desc = prefix + '%dto%d' % (sim_year + sim_start_year, tot_year + sim_start_year - 1)

    add_malaria_summary_report(task, manifest, start_day=start, end_day=start + (num_year * 365) - 1,
                               age_bins=age_bins, reporting_interval=365,
                               filename_suffix=desc, pretty_format=False)


def _get_serialized_filenames(num_cores, timesteps):
    if num_cores == 1:
        serialized_list = [f"state-{str(timesteps).zfill(5)}.dtk"]
    else:
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
