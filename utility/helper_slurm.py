import argparse
import os
import subprocess
import itertools
import pickle
from datetime import datetime
from datetime import datetime as dt
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d


# from idmtools.entities.experiment import Experiment


def exec(command):
    """
    Executes the specified command in a subprocess.

    Args:
        command (str): The command to execute.

    Returns:
        subprocess.Popen: A Popen object representing the subprocess.

    Raises:
        ValueError: If the command is empty or None.

    Notes:
        - This function runs the command in a new shell and captures both standard output
          and standard error.
        - The output can be accessed through the Popen object returned by this function.
    """

    return subprocess.Popen(
        command,
        shell=True,
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        universal_newlines=True,
        text=True,
    )


def shell_header_quest(
    sh_account, time_str="03:59:00", memG=3, job_name="myjob", arrayJob=None, mem_scl=1
):
    """
    Generates the SLURM shell script header for submitting jobs to a high-performance computing cluster.

    Args:
        sh_account (dict): Dictionary containing account information for SLURM, including the
            account name ('A'), partition ('p'), and whether it is a buy-in account ('buyin').
        time_str (str, optional): Time limit for the job in the format 'HH:MM:SS'.
            Defaults to '6:00:00'.
        memG (int, optional): Memory required for the job in gigabytes. Defaults to 3.
        job_name (str, optional): Name of the job. Defaults to 'myjob'.
        arrayJob (str, optional): Specification for array jobs. If provided, the script will
            include array job parameters. Defaults to None.
        mem_scl (float, optional): Memory scaling factor. Defaults to 1.

    Returns:
        str: The SLURM shell script header, which includes job submission parameters
            formatted for the SLURM workload manager.

    Raises:
        OSError: If unable to create the 'log' directory.

    Notes:
        - The function checks if the 'log' directory exists and creates it if it does not.
        - The partition is selected based on the job time limit if the account is not a buy-in account.
        - The generated header includes job error and output log file paths based on whether
          the job is an array job or a single job.
    """

    # Create 'log' subfolder if it doesn't exist
    if not os.path.exists("log"):
        os.makedirs(os.path.join("log"))

    # If not running on buyin account, need to select partition based on time required
    if not sh_account["buyin"]:
        t = datetime.strptime(time_str, "%H:%M:%S").time().hour
        if t < 4:
            sh_account["p"] = "short"
        if t >= 4:
            sh_account["p"] = "normal"
        if t >= 12:
            sh_account["p"] = "long"

    header = (
        f"#!/bin/bash\n"
        f'#SBATCH -A {sh_account["A"]}\n'
        f'#SBATCH -p {sh_account["p"]}\n'
        f"#SBATCH -t {time_str}\n"
        f"#SBATCH -N 1\n"
        f"#SBATCH --ntasks-per-node=1\n"
        f"#SBATCH --mem-per-cpu={int(memG * mem_scl)}G\n"
        f'#SBATCH --job-name="{job_name}"\n'
    )
    if arrayJob is not None:
        array = arrayJob
        err = f"#SBATCH --error=log/{job_name}_%A_%a.err\n"
        out = f"#SBATCH --output=log/{job_name}_%A_%a.out\n"
        header = header + array + err + out
    else:
        err = f"#SBATCH --error=log/{job_name}.%j.err\n"
        out = f"#SBATCH --output=log/{job_name}.%j.out\n"
        header = header + err + out
    return header


