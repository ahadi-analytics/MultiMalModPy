import os
from utility.helper import *
import shutil

# from OpenMalaria.functions.interventions import * # Currently not supported
from OpenMalaria.functions.convert_access import convert_access_lookup
from OpenMalaria.functions.interventions import *



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

    exp.days_between_clinical_cases_5days = 6

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

    # Load from snippets
    # Age Groups to monitor
    xmlageGroups = '\t\t<ageGroup lowerbound="0">'
    for item in exp.agebins:
        xmlageGroups += f'\n\t\t\t<group upperbound="{item}"/>'
    xml = xml.replace('<@age_groups@>', xmlageGroups)

    # Age demography
    snippet_file = 'age_demography.txt'
    with open(os.path.join(exp.openmalaria_input_path, 'snippets', snippet_file), 'r', encoding='utf-8') as file:
        snippet = file.read()
    xml = xml.replace('@age_demography@', snippet)

    # Interventions
    if "ccstep" in exp.intervention_list:
        xml = carrying_capacity(exp, xml)
    else:
        xml = xml.replace('@intervention_ccstep@', '')

    # Model options
    snippet_file = exp.openmalaria_modeloptions
    with open(os.path.join(exp.openmalaria_input_path, 'snippets', snippet_file), 'r', encoding='utf-8') as file:
        snippet = file.read()
    xml = xml.replace('@model_options@', snippet)

    # Model core parameters
    snippet_file = exp.openmalaria_parameter
    with open(os.path.join(exp.openmalaria_input_path, 'snippets', snippet_file), 'r', encoding='utf-8') as file:
        snippet = file.read()
    xml = xml.replace('@model_parameters@', snippet)

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
        scenario = scenario.replace('@eir@', str(row['transmission_intensity_OpenMalaria']))

        if 'ccstep' in exp.intervention_list:
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
        if '@' not in scenario:
            # Write the scenario XML file
            with open(f"{exp.job_directory}/xml/{row['index']}.xml", 'w') as fo:
                fo.write(f"{scenario}")
        else:
            raise ValueError(f"Error: The '@' symbol is present in the scenario XML {row['index']}.")

    # Copy additional files required by OpenMalaria
    shutil.copy(exp.openmalaria_path + "/densities.csv", f"{exp.job_directory}/")
    schema = f"scenario_{exp.openmalaria_version}.xsd"
    shutil.copy(os.path.join(exp.openmalaria_path, schema), exp.job_directory)


def submit_analyze_OpenMalaria(exp, t='03:59:00', memG=10):
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
    header_post = shell_header_quest(exp.sh_hpc_config, time_str = t, memG=memG, job_name='analyze_OpenMalaria',
                                     mem_scl=exp.mem_increase_factor)

    pycommand = f'\ncd {exp.root_directory}/OpenMalaria' \
                f'\n{exp.EMOD_venv}' \
                f'\npython analyze_sim.py --dir "{exp.job_directory}"'

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, 'run_analyzer_OpenMalaria.sh')
    file = open(script_path, 'w')
    file.write(header_post + pycommand)
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


def submit_run_OpenMalaria(exp, scen_df):
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

    if exp.hpc == 'LOCAL':
        if not exp.use_container:
            from utility.helper_local import write_ps1_analyzer, submit_runmodel_local
            write_ps1_OpenMalaria(exp)
            write_ps1_analyzer(exp, pyscript=exp.analyzer_script[0], model='OpenMalaria')
            submit_runmodel_local(exp, model='OpenMalaria')
        else:
            from utility.helper_local_docker import write_sh_analyzer, submit_runmodel_sh
            # Write local submission script
            write_sh_OpenMalaria(exp)
            write_sh_analyzer(exp, pyscript=exp.analyzer_script[0], model='OpenMalaria')
            submit_runmodel_sh(exp, model='OpenMalaria')
    else:
        submit_run_OpenMalaria_slurm(exp)


def submit_run_OpenMalaria_slurm(exp):
    """
    Submits OpenMalaria simulations as a SLURM array job for parallel execution.

    This function generates a SLURM script for running OpenMalaria simulations, configures job parameters like
    time, memory, and job array size, and then submits the job to a SLURM job scheduler. The job is submitted
    with the specified wall time and memory requirements, and it runs the OpenMalaria simulations for each task
    in the array.

    Args:
        exp (object): An experiment object containing attributes like 'nexps', 'max_running_jobs',
                      'sh_hpc_config', 'job_directory', and 'OPENMALARIA_venv' needed for job configuration and submission.

    Raises:
        subprocess.CalledProcessError: If there is an issue with running the SLURM job submission command.
    """
    array = f'#SBATCH --array=1-{str(exp.nexps)}%{str(exp.max_running_jobs)}\n'
    header_post = shell_header_quest(exp.sh_hpc_config, exp.openmalaria_time_per_sim, exp.openmalaria_memory_per_sim, job_name='run_openmalaria', arrayJob=array)
    openmalaria = exp.OPENMALARIA_venv
    path = f'export PATH=$PATH:{exp.job_directory}'
    slurmID = '${SLURM_ARRAY_TASK_ID}'
    command = f'\nopenMalaria -s xml/{slurmID}.xml  --output txt/{slurmID}.txt'
    script_path = os.path.join(exp.job_directory, 'run_OpenMalaria.sh')

    # Write the bash script for submitting OpenMalaria simulations
    file = open(script_path, 'w')
    file.write(header_post + openmalaria + path + command)
    file.close()

    # Submit the OpenMalaria simulations as a SLURM job
    p = subprocess.run(['sbatch', '--parsable', 'run_OpenMalaria.sh'], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))

    # Save the SLURM job ID to a file
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]
    print(f'Submitted OpenMalaria simulations - job id: {slurm_job_id}')
    file = open(os.path.join(exp.job_directory, 'job_id.txt'), 'w')
    file.write(slurm_job_id)
    file.close()

    # Submit the job for analysis
    submit_analyze_OpenMalaria(exp)


