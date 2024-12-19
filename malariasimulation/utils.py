from utility.helper import *

def submit_analyze_outputs(exp, t='01:00:00', memG=4):
    """
    Submits a job to analyze malaria simulation outputs using SLURM.

    This function generates a shell script to run the analysis and submits it to the SLURM workload manager
    with dependencies on a specified job.

    Args:
        exp (Experiment): An instance of the Experiment class containing job configuration and directories.
        t (str, optional): Time limit for the job in HH:MM:SS format. Defaults to '01:00:00'.
        memG (int, optional): Memory allocation in GB for the job. Defaults to 4.

    Returns:
        None: This function does not return any value. It only submits the job and prints the job ID.
    """

    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='analyze_malariasimulation',
                                     mem_scl=exp.mem_increase_factor)
    pycommand = f'\ncd /home/{exp.user}/model-characterization/malariasimulation' \
                f'\npython analyze_sim.py --job_dir "{exp.job_directory}"'
    script_path = os.path.join(exp.job_directory, 'run_analyzer_malariasimulation.sh')
    file = open(script_path, 'w')
    file.write(header_post + pycommand)
    file.close()

    malariasimulation_job_path = os.path.join(exp.job_directory, 'job_id_malariasimulation.txt')
    job_id = open(malariasimulation_job_path).read().strip()

    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))

    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted analyzer for malariasimulation  - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_malariasimulation_analyze.txt')


def submit_run_malariasimulation(exp, t='10:00:00', memG=3):
    """
    Submits a SLURM array job to run malaria simulations using an R script.

    This function generates a shell script to execute the malaria simulation for a specified number of experiments
    and submits it to the SLURM workload manager. It also triggers the submission of an analysis job after the
    simulations are submitted.

    Args:
        exp (Experiment): An instance of the Experiment class containing job configuration and directories.
        t (str, optional): Time limit for the job in HH:MM:SS format. Defaults to '10:00:00'.
        memG (int, optional): Memory allocation in GB for the job. Defaults to 3.

    Returns:
        None: This function does not return any value. It submits the job and prints the job ID.
    """

    array = f'#SBATCH --array=1-{str(exp.nexps)}%{str(exp.max_running_jobs)}\n'
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='run_malariasimulation', arrayJob=array)
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))

    r_file_path = os.path.join(ROOT_DIR, 'malariasimulation.R')
    r_folder_path = os.path.join(ROOT_DIR, 'functions/')
    script_path = os.path.join(exp.job_directory, 'run_malariasimulation.sh')

    malariasimulation_input_path = exp.malariasimulation_input_path
    slurmID = '${SLURM_ARRAY_TASK_ID}'
    os.makedirs(os.path.join(exp.job_directory, 'malariasimulation_jobs'), exist_ok=True)

    # Set up script for submitting malariasimulation simulations as a SLURM array job
    # The command structure for running an R Script as a subprocess is:
    #    1) the command (which sets up that the file type is a Rscript)
    #    2) the path to the Rscript 
    #    3) the inputs we want in our Rscript
    file = open(script_path, 'w')
    file.write(header_post + f'\ncd {malariasimulation_input_path}')
    file.write(f'\nRscript {r_file_path} {r_folder_path} {exp.job_directory} {slurmID}')
    file.close()

    # Now we can run the rscript as a subprocess via sbatch
    p = subprocess.run(['sbatch', script_path], check=True, stdout=subprocess.PIPE, cwd=str(exp.job_directory))
    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted simulations for malariasimulation  - job id: {slurm_job_id}')

    write_txt(slurm_job_id, exp.job_directory, 'job_id_malariasimulation.txt')
    submit_analyze_outputs(exp)
    return
