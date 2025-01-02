import os
import sys
import json
import subprocess
from functools import partial
from EMOD.functions.reporters import add_annual_reports, add_daily_reports, add_monthly_reports, add_5daily_reports
from EMOD.functions.EMOD_functions import build_burnin_df, all_campaigns, set_param, SwpFn, ItvFn, CfgFn, sweep_functions, habitat_setup, climate_setup
from EMOD.functions.forcedEIR import mAb_vs_EIR

import emodpy_malaria.malaria_config as malaria_config
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.entities.experiment import Experiment
sys.path.append('../')
import manifest
from utility.helper_slurm import shell_header_quest, write_txt


def submit_run_EMOD(exp, scen_df):
    """
    Submit and run an EMOD experiment, parameterizing various steps involved in the simulation.
    This function sets up the experiment, configures input files, manages reporting, and submits the experiment.

    This function handles the creation and configuration of the EMOD task based on the provided
    experiment parameters, including setting up entomology, serialized input data, and specifying
    how to handle different simulation steps (e.g., 'pickup', 'burnin'). It also schedules necessary
    reports for analysis and prepares the experiment for execution. The experiment is then submitted
    for execution on the provided platform, and the experiment analysis is scheduled.

    Args:
        exp (ExperimentConfig): An instance of the `ExperimentConfig` class that contains all the parameters
                                necessary to configure and run the EMOD simulation. This includes simulation
                                duration, entomology mode, burn-in period, platform configuration, and more.
        scen_df (pandas.DataFrame): A DataFrame containing the scenario data to be used for the experiment.
                                    The dataframe should include the scenario IDs and relevant parameters
                                    that define the experiment conditions.

    Returns:
        experiment (Experiment): The configured and submitted `Experiment` object that represents the
                                  EMOD experiment that was created and submitted for execution.

    Raises:
        ValueError: If the experiment configuration or scenario data is incomplete or invalid.

    """
    exp_name = exp.exp_name
    emod_serialized_id = exp.emod_serialized_id
    sim_dur_years = exp.sim_dur_years
    entomology_mode = exp.entomology_mode
    emod_step = exp.emod_step
    burnin = exp.emod_burnin
    platform = exp.platform
    agebins = exp.agebins
    sim_start_year_emod = exp.sim_start_year_emod

    # create EMODTask
    print("Creating EMODTask (from files)...")
    task = config_task(platform, exp)
    task = build_demog(task,exp)

    if entomology_mode == 'dynamic':
        task.common_assets.add_directory(os.path.join(manifest.input_dir, "example_weather"), relative_path="climate")

    if emod_step == 'pickup':
        serialized_df = build_burnin_df(emod_serialized_id, platform, burnin * 365)
        serialized_df = serialized_df.drop(columns=['x_Temporary_Larval_Habitat'], errors='ignore')
        scen_df_pickup = scen_df.merge(serialized_df, on=['scen_id'],
                                       how='inner')  ## FIXME when running expanded pickup from burnin
        builder = config_sweep_builder_pickup(exp, scen_df_pickup)
    else:
        builder = config_sweep_builder(exp, scen_df)

    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, 
                       num_year=sim_dur_years, detection_threshold=exp.detectionLimit)

    if emod_step != 'burnin':  # do not generate monthly reports for burnin
        if 'daily' in exp.analyzer_list:
            add_daily_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years,
                              detection_threshold=exp.detectionLimit) #We shouldn't generate daily reports unless specified
        add_monthly_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years,
                            detection_threshold=exp.detectionLimit)
        if '5day' in exp.analyzer_list or 'cc_step' in exp.analyzer_list:  # Note, we will not want to always run 5 days using the analyzer_list as a flag to include this reporter  or not
            add_5daily_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years,
                               detection_threshold=exp.detectionLimit)

    # Create experiment from builder and run
    experiment = Experiment.from_builder(builder, task, name=exp_name)
    experiment.run(wait_until_done=False, platform=platform)

    # Additional step to schedule analyzer
    experiment.hpc = exp.hpc
    experiment.sh_hpc_config = exp.sh_hpc_config
    experiment.mem_increase_factor = exp.mem_increase_factor
    experiment.EMOD_venv = exp.EMOD_venv
    experiment.analyzer_script = exp.analyzer_script
    experiment.job_directory = exp.job_directory
    experiment.emod_step = exp.emod_step
    experiment.start_end = [sim_start_year_emod, sim_start_year_emod + sim_dur_years - 1]

    submit_analyze_EMOD(experiment, platform)
    print(f"Experiment submission {experiment.uid} succeeded.")
    return experiment


