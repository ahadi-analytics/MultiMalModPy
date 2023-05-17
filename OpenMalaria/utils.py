from helper import *


# return a list of scenarios
def create_scenarios_OM(exp, scen_df):  ## to do, add back in different OpenMalaria models

    with open(os.path.join(exp.om_input_path, 'scaffolds', f"{exp.om_scaffold}.xml"), "r") as fp:
        xml = fp.read()

    ### Fixed parameters
    xml = xml.replace(f"@version@", f"{exp.om_version}")
    xml = xml.replace(f"@pop_size@", f"{exp.pop_size}")
    xml = xml.replace(f"@burnin_start_year@", f"{exp.burnin_start_year}")
    xml = xml.replace(f"@start_year@", f"{exp.start_year}")
    xml = xml.replace(f"@end_year@", f"{exp.end_year}")
    xml = xml.replace(f"@survey_step@", f"{exp.om_survey_step}")
    xml = xml.replace(f"@entomology_mode@", f"{exp.entomology_mode}")

    ### Scenario sweeps and runs
    for r, row in scen_df.iterrows():
        scenario = xml.replace('@seed@', str(row['seed']))
        scenario = scenario.replace('@eir@', str(row['eir']))
        scenario = scenario.replace('@access@', str(
            row['access']))  ## to do helper function to replace all, except seed and seasonality
        seasonality = getattr(exp, row['seasonality'])
        for i in range(1, 13):
            scenario = scenario.replace(f'@seasonality{i}@', str(seasonality[i - 1]))
        with open(f"{exp.job_directory}/xml/{row['index']}.xml", 'w') as fo:
            fo.write(f"{scenario}")

    shutil.copy(exp.om_path + "/densities.csv", f"{exp.job_directory}/")
    schema = f"scenario_{exp.om_version}.xsd"
    shutil.copy(os.path.join(exp.om_path, schema), exp.job_directory)


def submit_run_OpenMalaria(exp, scen_df):
    os.makedirs(os.path.relpath(f"{exp.job_directory}/log"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{exp.job_directory}/xml"), exist_ok=True)
    os.makedirs(os.path.relpath(f"{exp.job_directory}/txt"), exist_ok=True)

    create_scenarios_OM(exp, scen_df)
    # wdir = os.path.abspath(os.path.dirname(__file__))
    ## Write bash file to submit
    array = f'#SBATCH --array=1-{str(exp.nexps)}\n'
    header_post = shell_header_quest(job_name=f'run_openmalaria', t='01:00:00', arrayJob=array)
    module = '\n\nmodule purge all' \
             '\nmodule use /projects/b1139/OpenMalaria/modules/\n' \
             '\nmodule load openmalaria\n'
    path = f'export PATH=$PATH: {exp.job_directory}'
    slurmID = '${SLURM_ARRAY_TASK_ID}'
    command = f'\nopenMalaria -s xml/{slurmID}.xml  --output txt/{slurmID}.txt'
    script_path = os.path.join(exp.job_directory, f'run_sim_OpenMalaria.sh')

    file = open(script_path, 'w')
    file.write(header_post + module + path + command)
    file.close()

    p = subprocess.run(['sbatch', '--parsable', 'run_sim.sh'], stdout=subprocess.PIPE,
                       cwd=str(exp.job_directory))
    slurm_job_id = p.stdout.decode('utf-8').strip().split(';')[0]

    print(f'Submitted simulations - job id: {slurm_job_id}')
    file = open(os.path.join(exp.job_directory, f'job_id.txt'), 'w')
    file.write(slurm_job_id)
    file.close()
    submit_analyze_OpenMalaria(exp)


