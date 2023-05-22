import argparse, math, os, sys, subprocess, shutil, re, itertools, pickle
from idmtools.entities.experiment import Experiment
import pandas as pd
import numpy as np
import warnings


def parse_args():
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        help="Job Directory where exp.obj is located",
    )
    return parser.parse_args()


def make_dirs(manifest, suite_name, exp_name):
    job_directory = os.path.join(manifest.projdir, 'experiments', suite_name,  exp_name) 
    sim_out_dir = os.path.join(manifest.projdir, 'simulation_outputs', suite_name, exp_name)
    os.makedirs(os.path.relpath(job_directory), exist_ok=True)
    os.makedirs(os.path.join(job_directory,'log'), exist_ok=True)
    os.makedirs(os.path.relpath(sim_out_dir), exist_ok=True)
    os.makedirs(os.path.join(sim_out_dir, 'em'), exist_ok=True)
    os.makedirs(os.path.join(sim_out_dir, 'om'), exist_ok=True)
    os.makedirs(os.path.join(sim_out_dir, 'comb'), exist_ok=True)
    return job_directory, sim_out_dir


def get_time_param(start_year, end_year, burnin, serialize):
    burnin_start_year = start_year - burnin
    monitoring_years = end_year - start_year
    
    if serialize:
      sim_dur_years = end_year-burnin_start_year
      sim_start_year = burnin_start_year
    else:
      sim_dur_years = end_year-start_year
      sim_start_year = start_year
      
    return sim_start_year, burnin_start_year , monitoring_years, sim_dur_years


def save_exp_scen(exp, scen_df, save_dirs):
  for sdir in save_dirs:
    scen_df.to_csv(os.path.join(sdir, 'scenarios.csv'),   index=False)
    pickle.dump(exp, open(os.path.join(sdir, "exp.obj"), "wb"))
  

def get_seasonal_eir():
  # Define functional form of non-perennial, seasonal setting
  # season_daily =  1 + np.sin(2 * np.pi * (np.arange(0, 365) / 365))  ## used in EMOD-OM benchmarking
  season_daily = 1 + np.sin(2 * np.pi * (np.arange(0, 365) / 365)) / 2 + np.cos(2 * np.pi * (np.arange(0, 365) / 365)) / 2
  season_month = [season_daily[1 + int(i * (365 / 12))] for i in range(0, 12)]
  seasonal =  season_month / np.max(season_month)
  #eir_sum = sum(season_month)
  #seasonal = [(x / eir_sum) for x in season_month] # rescale to sum =1
  perennial = [x / 12 for x in [1] * 12]
  
  return season_daily, season_month, seasonal, perennial
  
  
def create_scenarios_csv(exp, col_list=None):
    if col_list is None:
        col_list =[ 'eirs', 'access', 'seasonality']
    my_attrs = [getattr(exp, attr) for attr in col_list]
    df_array = np.array(list(itertools.product(*my_attrs)))
    df = pd.DataFrame(df_array)
    df.columns = col_list
    df.reset_index(inplace=True)
    return df


def as_list(x):
    return x if isinstance(x, list) else [x]


def generate_scenario_list(o_emod):
    annual_eir = as_list(o_emod['sim']['eir'])
    access = as_list(o_emod['sim']['access'])
    seasonality = as_list(o_emod['plot']['dict_season'])

    df_array = np.array(
        list(itertools.product(annual_eir, access, seasonality)))

    df = pd.DataFrame(df_array)
    df.columns = ['annual_eir', 'access', 'seasonality']
    df.reset_index(inplace=True)
    df = df.rename(columns={'index': 'scen_num'})
    return df

def exec(command):
    return subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                            universal_newlines=True, text=True)

###---------------------------------

def shell_header_quest(A='p30781', p='short', t='02:00:00', N=1, ntasks_per_node=1, memG=8, job_name='myjob',
                       arrayJob=None):
    """Requires a 'log' subfolder to write in .err and .out files, alternatively log/ needs to be removed"""
    if not os.path.exists('log'):
        os.makedirs(os.path.join('log'))

    header = f'#!/bin/bash\n' \
             f'#SBATCH -A {A}\n' \
             f'#SBATCH -p {p}\n' \
             f'#SBATCH -t {t}\n' \
             f'#SBATCH -N {N}\n' \
             f'#SBATCH --ntasks-per-node={ntasks_per_node}\n' \
             f'#SBATCH --mem={memG}G\n' \
             f'#SBATCH --job-name="{job_name}"\n'
    if arrayJob is not None:
        array = arrayJob
        err = '#SBATCH --error=log/slurm_%A_%a.err\n'
        out = '#SBATCH --output=log/slurm_%A_%a.out\n'
        header = header + array + err + out
    else:
        err = f'#SBATCH --error=log/{job_name}.%j.err\n'
        out = f'#SBATCH --output=log/{job_name}.%j.out\n'
        header = header + err + out
    return header


def write_txt(txtobj, path, fname):
    file = open(os.path.join(path, fname), 'w')
    file.write(txtobj)
    file.close()
    
    