def config_task(platform, exp):
    """
    Configure and create an EMODTask for running EMOD.
    This function initializes an EMODTask by loading configuration files, setting up custom campaign parameters,
    and configuring simulation parameters.

    Args:
        platform (str): The platform on which the simulation is to be executed (e.g., HPC, local machine).
        exp (ExperimentConfig): An instance of the `ExperimentConfig` class containing all necessary parameters
                                for configuring the EMOD simulation, such as simulation duration, entomology mode,
                                and other experiment-specific settings.

    Returns:
        EMODTask: An instance of the `EMODTask` class that is configured with the relevant experiment settings
                  and is ready to be run on the specified platform.

    Raises:
        FileNotFoundError: If the required configuration files (e.g., "config.json", schema files) are not found
                            at the specified paths.
        ValueError: If there are any issues in setting up the EMODTask, such as missing or incorrect experiment parameters.

    """
    print("Creating EMODTask (from files)...")
    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=build_standard_campaign_object,
        schema_path=manifest.schema_file,
        param_custom_cb=set_config_parameters,  # (config = config, exp = exp),
        ep4_custom_cb=None,
        demog_builder=None,
        plugin_report=None
    )
    set_emod_exp_parameters(task.config, exp)
    task.set_sif(manifest.SIF_PATH, exp.platform)
    return task


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


def set_config_parameters(config):
    """
    This function is a callback that is passed to emod-api.config to set config parameters,
    including the malaria defaults.
    Args:
        config (object): The configuration object to be modified.
    Returns:
        object: The modified configuration object.
    """
    config = malaria_config.set_team_defaults(config, manifest)
    return config


def set_emod_exp_parameters(config, exp):
    """
    Set the experiment-specific parameters in the EMOD configuration.
    This function takes an `exp` object containing experiment settings and applies these settings to the
    provided EMOD `config` object. The parameters configured include population size, simulation duration,
    detection thresholds, and serialization settings. The function handles different configurations depending
    on the experiment step (e.g., "burnin" or "pickup").

    Args:
        config (EMODConfig): The EMOD configuration object to be modified with experiment parameters.
        exp (ExperimentConfig): An instance of the `ExperimentConfig` class containing parameters for the simulation,
                                such as population size, duration, detection limits, and serialization settings.

    Returns:
        None: The function modifies the `config` object in place.

    Raises:
        ValueError: If the `exp.emod_step` is not one of the expected values ("burnin", "pickup").

    """
    config.parameters.x_Base_Population = exp.emod_pop_size / 1000
    config.parameters.Simulation_Duration = exp.sim_dur_years * 365
    config.parameters.Report_Detection_Threshold_Blood_Smear_Parasites = exp.detectionLimit
    config.parameters.Report_Detection_Threshold_Blood_Smear_Gametocytes = exp.detectionLimit
    #We may no longer need to indicate blood smear parasites and gametocytes, instead we do need to indicate true parasite density
    config.parameters.Report_Detection_Threshold_True_Parasite_Density = exp.detectionLimit
    config.parameters.Report_Parasite_Smear_Sensitivity = 1
    config.parameters.Birth_Rate_Dependence = "FIXED_BIRTH_RATE"
    config.parameters.Min_Days_Between_Clinical_Incidents = 14  

    
    # Serialization configuration
    if exp.emod_step == 'burnin':
        config.parameters.Serialized_Population_Writing_Type = "TIMESTEP"
        config.parameters.Serialization_Time_Steps = [exp.sim_dur_years * 365]
        config.parameters.Serialization_Mask_Node_Write = 0
        config.parameters.Serialization_Precision = "REDUCED"
    if exp.emod_step == 'pickup':
        config.parameters.Serialized_Population_Reading_Type = "READ"
        config.parameters.Serialization_Mask_Node_Read = 0
        config.parameters.Serialization_Time_Steps = [exp.emod_burnin * 365]


