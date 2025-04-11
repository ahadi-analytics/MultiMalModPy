import os
import sys
import json
import subprocess
import math
import csv
from functools import partial
from EMOD.functions.reporters import add_annual_reports, add_daily_reports, add_monthly_reports, add_5daily_reports
from EMOD.functions.EMOD_functions import build_burnin_df, all_campaigns, set_param, SwpFn, ItvFn, CfgFn, sweep_functions, habitat_setup, climate_setup
from EMOD.functions.forcedEIR import mAb_vs_EIR
from emodpy_malaria.reporters.builtin import *
import emod_api.config.default_from_schema_no_validation as dfs
import emodpy_malaria.vector_config as vector_config
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.entities.experiment import Experiment
sys.path.append('../')
import manifest
from utility.helper_slurm import shell_header_quest, write_txt, submit_run_pyscript

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
    import emod_malaria.bootstrap as dtk
    import pathlib
    dtk.setup(pathlib.Path(manifest.eradication_path).parent)
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
        task.common_assets.add_directory(os.path.join(manifest.input_dir, "climate"), relative_path="climate")

    if emod_step == 'pickup':
        serialized_df = build_burnin_df(emod_serialized_id, platform, burnin * 365)
        serialized_df = serialized_df.drop(columns=['x_Temporary_Larval_Habitat'], errors='ignore')
        scen_df_pickup = scen_df.merge(serialized_df, on=['scen_id'],
                                       how='inner')  ## FIXME when running expanded pickup from burnin
        builder = config_sweep_builder_pickup(exp, scen_df_pickup)
    else:
        builder = config_sweep_builder(exp, scen_df)

    #add_report_vector_stats(task, manifest, species_list=["gambiae"], stratify_by_species =True)
    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, 
                       num_year=sim_dur_years, detection_threshold=exp.detectionLimit)

    if emod_step != 'burnin':  # do not generate more granular reports for burnin
        if 'daily' in exp.analyzer_list:
            add_daily_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years,
                              detection_threshold=exp.detectionLimit) 
        add_monthly_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years,
                            detection_threshold=exp.detectionLimit)
        if '5day' in exp.analyzer_list or 'ccstep' in exp.analyzer_list:
            add_5daily_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years,
                               detection_threshold=exp.detectionLimit)

    # Create experiment from builder and run
    experiment = Experiment.from_builder(builder, task, name="")
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
    generate_run_EMOD_file(experiment, platform, suite_directory = exp.suite_directory)
    submit_analyze_EMOD(experiment, platform)
    print(f"Experiment submission {experiment.uid} succeeded.")
    exp.emod_id = experiment.id
    if exp.emod_step == 'burnin':
        exp.exp_name_pickup = exp.exp_name.replace(f'_burnin{exp.emod_burnin}', '')
        submit_run_pyscript(exp, pyscript='launch_sim.py', shname='launch_pickup.sh',
                            custom_args=f"--suite {exp.SUITEname} --expname {exp.exp_name_pickup} "
                                        f"--emodstep pickup --serializedid {exp.emod_id} "
                                        f"--models {' '.join([m for m in exp.models_pickup])} ",
                            job_id_EMOD='job_id_EMODanalyze',memG=exp.mem_increase_factor*5, job='pickup_launch')
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
    config = set_team_defaults(config, manifest)
    return config

