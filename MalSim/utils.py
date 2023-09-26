import os
import subprocess
from idmtools.entities.experiment import Experiment
from helper import *

user = os.getlogin()


def submit_analyze_MalSim(exp, t='01:00:00', memG=4):
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name=f'analyze_MSim', mem_scl = exp.mem_increase_factor)
    pycommand = f'\ncd /home/{user}/model-characterization/MalSim' \
                f'\npython analyze_sim.py --output_dir "{exp.sim_out_dir}"'
    script_path = os.path.join(exp.job_directory, f'run_analyzer_MalSim.sh')
    file = open(script_path, 'w')
    file.write(header_post + pycommand)
    file.close()
    
    malsim_job_path = os.path.join(exp.job_directory, 'job_id_MalSim.txt')
    job_id = open(malsim_job_path).read().strip()
    
    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE, cwd = str(exp.job_directory))
    
    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted MalSim Analyzer - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_MalSim_analyze.txt')
    
    
    

def submit_run_MalSim(exp, t ='01:00:00', memG=8):
    
    # Set up script for submitting MalSim simulations as a SLURM array job
    header_post = shell_header_quest(exp.sh_hpc_config, t, memG, job_name=f'run_MalSim', arrayJob=None)
    
    #The command structure for running an R Script as a subprocess is:
    #    1) the command (which sets up that the file type is an Rscript)
    #    2) the path to the Rscript 
    #    3) the inputs we want in our Rscript
    ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
    r_script = 'malsim_benchmarking_exercise.R'   
    r_file_path = os.path.join(ROOT_DIR, r_script)
    r_folder_path = os.path.join(ROOT_DIR, 'R_functions/')
    scen_directory = os.path.join(exp.job_directory, 'scenarios_wseeds.csv')
    #scen_directory = os.path.join(exp.job_directory, 'scenarios.csv')
    num_years = str(exp.MalSim_duration)
    script_path = os.path.join(exp.job_directory, f'run_MalSim.sh')
    file = open(script_path, 'w')
    file.write(header_post + f'\ncd /home/{user}/model-characterization/MalSim \nRscript {r_file_path} {r_folder_path} {scen_directory} {num_years} {exp.sim_out_dir}/MalSim')
    file.close()

    # Now we can run the rscript as a subprocess in an sbatch
    p = subprocess.run(['sbatch',script_path], check=True, stdout=subprocess.PIPE,cwd=str(exp.job_directory))
    slurm_job_id = p.stdout.decode('utf-8').strip().split(' ')[-1]
    print(f'Submitted MalSim simulations - job id: {slurm_job_id}')
    
    write_txt(slurm_job_id, exp.job_directory, 'job_id_MalSim.txt')
    
    submit_analyze_MalSim(exp)
    return
    