def build_demog(task, exp):
    """
    Builds the demographic structure for the EMOD simulation.
    """
    # Create a Demographics object and set location and population size
    #demog = Demographics.from_template_node(lat=1, lon=2, pop=1000, name="Example_Site")
    demog = json.load(open(os.path.join(exp.emod_input_path,"demographics.json")))
    #This calculation is the same as using crude rate, but jsons don't recognize 
    birthrate = float(34.95*exp.emod_pop_size/365/1000)
    demog["Defaults"]["NodeAttributes"].update({"BirthRate": birthrate})
    with open(os.path.join(exp.emod_input_path, f"demographics_{exp.emod_pop_size}.json"), "w") as outfile: 
        json.dump(demog, outfile)
    task.transient_assets.add_asset(os.path.join(exp.emod_input_path, f"demographics_{exp.emod_pop_size}.json"))
    task.set_parameter("Demographics_Filenames", [f"demographics_{exp.emod_pop_size}.json"])
    task.config.parameters.Age_Initialization_Distribution_Type = "DISTRIBUTION_COMPLEX"
    task.config.parameters.Death_Rate_Dependence = "NONDISEASE_MORTALITY_BY_AGE_AND_GENDER"
    task.config.parameters.Enable_Demographics_Risk = 1
    task.config.parameters.Enable_Initial_Prevalence = 1
    task.config.parameters.Enable_Natural_Mortality = 1
    task.config.parameters.x_Other_Mortality = 1
    return task


def config_sweep_builder(exp, scen_df):
    """
    Builds the demographic structure for the EMOD simulation and updates the task configuration.
    This function reads a demographic template, modifies the birth rate based on the experiment population size,
    and writes the updated demographic data to a new JSON file. It then adds this file to the task as a transient asset
    and configures EMOD simulation parameters related to demographics and mortality.

    Args:
        task (EMODTask): The EMOD task object that represents the simulation run. The task will be updated with
                         demographic data and the relevant parameters.
        exp (ExperimentConfig): An instance of the `ExperimentConfig` class containing the experiment settings,
                                 including population size and input file paths. This object is used to update the
                                 demographics and configuration for the simulation.

    Returns:
        EMODTask: The updated `task` object with demographic and simulation parameters configured.

    """
    builder = SimulationBuilder()
    nseeds = exp.num_seeds
    if exp.emod_step == 'burnin':
        nseeds = exp.num_seeds_burnin
    if exp.entomology_mode == 'forced':
        matAP = 0.1327
        sweeps = [[ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
                   partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.model_input_emod)),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
    elif exp.entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
                   CfgFn(habitat_setup, exp, row=row),
                   SwpFn(climate_setup,  seasonality = row.seasonality),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.model_input_emod),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
    else:
        raise ValueError(f'{exp.entomology_mode} not valid')

    if exp.emod_calib_params: #This will allow us to vary EMOD parameters associated with NU's within-host calibration efforts.
        from EMOD.functions.calib_params import get_emod_calib_params
        calib_params = get_emod_calib_params(exp,scen_df)
        for i in range(0, len(calib_params)):
            sweeps[i] = sweeps[i] + calib_params[i]
    builder.add_sweep_definition(sweep_functions, sweeps)
    return [builder]


