from utility.helper import *


def submit_analyze_outputs(exp, t='01:00:00', memG=4):
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
    array = f'#SBATCH --array=1-{str(exp.nexps)}%{str(exp.max_running_jobs)}\n'
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='run_malariasimulation', arrayJob=array)
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
    r_file_path = os.path.join(ROOT_DIR, exp.malariasimulation_script)
    r_folder_path = os.path.join(ROOT_DIR, 'R_functions/')
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