def submit_analyze_OpenMalaria(exp):
    header_post = shell_header_quest(job_name=f'analyze_exp', t='01:00:00')
    pycommand = f'\ncd /home/mrm9534/model-characterization/' \
                f'\npython OpenMalaria/analyze_sim.py --dir "{exp.job_directory}"'

    script_path = os.path.join(exp.job_directory, f'run_analyzer_OpenMalaria.sh')
    file = open(script_path, 'w')
    file.write(header_post + pycommand)
    file.close()

    ## get job_id
    job_id_path = os.path.join(exp.job_directory, 'job_id.txt')
    job_id = open(job_id_path).read().strip()

    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))

    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]
    print(f'Submitted OpenMalaria analyzer - job id: {slurm_job_id}')
    write_txt(slurm_job_id, exp.job_directory, 'job_id_OManalyze.txt')

    
    
def submit_analyze_EMOD(experiment, platform):
    wdir = os.path.abspath(os.path.dirname(__file__))
    ## Write bash file to submit
    header_post = shell_header_quest(job_name=f'analyze_exp', t='01:00:00')
    emodpy_venv = emodpy_module(experiment.hpc)
    ### pycommand(s) - additional python or R scripts to directly run after analyzer can be added below
    pycommand = '\n'.join([ f'\npython {scr} -d {experiment.job_directory} -i {experiment.id}' for scr in experiment.analyzer])

    script_path = os.path.join(experiment.job_directory, f'run_analyzer_EMOD.sh') 
    file = open(script_path, 'w')
    file.write(header_post + emodpy_venv + f'\ncd {wdir}/EMOD' + pycommand)
    file.close()

    ## get job_id
    job_id = platform._op_client.get_job_id(experiment.id, experiment.item_type)
    p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                       cwd=str(experiment.job_directory))

    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]
    print(f'Submitted EMOD analyzer - job id: {slurm_job_id}')

    ### Write out slurn job-ids
    write_txt(job_id,experiment.job_directory, 'job_id_EMODsim.txt')
    write_txt(experiment.id,experiment.job_directory, 'exp_id_EMODsim.txt')
    write_txt(slurm_job_id,experiment.job_directory, 'job_id_EMODanalyze.txt')
    if experiment.emod_serialize:
      write_txt(job_id,experiment.job_directory, 'job_id_burnin.txt')


def submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh', job_id=None):
    wdir = os.path.abspath(os.path.dirname(__file__))
    ## Write bash file to submit
    header_post = shell_header_quest(job_name=f'pyjob', t='01:00:00')
    emodpy_venv = emodpy_module(exp.hpc)
    pycommand = f'\npython {pyscript} -d {exp.job_directory}'
    script_path = os.path.join(exp.job_directory, shname)
    
    file = open(script_path, 'w')
    file.write(header_post + emodpy_venv + f'\ncd {wdir}' + pycommand)
    file.close()
    
    if isinstance(job_id, str):
      job_id = open(os.path.join(exp.job_directory,F'{job_id}.txt')).read().strip()  
    if not isinstance(job_id, str):
      p = subprocess.run(['sbatch', '--parsable', f'--dependency=afterany:{job_id}', script_path], stdout=subprocess.PIPE,
                         cwd=str(exp.job_directory))
    else:
      p = subprocess.run(['sbatch', '--parsable', script_path], stdout=subprocess.PIPE, cwd=str(exp.job_directory))    
        
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0] 
    print(f'Submitted {shname} to run {pyscript} - job id: {slurm_job_id}') 
    
    
def emodpy_module(location='NUCLUSTER'):
    if location == 'NUCLUSTER':
        emod_venv = '\n\nmodule purge all' \
                    '\nsource activate /projects/b1139/environments/emodpy_alt\n'
    if location == 'SCICORE':
        emod_venv = '\n\nmodule purge all' \
                    '\nsource activate /projects/b1139/environments/emodpy_alt\n'
    return emod_venv


def OM_module(location='NUCLUSTER', om_version=45):
    if location =='NUCLUSTER':
        if om_version == 43:
            ommodule = '\n\nmodule use /projects/b1139/OpenMalaria/modules/ \nmodule load openmalaria\n'
        elif om_version == 45:
            ommodule = '\n\nmodule use /projects/b1139/OpenMalaria/om_v45/modules/ \nmodule load openmalaria\n'
        else:
            raise ValueError(f'{om_version} not a valid OpenMalaria version, available versions: 43, 45')
    if location =='SCICORE':   ## FIXME
        ommodule = '\n\nmodule use /projects/b1139/OpenMalaria/modules/ \nmodule load openmalaria\n'
    return ommodule


def combine_emodom_results(sim_out_dir):
  df_em =  pd.read_csv(os.path.join(sim_out_dir,'em', 'OM_benchmark.csv'))
  df_om =  pd.read_csv(os.path.join(sim_out_dir,'om', 'EMOD_benchmark.csv'))
  
  df_em['emodom']= 'EMOD'
  df_om['emodom']= 'OpenMalaria'
  df = df_em.append(df_om)
  df.to_csv((os.path.join(sim_out_dir,'comb',f'benchmark.csv')),  index=False)
  


def str_to_digit(x):
    try:
        x = float(x)
    except:
        x = x
    return x


def pretty_legend(fig, ltitle, r_adj=0.80, round_values=False):
    handles, labels = fig.gca().get_legend_handles_labels()
    if round_values:
        labels = [str_to_digit(x) for x in labels]
        labels = [round(x, 2) for x in labels]
    by_label = dict(zip(labels, handles))
    fig.legend(by_label.values(), by_label.keys(), loc=7, title=ltitle[:20])
    fig.tight_layout()
    return fig.subplots_adjust(right=r_adj)