def config_sweep_builder_pickup(exp, scen_df_pickup):
    """
    Configures the sweep builder for an EMOD experiment in 'pickup' mode, where a previous simulation's state
    is loaded to continue the experiment.

    This function creates a sweep configuration based on the experiment settings and the given scenario data frame.
    It sets up intervention strategies, serialized population paths, and entomology-related parameters for both
    'forced' and 'dynamic' entomology modes. It also handles adding calibration parameters if specified.

    Args:
        exp (ExperimentConfig): The experiment configuration object containing various experiment parameters,
                                 such as entomology mode, intervention list, number of seeds, and serialized
                                 population settings.
        scen_df_pickup (pandas.DataFrame): The scenario data frame containing the specific scenario settings for
                                            each sweep, including serialized population paths and filenames.

    Returns:
        list: A list containing the configured `SimulationBuilder` object with the sweep definition added.

    Raises:
        ValueError: If the `entomology_mode` in `exp` is not recognized ('forced' or 'dynamic').

    """
    builder = SimulationBuilder()
    nseeds = exp.num_seeds
    if exp.entomology_mode == 'forced':
        matAP = 0.1327
        sweeps = [[
            ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
            partial(set_param, param='Serialized_Population_Path',
                    value=os.path.join(row["serialized_file_path"], "output")),
            partial(set_param, param='Serialized_Population_Filenames', value=row["Serialized_Population_Filenames"]),
            partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.model_input_emod)),
            partial(set_param, param='Run_Number', value=s)]
            for i, row in scen_df_pickup.iterrows()
            for s in range(nseeds)]
    elif exp.entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
                   CfgFn(habitat_setup, exp, seasonality = row.seasonality),
                   SwpFn(climate_setup,  seasonality = row.seasonality),
                   partial(set_param, param='Serialized_Population_Path',
                           value=os.path.join(row["serialized_file_path"], "output")),
                   partial(set_param, param='Serialized_Population_Filenames',
                           value=row["Serialized_Population_Filenames"]),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.model_input_emod),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df_pickup.iterrows()
                  for s in range(nseeds)]
    else:
        raise ValueError(f'{exp.entomology_mode} not valid')

    if exp.emod_calib_params: #This will allow us to vary EMOD parameters associated with  NU's within-host calibration efforts.
        from EMOD.scaffolds.calib_params import get_emod_calib_params
        calib_params = get_emod_calib_params(exp,scen_df_pickup)
        for i in range(0, len(calib_params)):
            sweeps[i] = sweeps[i] + calib_params[i]
    builder.add_sweep_definition(sweep_functions, sweeps)
    return [builder]


def submit_analyze_EMOD(experiment, platform, t='04:00:00', memG=20):
    """
    Submits a job to analyze EMOD simulation outputs on a high-performance computing (HPC) platform.

    This function creates a SLURM shell script for submitting an analysis job, which processes the EMOD simulation
    outputs. It sets up the job environment, defines dependencies on previous jobs, and submits the job to the platform.

    Args:
        experiment (Experiment): The experiment object containing relevant parameters such as job directory,
                                  EMOD virtual environment, and analyzer script(s).
        platform (Platform): The platform object representing the HPC system where the job will be submitted.
        t (str, optional): The time limit for the job in HH:MM:SS format. Defaults to '04:00:00'.
        memG (int, optional): The amount of memory (in GB) allocated for the job. Defaults to 20 GB.

    Returns:
        None
    """

    # Get the current working directory
    wdir = os.path.abspath(os.path.dirname(__file__))

    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(experiment.sh_hpc_config, t, memG, job_name='analyze_EMODsim',
                                     mem_scl=experiment.mem_increase_factor)

    # Get the EMODpy virtual environment path
    emodpy_venv = experiment.EMOD_venv

    # Generate the Python commands to run additional scripts
    # If any, add  python or R scripts to directly run after analyzer can be added below
    pycommand = '\n'.join(
        [f'\npython {scr} -d {experiment.job_directory} -i {experiment.id}' for scr in experiment.analyzer_script])

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