def set_team_defaults(config, manifest):
    """
        Set configuration defaults using team-wide values, including drugs and vector species.
    """
    vector_config.set_team_defaults(config, manifest)
    config.parameters.Simulation_Type = "MALARIA_SIM"
    # removing Infectious_Period parameteres because not allowed in MALARIA_SIM, but need in VECTOR SIM
    config.parameters.pop("Infectious_Period_Constant")
    config.parameters.pop("Infectious_Period_Distribution")
    config.parameters.Malaria_Strain_Model = "FALCIPARUM_RANDOM_STRAIN"
    config.parameters.Enable_Disease_Mortality = 0

    # INFECTION
    config.parameters.Max_MSP1_Antibody_Growthrate = 0
    config.parameters.Min_Adapted_Response = 0
    config.parameters.Infection_Updates_Per_Timestep = 8
    config.parameters.Enable_Superinfection = 1
    config.parameters.Incubation_Period_Distribution = "CONSTANT_DISTRIBUTION"
    config.parameters.Incubation_Period_Constant = 7
    config.parameters.Antibody_IRBC_Kill_Rate = 1.596
    config.parameters.RBC_Destruction_Multiplier = 3.29
    config.parameters.Parasite_Switch_Type = "RATE_PER_PARASITE_7VARS"
    config.parameters.Antigen_Switch_Rate = math.pow(10, -9.116590124)
    config.parameters.Base_Gametocyte_Production_Rate = 0.06150582
    config.parameters.Base_Gametocyte_Mosquito_Survival_Rate = 0.002011099
    config.parameters.Falciparum_MSP_Variants = 32
    config.parameters.Falciparum_Nonspecific_Types = 76
    config.parameters.Falciparum_PfEMP1_Variants = 1070
    config.parameters.Gametocyte_Stage_Survival_Rate = 0.588569307
    config.parameters.MSP1_Merozoite_Kill_Fraction = 0.511735322
    config.parameters.Max_Individual_Infections = 3
    config.parameters.Nonspecific_Antigenicity_Factor = 0.415111634

    # IMMUNITY; these are NOT schema defaults
    config.parameters.Antibody_CSP_Killing_Threshold = 20
    config.parameters.Antigen_Switch_Rate = math.pow(10, -9.116590124)
    config.parameters.Base_Gametocyte_Production_Rate = 0.06150582
    config.parameters.Base_Gametocyte_Mosquito_Survival_Rate = 0.002011099
    config.parameters.Pyrogenic_Threshold = 1.5e4
    config.parameters.Falciparum_MSP_Variants = 32
    config.parameters.Falciparum_Nonspecific_Types = 76
    config.parameters.Falciparum_PfEMP1_Variants = 1070
    config.parameters.Fever_IRBC_Kill_Rate = 1.4
    config.parameters.Gametocyte_Stage_Survival_Rate = 0.588569307
    config.parameters.Max_MSP1_Antibody_Growthrate = 0.045
    config.parameters.MSP1_Merozoite_Kill_Fraction = 0.511735322
    config.parameters.Max_Individual_Infections = 3
    config.parameters.Nonspecific_Antigenicity_Factor = 0.415111634
    config.parameters.Antibody_Capacity_Growth_Rate = 0.09
    config.parameters.Antibody_Stimulation_C50 = 30
    config.parameters.Antibody_Memory_Level = 0.34
    config.parameters.Min_Adapted_Response = 0.05
    config.parameters.Cytokine_Gametocyte_Inactivation = 0.01667
    config.parameters.Enable_Maternal_Antibodies_Transmission = 1
    config.parameters.Maternal_Antibodies_Type = "SIMPLE_WANING"
    config.parameters.Maternal_Antibody_Protection = 0.1327

    # SYMPTOMATICITY
    config.parameters.Anemia_Mortality_Inverse_Width = 1
    config.parameters.Anemia_Mortality_Threshold = 0.654726662830038
    config.parameters.Anemia_Severe_Inverse_Width = 10
    config.parameters.Anemia_Severe_Threshold = 4.50775824973078
    config.parameters.Fever_Mortality_Inverse_Width = 1895.51971624351
    config.parameters.Fever_Mortality_Threshold = 3.4005008555391
    config.parameters.Fever_Severe_Inverse_Width = 27.5653580403806
    config.parameters.Fever_Severe_Threshold = 3.98354299722192
    config.parameters.Parasite_Mortality_Inverse_Width = 327.51594505874
    config.parameters.Parasite_Mortality_Threshold = 10 ** 5.93
    config.parameters.Parasite_Severe_Inverse_Width = 56.5754896048744
    config.parameters.Parasite_Severe_Threshold = 10 ** 5.929945527
    config.parameters.Clinical_Fever_Threshold_High = 1.5
    config.parameters.Clinical_Fever_Threshold_Low = 0.5
    config.parameters.Min_Days_Between_Clinical_Incidents = 14
    config.parameters.PfHRP2_Boost_Rate = 0.018  # original value: 0.07
    config.parameters.PfHRP2_Decay_Rate = 0.167  # original value: 0.172
    config.parameters.Report_Detection_Threshold_Blood_Smear_Gametocytes = 20
    config.parameters.Report_Detection_Threshold_Blood_Smear_Parasites = 20
    config.parameters.Report_Detection_Threshold_Fever = 1.0
    config.parameters.Report_Detection_Threshold_PCR_Gametocytes = 0.05
    config.parameters.Report_Detection_Threshold_PCR_Parasites = 0.05
    config.parameters.Report_Detection_Threshold_PfHRP2 = 5.0
    config.parameters.Report_Detection_Threshold_True_Parasite_Density = 0.0
    config.parameters.Report_Gametocyte_Smear_Sensitivity = 0.1
    config.parameters.Report_Parasite_Smear_Sensitivity = 0.1  # 10/uL
    config = set_team_drug_params(config, manifest)

    return config


