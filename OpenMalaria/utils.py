from utility.helper import *
import shutil

# from OpenMalaria.functions.interventions import * # Currently not supported
from OpenMalaria.functions.convert_access import convert_access_lookup



def create_scenarios(exp, scen_df):
    """
    Creates OpenMalaria simulation scenarios based on a dataframe containing scenario parameters.

    This function generates multiple OpenMalaria scenario XML files by replacing placeholders in a template
    XML with specific parameters from the experiment configuration and scenario dataframe. Each scenario is
    customized based on the parameters from the dataframe, and the resulting XML files are saved to the job directory.

    Args:
        exp (Experiment): The experiment object containing configuration parameters such as OpenMalaria version,
                           population size, simulation years, entomology mode, and other parameters required for
                           generating the scenarios.
        scen_df (pandas.DataFrame): A dataframe containing scenario parameters such as seed values, clinical malaria
                                     data, and other model-specific inputs.

    Returns:
        None

    """
    with open(os.path.join(exp.openmalaria_input_path, 'scaffolds', f"{exp.openmalaria_scaffold}.xml"), "r") as fp:
        xml = fp.read()

    exp.days_between_clinical_cases_5days = 5  # Aurelien communicated that as long as we use v46, we should have a days_between_clinical_cases of 25 days

    # Replace placeholders in the XML template with fixed parameters
    xml = xml.replace("@version@", f"{exp.openmalaria_version}")
    xml = xml.replace("@pop_size@", f"{exp.openmalaria_pop_size}")
    xml = xml.replace("@burnin_start_year@", f"{exp.sim_start_year_openmalaria}")
    xml = xml.replace("@start_year@", f"{exp.start_year - 1}")
    xml = xml.replace("@end_year@", f"{exp.end_year - 1}")
    xml = xml.replace("@survey_step@", f"{exp.openmalaria_survey_step}")
    xml = xml.replace("@entomology_mode@", f"{exp.entomology_mode}")
    xml = xml.replace("@detectionLimit@", f"{exp.detectionLimit}")
    xml = xml.replace('@importation_rate@', f"{exp.openmalaria_importation_rate}")
    xml = xml.replace('@healthSystemMemory@', f"{str(int(exp.days_between_clinical_cases_5days))}")
    xmlageGroups = '\t\t<ageGroup lowerbound="0">'
    for item in exp.agebins:
        xmlageGroups += f'\n\t\t\t<group upperbound="{item}"/>'
    xml = xml.replace('<@age_groups@>', xmlageGroups)

    # Scenario sweeps and runs
    df = rep_scen_df(scen_df)
    for r, row in df.iterrows():

        if row['cm_clinical'] == 0.45:
            cm_clinical_5daily = 0.209261
        elif row['cm_clinical'] == 0.15:
            cm_clinical_5daily = 0.05161556
        elif row['cm_clinical'] == 0:
            cm_clinical_5daily = 0
        else:
            cm_clinical_5daily = convert_access_lookup(row['cm_clinical']) #  converted from R function to python, returns an error if value outside of lookup range
            # cm_clinical_5daily = convert_access(row['cm_clinical']) # TODO convert from R function to python


        scenario = xml.replace('@seed@', str(row['seed']))
        scenario = scenario.replace('@cm_clinical@', str(cm_clinical_5daily))
        scenario = scenario.replace('@cm_severe@', str(row['cm_severe']))
        scenario = scenario.replace('@eir@', str(row['model_input_OpenMalaria']))

        if 'cc_step' in exp.intervention_list:
            scenario = scenario.replace('@EIR_reduction@', str(row['cc_factor_OpenMalaria']))
            scenario = scenario.replace('@step_change_time@', str(row['cc_timestep_OpenMalaria']))
        
        #SMC currently not supported
        #if 'smc' in exp.intervention_list:
        #    scenario = write_smc_deployment(scenario, row)

        seasonality = getattr(exp, row['seasonality'])

        # Replace seasonality placeholders with corresponding values from the experiment object
        for i in range(1, 13):
            scenario = scenario.replace(f'@seasonality{i}@', str(seasonality[i - 1]))

        # Write the scenario XML file
        with open(f"{exp.job_directory}/xml/{row['index']}.xml", 'w') as fo:
            fo.write(f"{scenario}")

    # Copy additional files required by OpenMalaria
    shutil.copy(exp.openmalaria_path + "/densities.csv", f"{exp.job_directory}/")
    schema = f"scenario_{exp.openmalaria_version}.xsd"
    shutil.copy(os.path.join(exp.openmalaria_path, schema), exp.job_directory)


