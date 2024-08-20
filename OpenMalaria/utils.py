from helper import *
import shutil
from OpenMalaria.scaffolds.intervention_snippets import *

def create_scenarios_OM(exp, scen_df):
    """
    Creates OpenMalaria scenarios based on a dataframe containing scenario parameters.
    Args:
        exp: The experiment object containing the experiment configuration.
        scen_df: The dataframe containing scenario parameters.
    Returns:
        None
    """
    with open(os.path.join(exp.om_input_path, 'scaffolds', f"{exp.om_scaffold}.xml"), "r") as fp:
        xml = fp.read()

    # Replace placeholders in the XML template with fixed parameters
    xml = xml.replace("@version@", f"{exp.om_version}")
    xml = xml.replace("@pop_size@", f"{exp.pop_size}")
    xml = xml.replace("@burnin_start_year@", f"{exp.sim_start_year_om}")
    xml = xml.replace("@start_year@", f"{exp.start_year-1}")
    xml = xml.replace("@end_year@", f"{exp.end_year-1}")
    xml = xml.replace("@survey_step@", f"{exp.om_survey_step}")
    xml = xml.replace("@entomology_mode@", f"{exp.entomology_mode}")
    xml = xml.replace("@detectionLimit@", f"{exp.detectionLimit}")
    xml = xml.replace('@importation_rate@', f"{exp.importation_rate}")

    # Scenario sweeps and runs
    df = rep_scen_df(scen_df)
    for r, row in df.iterrows():
        scenario = xml.replace('@seed@', str(row['seed']))
        scenario = scenario.replace('@cm_clinical@', str(row['cm_clinical']))
        scenario = scenario.replace('@cm_severe@', str(row['cm_severe']))
        scenario = scenario.replace('@eir@', str(row['model_input_om']))
        if 'cc_step' in exp.intervention_list: # GOING TO HAVE TO CHANGE SIGNIFICANTLY DUE TO INTERPOLATION
            scenario = scenario.replace('@EIR_reduction@', str(row['cc_factor_om']))
            scenario = scenario.replace('@step_change_time@', str(row['cc_timestep_om']))

        if 'smc' in exp.intervention_list:
            scenario = write_smc_deployment(scenario, row)

        seasonality = getattr(exp, row['seasonality'])

        # Replace seasonality placeholders with corresponding values from the experiment object
        for i in range(1, 13):
            scenario = scenario.replace(f'@seasonality{i}@', str(seasonality[i - 1]))

        # Write the scenario XML file
        with open(f"{exp.job_directory}/xml/{row['index']}.xml", 'w') as fo:
            fo.write(f"{scenario}")

    # Copy additional files required by OpenMalaria
    shutil.copy(exp.om_path + "/densities.csv", f"{exp.job_directory}/")
    schema = f"scenario_{exp.om_version}.xsd"
    shutil.copy(os.path.join(exp.om_path, schema), exp.job_directory)

def submit_analyze_OpenMalaria(exp, t='04:00:00', memG=4):
    """
    Submits a job to analyze OpenMalaria simulation results.
    Args:
        exp (object): The experiment object containing job directory information.
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
    file.write(header_post + exp.EMOD_venv + pycommand) # Also load EMOD's Python virtual environment - needed for handling exp object from idmtools
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
    Submits OpenMalaria simulations to a high-performance computing cluster.

    Args:
        exp (Experiment): An object containing experiment parameters and configuration.
        scen_df (pandas.DataFrame): A DataFrame containing scenario information.
        t (str, optional): Wall time for the job in the format 'HH:MM:SS'. Defaults to '01:00:00'.
        memG (int, optional): Memory required for the job in GB. Defaults to 8.

    Returns:
        None
    """

    # Create necessary directories for logs, XML files, and output text files
    os.makedirs(os.path.relpath(f"{exp.job_directory}/log"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{exp.job_directory}/xml"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{exp.job_directory}/txt"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{exp.job_directory}/ctsout"), exist_ok=True)

    # Generate OpenMalaria scenario XML files
    create_scenarios_OM(exp, scen_df)

    # Set up script for submitting OpenMalaria simulations as a SLURM array job
    array = f'#SBATCH --array=1-{str(exp.nexps)}%{str(exp.max_running_jobs)}\n'
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='run_openmalaria', arrayJob=array)
    openmalaria = exp.OM_venv
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
    create_scenarios_OM(exp, scen_df)