def set_team_drug_params(config, manifest):
    with open(os.path.join(manifest.emod_input_path, 'malaria_drug_params.csv'), newline='') as csvfile:
        my_reader = csv.reader(csvfile)
        header = next(my_reader)
        drug_name_idx = header.index("Name")
        drug_pkpd_model_idx = header.index("PKPD_Model")
        drug_cmax_idx = header.index("Drug_Cmax")
        drug_decayt1_idx = header.index("Drug_Decay_T1")
        drug_decayt2_idx = header.index("Drug_Decay_T2")
        drug_vd_idx = header.index("Drug_Vd")
        drug_pkpdc50_idx = header.index("Drug_PKPD_C50")
        drug_ftdoses_idx = header.index("Drug_Fulltreatment_Doses")
        drug_dose_interval_idx = header.index("Drug_Dose_Interval")
        drug_gam02_idx = header.index("Drug_Gametocyte02_Killrate")
        drug_gam34_idx = header.index("Drug_Gametocyte34_Killrate")
        drug_gamM_idx = header.index("Drug_GametocyteM_Killrate")
        drug_hep_idx = header.index("Drug_Hepatocyte_Killrate")
        drug_maxirbc_idx = header.index("Max_Drug_IRBC_Kill")
        drug_bwexp_idx = header.index("Bodyweight_Exponent")
        drug_fracdos_key_idx = header.index("Upper_Age_In_Years")
        drug_fracdos_val_idx = header.index("Fraction_Of_Adult_Dose")
        for row in my_reader:
            mdp = dfs.schema_to_config_subnode(manifest.schema_file, ["idmTypes", "idmType:MalariaDrugTypeParameters"])
            mdp.parameters.Drug_Cmax = float(row[drug_cmax_idx])
            mdp.parameters.Drug_Decay_T1 = float(row[drug_decayt1_idx])
            mdp.parameters.Drug_Decay_T2 = float(row[drug_decayt2_idx])
            mdp.parameters.Drug_Vd = float(row[drug_vd_idx])
            mdp.parameters.Drug_PKPD_C50 = float(row[drug_pkpdc50_idx])
            mdp.parameters.Drug_Fulltreatment_Doses = float(row[drug_ftdoses_idx])
            mdp.parameters.Drug_Dose_Interval = float(row[drug_dose_interval_idx])
            mdp.parameters.Drug_Gametocyte02_Killrate = float(row[drug_gam02_idx])
            mdp.parameters.Drug_Gametocyte34_Killrate = float(row[drug_gam34_idx])
            mdp.parameters.Drug_GametocyteM_Killrate = float(row[drug_gamM_idx])
            mdp.parameters.Drug_Hepatocyte_Killrate = float(row[drug_hep_idx])
            mdp.parameters.Max_Drug_IRBC_Kill = float(row[drug_maxirbc_idx])
            mdp.parameters.PKPD_Model = row[drug_pkpd_model_idx]
            mdp.parameters.Name = row[drug_name_idx]
            mdp.parameters.Bodyweight_Exponent = float(row[drug_bwexp_idx])
            try:
                key = row[drug_fracdos_key_idx].strip('[]').replace(' ','')
                if len(key) > 0:
                    ages = [float(x) for x in row[drug_fracdos_key_idx].strip('[]').split(",")]
                    values = [float(x) for x in row[drug_fracdos_val_idx].strip('[]').split(",")]
            except Exception as ex:
                print("For drug {}, {}".format(row[0], str(ex)))
                ages = []
                values = []
            for idx in range(len(ages)):
                fdbua = dict()
                fdbua["Upper_Age_In_Years"] = ages[idx]
                fdbua["Fraction_Of_Adult_Dose"] = values[idx]
                mdp.parameters.Fractional_Dose_By_Upper_Age.append(fdbua)
            config.parameters.Malaria_Drug_Params.append(mdp.parameters)
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
                   partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.transmission_intensity_EMOD)),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
    elif exp.entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
                   CfgFn(habitat_setup, exp, row=row),
                   SwpFn(climate_setup,  seasonality = row.seasonality),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.transmission_intensity_EMOD),
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
            partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.transmission_intensity_EMOD)),
            partial(set_param, param='Run_Number', value=s)]
            for i, row in scen_df_pickup.iterrows()
            for s in range(nseeds)]
    elif exp.entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
                   CfgFn(habitat_setup, exp, row=row),
                   SwpFn(climate_setup,  seasonality = row.seasonality),
                   partial(set_param, param='Serialized_Population_Path',
                           value=os.path.join(row["serialized_file_path"], "output")),
                   partial(set_param, param='Serialized_Population_Filenames',
                           value=row["Serialized_Population_Filenames"]),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.transmission_intensity_EMOD),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df_pickup.iterrows()
                  for s in range(nseeds)]
    else:
        raise ValueError(f'{exp.entomology_mode} not valid')

    if exp.emod_calib_params: #This will allow us to vary EMOD parameters associated with  NU's within-host calibration efforts.
        from EMOD.functions.calib_params import get_emod_calib_params
        calib_params = get_emod_calib_params(exp,scen_df_pickup)
        for i in range(0, len(calib_params)):
            sweeps[i] = sweeps[i] + calib_params[i]
    builder.add_sweep_definition(sweep_functions, sweeps)
    return [builder]


