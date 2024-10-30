import os
import sys
import json
import subprocess
from functools import partial
from EMOD.scaffolds.reporters import add_annual_reports, add_daily_reports, add_monthly_reports, add_5daily_reports
from EMOD.scaffolds.EMOD_functions import build_burnin_df, all_campaigns, set_param, ItvFn, CfgFn, sweep_functions, seasonality_setup
from EMOD.scaffolds.forcedEIR import mAb_vs_EIR

import emodpy_malaria.malaria_config as malaria_config
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.entities.experiment import Experiment
sys.path.append('../')
import manifest
from utility.helper_slurm import shell_header_quest, write_txt


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

    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years)

    if emod_step != 'burnin':  # do not generate monthly reports for burnin
        if 'daily' in exp.analyzer_list:
            add_daily_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years) #We shouldn't generate daily reports unless specified
        add_monthly_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years)
        if '5day' in exp.analyzer_list or 'cc_step' in exp.analyzer_list:  # Note, we will not want to always run 5 days using the analyzer_list as a flag to include this reporter  or not
            add_5daily_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year_emod, num_year=sim_dur_years)

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
    Parameters:
        config (object): The configuration object to be modified.
    Returns:
        object: The modified configuration object.
    """
    config = malaria_config.set_team_defaults(config, manifest)
    return config


def set_emod_exp_parameters(config, exp):
    config.parameters.x_Base_Population = exp.emod_pop_size / 1000
    config.parameters.Simulation_Duration = exp.sim_dur_years * 365
    config.parameters.Report_Detection_Threshold_Blood_Smear_Parasites = exp.detectionLimit
    config.parameters.Report_Detection_Threshold_Blood_Smear_Gametocytes = exp.detectionLimit
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
        config.parameters.Serialization_Time_Steps = [exp.burnin * 365]


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
                   CfgFn(seasonality_setup, exp, seasonality = row.seasonality),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.model_input_emod),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
    else:
        raise ValueError(f'{exp.entomology_mode} not valid')

    if exp.emod_calib_params: #This will allow us to vary EMOD parameters associated with NU's within-host calibration efforts.
        from EMOD.scaffolds.calib_params import get_emod_calib_params
        calib_params = get_emod_calib_params(exp,scen_df)
        for i in range(0, len(calib_params)):
            sweeps[i] = sweeps[i] + calib_params[i]
    builder.add_sweep_definition(sweep_functions, sweeps)
    return [builder]


def config_sweep_builder_pickup(exp, scen_df_pickup):
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
                   CfgFn(seasonality_setup, exp, seasonality = row.seasonality),
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