def write_ps1_OpenMalaria(exp):
    """
    Creates a PowerShell script to run OpenMalaria simulations (sequentially) locally.

    This function generates a PowerShell script that:
    1. Sets job parameters, including the path to the OpenMalaria executable and the job directory.
    2. Ensures the log directory exists, creating it if necessary.
    3. Iterates over all experiments, running the OpenMalaria simulation for each one.
    4. Logs the output and errors to respective log files.

    Args:
        exp (object): An experiment object containing attributes such as 'job_directory', 'nexps', and paths
                      necessary for setting up and running the simulation.

    Raises:
        IOError: If there is an issue with writing the PowerShell script to the file.
    """
    # Define file path for PowerShell script
    file_path = os.path.join(exp.job_directory, 'run_openmalaria.ps1')

    # Get the absolute path of the working directory
    wdir = os.path.abspath(os.path.dirname(__file__))
    wdir = os.path.abspath(os.path.join(wdir, os.pardir))

    # Construct the content of the PowerShell script
    ps_content = f"""
# Job settings
$job_name = "run_openmalaria"
$exe_path = "{exp.OPENMALARIA_PATH}"
$jobdir = "{exp.job_directory}"
$log_dir = Join-Path $jobdir "log"

# Create log directory if it doesn't exist
if (-not (Test-Path -Path $log_dir)) {{
    New-Item -ItemType Directory -Force -Path $log_dir
}}

# Navigate to the working directory
Set-Location -Path $jobdir

# Run the OpenMalaria simulation for each experiment, with progress bar
$total = {exp.nexps}
$startTime = Get-Date
for ($i = 1; $i -le {exp.nexps}; $i++) {{
    $elapsed = (Get-Date) - $startTime
    $percent = ($i / $total) * 100
    $status = "Simulation $i of $total | Elapsed: {{0:hh\\:mm\\:ss}}" -f $elapsed
    Write-Progress -Activity "Running OpenMalaria" -Status $status -PercentComplete $percent
    # Run the openMalaria command
    & "$exe_path/openMalaria.exe" -s "xml/$i.xml" --output "txt/$i.txt" `
    >> "$log_dir/run_openmalaria.log" 2>> "$log_dir/run_openmalaria.err"
}}

Write-Progress -Activity "Running OpenMalaria" -Completed
$elapsedTotal = (Get-Date) - $startTime
Write-Host "All $total simulations complete in $($elapsedTotal.ToString())."
"""

    # Write the PowerShell content to a .ps1 file
    with open(file_path, 'w') as file:
        file.write(ps_content)
    print(f"PowerShell script written successfully at {file_path}")


def write_sh_OpenMalaria(exp):
    """
    Creates a shell script to run OpenMalaria simulations (sequentially) locally.

    This function generates a shell script that:
    1. Sets job parameters, including the path to the OpenMalaria executable and the job directory.
    2. Ensures the log directory exists, creating it if necessary.
    3. Iterates over all experiments, running the OpenMalaria simulation for each one.
    4. Logs the output and errors to respective log files.

    Args:
        exp (object): An experiment object containing attributes such as 'job_directory', 'nexps', and paths
                      necessary for setting up and running the simulation.

    Raises:
        IOError: If there is an issue with writing the shell script to the file.
    """
    # Define file path for shell script
    file_path = os.path.join(exp.job_directory, 'run_OpenMalaria.sh')

    # Get the absolute path of the working directory
    wdir = os.path.abspath(os.path.dirname(__file__))
    wdir = os.path.abspath(os.path.join(wdir, os.pardir))

    # Construct the content of the shell script
    sh_content = f"""#!/bin/bash

# Job settings
job_name="run_openmalaria"
exe_path="{exp.OPENMALARIA_venv}"
jobdir="{exp.job_directory}"
log_dir="$jobdir/log"

# Create log directory if it doesn't exist
if [ ! -d "$log_dir" ]; then
    mkdir -p "$log_dir"
fi

# Navigate to the job directory
cd "$jobdir" || exit 1

# Run the OpenMalaria simulation for each experiment
for ((i = 1; i <= {exp.nexps}; i++)); do
    # Run the OpenMalaria command and log output and errors
    "{exp.OPENMALARIA_venv}/openMalaria" -s "$jobdir/xml/$i.xml" --output "txt/$i.txt" >> "$log_dir/run_openmalaria.log" 2>> "$log_dir/run_openmalaria.err" || true
done

echo "OpenMalaria simulation complete."
"""

    # Write the shell content to a .sh file
    with open(file_path, 'w') as file:
        file.write(sh_content)

    print(f"Shell script written successfully at {file_path}")

if __name__ == "__main__":
    wdir = ''
    file = open(os.path.join(wdir, "exp.obj"), "rb")
    exp = pickle.load(file)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))
    create_scenarios(exp, scen_df)
