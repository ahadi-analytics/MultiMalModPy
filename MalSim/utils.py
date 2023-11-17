import os
import subprocess
from helper import *
import pandas as pd

user = os.getlogin()


def submit_analyze_MalSim(exp, t='01:00:00', memG=4):
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name='analyze_MSim', mem_scl = exp.mem_increase_factor)
    pycommand = f'\ncd /home/{user}/model-characterization/MalSim' \
                f'\npython analyze_sim.py --output_dir "{exp.sim_out_dir}"'
    script_path = os.path.join(exp.job_directory, 'run_analyzer_MalSim.sh')
    file = open(script_path, 'w')
    file.write(header_post + pycommand)
    file.close()

    malsim_job_path = os.path.join(exp.job_directory, 'job_id_MalSim.txt')
    job_id = open(malsim_job_path).read().strip()

    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE, cwd = str(exp.job_directory))

    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted MalSim Analyzer - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_MalSim_analyze.txt')



def create_malsim_scenarios(exp):
    os.makedirs(os.path.join(exp.job_directory, 'malsim_jobs'), exist_ok=True)
    scenarios = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))
    for i in range(0,len(scenarios)):
        scenarios.iloc[[i]].to_csv(os.path.join(exp.job_directory, 'malsim_jobs', f'{i+1}.csv'))
    return

def submit_run_MalSim(exp, t ='01:00:00', memG=8):
    array = f'#SBATCH --array=1-{str(exp.nexps)}\n'
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name=f'run_malsim', arrayJob=array)
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
    r_file_path = os.path.join(ROOT_DIR, exp.MalSim_script)
    r_folder_path = os.path.join(ROOT_DIR, 'R_functions/')
    script_path = os.path.join(exp.job_directory, 'run_MalSim.sh')
    ms_input_path = f'/home/{user}/model-characterization/MalSim'  # might need to switch to manifest defined ms_input_path if running elsewhere? 
    slurmID = '${SLURM_ARRAY_TASK_ID}'
    create_malsim_scenarios(exp)

    # Set up script for submitting MalSim simulations as a SLURM array job
    #The command structure for running an R Script as a subprocess is:
    #    1) the command (which sets up that the file type is a Rscript)
    #    2) the path to the Rscript 
    #    3) the inputs we want in our Rscript
    file = open(script_path, 'w')
    file.write(header_post + f'\ncd {ms_input_path}') 
    file.write(f'\nRscript {r_file_path} {r_folder_path} {exp.job_directory} malsim_jobs/{slurmID} {slurmID}')
    file.close()

    # Now we can run the rscript as a subprocess via sbatch
    p = subprocess.run(['sbatch',script_path], check=True, stdout=subprocess.PIPE,cwd=str(exp.job_directory))
    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted MalSim simulations - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_MalSim.txt')
    submit_analyze_MalSim(exp)
    return