def submit_run_pyscript(
    exp,
    pyscript="plotter/plot_relationship.py",
    shname="run_relationship_plots.sh",
    custom_args="--models EMOD malariasimulation OpenMalaria",
    t="05:00:00",
    memG=20,
    job_id_EMOD=False,
    job_id_malariasimulation=False,
    job_id_OpenMalaria=False,
    job="pyjob",
    wdir=None,
    write_only=False,
):
    """
    Submits a job to run a specified Python script using SLURM.

    Args:
        exp (Experiment): The experiment object containing job directory and other related information.
        pyscript (str, optional): The name of the Python script to run. Defaults to 'plotter/plot_relationship.py'.
        shname (str, optional): The name of the shell script to submit. Defaults to 'run_relationship_plots.sh'.
        custom_args (str, optional): Custom arguments to pass to the Python script.
            Defaults to '--models EMOD malariasimulation OpenMalaria'.
        t (str, optional): Wall time for the job in the format 'HH:MM:SS'. Defaults to '05:00:00'.
        memG (int, optional): Memory required for the job in GB. Defaults to 20.
        job_id_EMOD (bool, optional): If True, sets the job ID as a dependency for EMOD. Defaults to False.
        job_id_malariasimulation (bool, optional): If True, sets the job ID as a dependency for malariasimulation. Defaults to False.
        job_id_OpenMalaria (bool, optional): If True, sets the job ID as a dependency for OpenMalaria. Defaults to False.
        job (str, optional): Name of the job. Defaults to 'pyjob'.
        wdir (str, optional): Location of the working directory. If None, uses the current directory.
        write_only (bool, optional): If True, does not submit the job but only writes the script. Defaults to False.

    Returns:
        None

    Raises:
        FileNotFoundError: If the specified job directory or dependencies do not exist.

    Notes:
        - The function generates a shell script that includes the SLURM header and the command
          to run the specified Python script.
        - It handles job dependencies based on the provided job IDs for EMOD, malariasimulation,
          and OpenMalaria.
        - The script is written to the job directory and submitted to the SLURM workload manager.
        - The submitted job ID is printed to the console for tracking purposes.
    """

    # Get the current working directory
    if wdir is None:
        wdir = os.path.abspath(os.path.dirname(__file__))
        wdir = os.path.abspath(os.path.join(wdir, os.pardir))

    # Generate the SLURM shell script header for the job
    header_post = shell_header_quest(
        exp.sh_hpc_config, t, memG, job_name=job, mem_scl=1
    )

    # Generate the Python command to run the script
    if exp.use_container:
        pycommand = f"\n{exp.EMOD_venv} && python {pyscript} -d {exp.output_directory} {custom_args}"
        pycommand = (
            f"module load singularity "
            f'\nsingularity exec --bind {exp.bind_path} --pwd {exp.ROOT_DIR}  {exp.image_path} bash -c "{pycommand}"'
        )
    else:
        pycommand = f"\npython {pyscript} -d {exp.output_directory} {custom_args}"
        pycommand = exp.EMOD_venv + f"\ncd {wdir}" + pycommand

    # Write the shell script to a file
    script_path = os.path.join(exp.job_directory, shname)
    file = open(script_path, "w")
    file.write(header_post + pycommand)
    file.close()
    dependencies = "--dependency=afterany:"
    prior_dependency = False
    # Check if job_id is provided as a string to define dependendies
    if not write_only:
        if job_id_EMOD:
            id_EMOD = (
                open(os.path.join(exp.job_directory, "job_id_EMODanalyze.txt"))
                .read()
                .strip()
            )
            dependencies = dependencies + f"{id_EMOD}"
            prior_dependency = True
        # Check if job_id_malariasimulation is provided as a string
        if job_id_malariasimulation:
            id_malariasimulation = (
                open(
                    os.path.join(
                        exp.job_directory, "job_id_malariasimulation_analyze.txt"
                    )
                )
                .read()
                .strip()
            )
            if prior_dependency:
                dependencies = dependencies + f",{id_malariasimulation}"
            else:
                dependencies = dependencies + f"{id_malariasimulation}"
                prior_dependency = True
        if job_id_OpenMalaria:
            id_OpenMalaria = (
                open(os.path.join(exp.job_directory, "job_id_OManalyze.txt"))
                .read()
                .strip()
            )
            if prior_dependency:
                dependencies = dependencies + f",{id_OpenMalaria}"
            else:
                dependencies = dependencies + f"{id_OpenMalaria}"
        # Submit job with dependency
        if not job_id_EMOD and not job_id_malariasimulation and not job_id_OpenMalaria:
            # Submit job without dependency
            p = subprocess.run(
                ["sbatch", "--parsable", script_path],
                stdout=subprocess.PIPE,
                cwd=str(exp.job_directory),
            )
        else:
            p = subprocess.run(
                ["sbatch", "--parsable", dependencies, script_path],
                stdout=subprocess.PIPE,
                cwd=str(exp.job_directory),
            )

        # Extract the SLURM job ID from the output
        slurm_job_id = p.stdout.decode("utf-8").strip().split(";")[0]

        # Print the submitted job ID
        print(f"Submitted {shname} to run {pyscript} - job id: {slurm_job_id}")