def submit_analyze_OpenMalaria(exp, t='04:00:00', memG=4):
    """
    Submits a job to analyze OpenMalaria simulation results on an HPC cluster.

    This function generates a SLURM job submission script to analyze the results of an OpenMalaria simulation.
    The job runs a Python script (`analyze_sim.py`) in a specified environment to process the simulation results,
    and it submits the job with a dependency on a previously run job, ensuring the analysis starts after the
    prior job completes.

    Args:
        exp (Experiment): The experiment object containing configuration details such as the job directory,
                           HPC platform specification (e.g., NUCLUSTER, SCICORE), and virtual environment paths.
        t (str, optional): The time limit for the job submission in the format 'HH:MM:SS'. Default is '04:00:00'.
        memG (int, optional): The amount of memory (in GB) to allocate for the job. Default is 4 GB.

    Returns:
        None

    """
    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='analyze_OMsim',
                                     mem_scl=exp.mem_increase_factor)

    # Create the Python command to run the analyzer
    if exp.hpc == 'NUCLUSTER':
        pycommand = f'\ncd /home/{exp.user}/model-characterization/OpenMalaria' \
                    f'\npython analyze_sim.py --dir "{exp.job_directory}"'
    elif exp.hpc == 'SCICORE':
        pycommand = f'\ncd /scicore/home/scicore/cavelan/git/model-characterization/OpenMalaria' \
                    f'\n\nml Python/3.9.6-GCCcore-11.2.0-bare' \
                    f'\nsource /scicore/home/scicore/cavelan/git/model-characterization/emodenv/bin/activate' \
                    f'\npython analyze_sim.py --dir "{exp.job_directory}"'
    else:
        raise ValueError('HPC specification not available, must be NUCLUSTER or SCICORE')

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, 'run_analyzer_OpenMalaria.sh')
    file = open(script_path, 'w')
    file.write(
        header_post + exp.EMOD_venv + pycommand)  # Also load EMOD's Python virtual environment - needed for handling exp object from idmtools
    file.close()

    # Read the job ID from the 'job_id.txt' file
    job_id_path = os.path.join(exp.job_directory, 'job_id.txt')
    job_id = open(job_id_path).read().strip()

    # Submit the job with dependency on the previous job
    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))

    # Extract the SLURM job ID from the output
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]

    # Print the submitted job ID and save it to a file
    print(f'Submitted OpenMalaria analyzer - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_OManalyze.txt')


def submit_run_OpenMalaria(exp, scen_df, t='04:00:00', memG=3):
    """
    Submits OpenMalaria simulations to a high-performance computing (HPC) cluster using SLURM.

    This function generates SLURM job scripts to run OpenMalaria simulations on an HPC cluster. It creates necessary
    directories for storing logs, XML files, and output, generates simulation scenarios, and then submits the simulations
    as a SLURM array job. After the simulations are submitted, it also triggers a job to analyze the results.

    Args:
        exp (Experiment): An object containing experiment parameters and configuration, including paths,
                           simulation settings, and HPC-specific configurations.
        scen_df (pandas.DataFrame): A DataFrame containing scenario parameters such as seeds, clinical model parameters,
                                     and other model-specific inputs that will be used to generate simulation scenarios.
        t (str, optional): Wall time for the SLURM job in the format 'HH:MM:SS'. Default is '04:00:00'.
        memG (int, optional): The amount of memory (in GB) to allocate for the job. Default is 3 GB.

    Returns:
        None

    """

    # Create necessary directories for logs, XML files, and output text files
    os.makedirs(os.path.relpath(f"{exp.job_directory}/log"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{exp.job_directory}/xml"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{exp.job_directory}/txt"), exist_ok=True)
    # os.makedirs(os.path.relpath(f"{exp.job_directory}/ctsout"), exist_ok=True) # only required when running continuous output

    # Generate OpenMalaria scenario XML files
    create_scenarios(exp, scen_df)

    # Set up script for submitting OpenMalaria simulations as a SLURM array job
    array = f'#SBATCH --array=1-{str(exp.nexps)}%{str(exp.max_running_jobs)}\n'
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='run_openmalaria', arrayJob=array)
    openmalaria = exp.OPENMALARIA_venv
    path = f'export PATH=$PATH:{exp.job_directory}'
    slurmID = '${SLURM_ARRAY_TASK_ID}'
    command = f'\nopenMalaria -s xml/{slurmID}.xml  --output txt/{slurmID}.txt'
    script_path = os.path.join(exp.job_directory, 'run_sim_OpenMalaria.sh')

    # Write the bash script for submitting OpenMalaria simulations
    file = open(script_path, 'w')
    file.write(header_post + openmalaria + path + command)
    file.close()

    # Submit the OpenMalaria simulations as a SLURM job
    p = subprocess.run(['sbatch', '--parsable', 'run_sim_OpenMalaria.sh'], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))

    # Save the SLURM job ID to a file
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]
    print(f'Submitted OpenMalaria simulations - job id: {slurm_job_id}')
    file = open(os.path.join(exp.job_directory, 'job_id.txt'), 'w')
    file.write(slurm_job_id)
    file.close()

    # Submit the job for analysis
    submit_analyze_OpenMalaria(exp)


if __name__ == "__main__":
    wdir = ''
    file = open(os.path.join(wdir, "exp.obj"), "rb")
    exp = pickle.load(file)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))
    create_scenarios(exp, scen_df)