def generate_run_EMOD_file(experiment, platform, suite_directory, t = '00:30:00', memG=5):
    """
    Generates a SBATCH file to re-run EMOD simulations, in case the user wants to re-run simulation
    This function creates a SLURM shell script for re-submitting EMOD simulations.
    
    Args:
        experiment (Experiment): The experiment object containing relevant parameters such as emod suite and emod experiment id.
        platform (Platform): The platform object representing the HPC system where the job will be submitted.
        suite_directory (str): The parent directory of job directory, so the sbatch can cd into the correct directory.
        t (str, optional): The time limit for the job in HH:MM:SS format. Defaults to '04:00:00'.
        memG (int, optional): The amount of memory (in GB) allocated for the job. Defaults to 20 GB.

    Returns:
        None
    """
    header_post = shell_header_quest(experiment.sh_hpc_config, t, memG, job_name='run_EMOD',
                                     mem_scl=experiment.mem_increase_factor)
    emodpy_venv = experiment.EMOD_venv
    pycommand = '\nbash batch.sh'
    suite = f"{experiment.parent.name}_{experiment.parent.id}"
    emod_directory = os.path.join(suite_directory, suite, experiment.id)
    script_path = os.path.join(experiment.job_directory, 'run_EMOD.sh')
    file = open(script_path, 'w')
    file.write(header_post + emodpy_venv+ f'\ncd {emod_directory}'+ pycommand)
    file.close()


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