def submit_run_plotters_slurm(exp):
    """
    Submits and manages the creation of shell scripts to run standardized plots
    based on the models specified in the experiment.

    Args:
        exp (Experiment): The experiment object that contains attributes such as
            `models` and `plots_to_run`, which determine which models and
            plots should be processed.

    Returns:
        None

    Notes:
        - The function checks which models (EMOD, malariasimulation, OpenMalaria) are
          specified in `exp.models` and sets corresponding job IDs.
        - It prepares a submission script for a set of default plots (`relationship`,
          `timeseries`, `agecurves`) and also handles custom plots if specified in
          `exp.plots_to_run`.
        - Memory requirements for each plot are defined and passed to the submission
          script. The default is 20 GB, but this can be adjusted based on specific
          plot needs (e.g., `ccstep` requires 80 GB).
        - If `exp.plots_to_run` is set to `'all'`, all available plots will be processed.
    """

    job_id_EMOD = False
    job_id_malariasimulation = False
    job_id_OpenMalaria = False
    if "EMOD" in exp.models:
        job_id_EMOD = True
    if "malariasimulation" in exp.models:
        job_id_malariasimulation = True
    if "OpenMalaria" in exp.models:
        job_id_OpenMalaria = True

    plot_names_all = ["relationship", "timeseries", "agecurves"]
    ## ['ccstep', 'smc'] custom plotter excluded, as these only apply for specific simulation experiments
    # plot_memrequests_all = {'sampleplots' : 10,'relationship' :10,'agecurves' :10 ,'ccstep' :20}

    ## Write  shell submission script for all, even if not running
    fdir = os.path.abspath(os.path.dirname(__file__))
    parent_dir = os.path.abspath(os.path.join(fdir, os.pardir))
    for plot_name in plot_names_all:
        pyscript_name = f"-m plotter.plot_{plot_name}"

        plot_memG = 20  # current default in submit_run_pyscript
        submit_run_pyscript(
            exp,
            pyscript=pyscript_name,
            shname=f"run_{plot_name}_plots.sh",
            custom_args=f"--models {' '.join([x for x in exp.models])}",
            job=f"{plot_name}_plots",
            memG=plot_memG,
            wdir=parent_dir,
            write_only=True,
        )

    ## Write and run plots specified in exp.plots_to_run
    plots_to_run = [
        p for p in exp.plots_to_run if not p == "sampleplots"
    ]  # exp.plots_to_run
    if exp.plots_to_run[0] == "all":
        plots_to_run = plot_names_all

    ## Overwriting and submitting those to run
    for plot_name in plots_to_run:
        pyscript_name = f"-m plotter.plot_{plot_name}"

        plot_memG = 20  # current default in submit_run_pyscript
        if plot_name == "ccstep":
            plot_memG = 80  ## as specified in launch_ccstep.py, could reintroduce/use mem_scaling factor

        submit_run_pyscript(
            exp,
            pyscript=pyscript_name,
            shname=f"run_{plot_name}_plots.sh",
            custom_args=f"--models {' '.join([x for x in exp.models])}",
            job_id_EMOD=job_id_EMOD,
            job_id_malariasimulation=job_id_malariasimulation,
            job_id_OpenMalaria=job_id_OpenMalaria,
            job=f"{plot_name}_plots",
            memG=plot_memG,
            wdir=parent_dir,
        )


def write_txt(txtobj, path, fname):
    """
    Writes a text object to a specified file.

    Args:
        txtobj (str): The text object to write to the file.
        path (str): The path to the directory where the file will be saved.
        fname (str): The filename to use for the saved file.

    Raises:
        IOError: If there is an issue with writing to the file.

    Notes:
        - This function opens the specified file in write mode and writes the contents of
          `txtobj` to it. If the file already exists, it will be overwritten.
    """
    file = open(os.path.join(path, fname), "w")
    file.write(txtobj)
    file.close()
