# Characterization and comparison of three main malaria models: EMOD, OpenMalaria, and malariasimulation
_[EMOD](https://docs.idmod.org/projects/emod-malaria/en/latest/index.html) | [OpenMalaria](https://github.com/SwissTPH/openmalaria/) | [malariasimulation](https://github.com/mrc-ide/malariasimulation/tree/master)_  

_Disclaimer: This repository is under active development, if something is not working, please contact us - or simply create an issue on GitHub that we can follow up on._

------------------------------------- 

#### Table of contents

1. [Goal](#goal)
2. [Setup](#setup)
    - [Repository structure](#repository-structure)
    - [Programming language](#programming-language)
    - [Simulation framework](#simulation-framework)
    - [Model inputs and scaffolds](#model-inputs-and-scaffolds)
    - [EMOD serialization](#emod-serialization)
3. [Scenarios implemented](#Scenarios-implemented)
    - [base case](#base-case)
4. [Running simulations](#running-simulations)
   - [Manifest configuration](#manifest-configuration)  
   - [Simulation experiment configuration](#simulation-experiment-configuration)  
   - [Submit run and analyze simulations](#submit-run-and-analyze-simulations)  
   - [Output files and metrics](#output-files-and-metrics)
   - [Customizing simulation and outputs](#customizing-simulation-and-outputs)
6. [Installation](#installation)
7. [Troubleshooting](#troubleshooting)
8. [Change log](#change-log)

------------------------------------- 

## Goal

To characterize the basic transmission and disease dynamics of malaria simulated using EMOD and OpenMalaria
using a simple python framework and allow flexible user-specific plotting.

**Objectives:**

1) Model characterization - basic transmission and disease dynamics:
    - Explore and describe basic transmission and disease dynamics
2) Model behaviour - effects of perturbation of the system:
    - Treatment of cases and contribution of cases to onward transmission
    - Infection clearance, short and long term prevention
    - Vector control effects on mosquito life and feeding cycle



**Repositories of malaria models used and frameworks utilized:**  

- **EMOD** - Institute for Disease Modeling (IDM): [idmtools](https://github.com/InstituteforDiseaseModeling/idmtools), [emodpy-malaria](https://github.com/InstituteforDiseaseModeling/emodpy-malaria),
emod-api, emodpy   
- **OpenMalaria** - Swiss Tropical and Public Health Institute (Swiss TPH): [openmalaria](https://github.com/SwissTPH/openmalaria/) , ([r-openMalariaUtilities](https://github.com/SwissTPH/r-openMalariaUtilities))   
- **malariasimulation** - Imperial College London (ICL): [malariasimulation](https://github.com/mrc-ide/malariasimulation/tree/master)   


-------------------------------------

## Setup

### Repository structure 
The repository has a nested structure with model specific input and helper functions within sub-directories.  
The model-specific scripts mimic the same file names and content as much as possible to not have to search the equivalent script for each new model.  
The main configuration `manifest.py` and test simulation script `launch_test.py` are located directly under the root directory. 

    .  
    ├─ EMOD/                            # EMOD inputs and specific functions
    │   ├─ inputs/
    │   │   └─ ... 
    │   ├─ scaffolds/
    │   │   ├─ forcedEIR.py             
    │   │   └─ interventions.py 
    │   ├─ analyze_sim.py
    │   ├─ sample_plots.py
    │   └─ utils.py 
    ├─ OpenMalaria/                     # OpenMalaria inputs and specific functions  
    │   ├─ scaffolds/
    │   │   └─ ... 
    │   ├─ analyze_sim.py  
    │   ├─ measures.py
    │   ├─ sample_plots.py
    │   └─ utils.py 
    ├─ malariasimulation/               # malariasimulation inputs and specific functions   (coming soon)
    │   ├─ ...  
    │   └─ ...  
    ├─ custom_plotter/                  # Unstructured collection of custom figures scripts (optional)
    │   └─ ...  
    ├─ sim_popsize/                     # Alternative use of framework to sweep uncommong parameters (example)
    │   └─ ...  
    ├─ simulations/                     # Collection of sub-question specific simulation scripts (coming soon)  
    │   └─ ...  
    ├─ static/                          # Readme images 
    │   └─ ...  
    ├─ benchmark_plots.py               # Default plots for model comparison 
    ├─ functions.R                      # Helper functions for custom R plots (optional)   
    ├─ helper.py _(required)_  
    ├─ launch_test.py                   # Base-case simulation script used for testing  
    └─ manifest.py                      # Configuration of system defaults, HPC account, directories   

 
### Programming language
- Python had been selected as the main programming language, whereas previous frameworks in R do at varying extent exist for the different models. 
- In general, the framework is aimed to be flexible enough to integrate model-specific R scripts for generating or postprocessing results, as long as integrated into the main python pipeline (i.e. via sourcing of R scripts), however full integration into python is preferred.
- R is often preferred for generating results and plots, as seen in the sub-directory `custom_plotter`. 
- Other software languages used for handling model inputs or HPC job submission are `XML`, `json`, and `shell` scripts, as well as `txt` and `log` text files.


<details><summary><span>Expand to view conceptual figure</span></summary>
<p>

![Schematic of simulation analysis worklfow](https://github.com/numalariamodeling/model-characterization/blob/main/static/flowchart.png)
</p>
</details>


### Simulation framework 

The repository and programming heavily follows the structure and requirements of a simulation in EMOD using IDM's programming framework (emodpy, idmtools) for generating, submitting and post-processing simulations.
The name of some input and output names have been predominantly aligned to OpenMalaria conventions where possible.  

A single `launch_test.py` python script launches the simulation experiment with parameters defined directly in the file
Helper functions for EMOD and OpenMalaria, stored in 'utils.py' in model specific subfolders are sourced in  the  `launch_test.py` python script.   

![Simulation framework](https://github.com/numalariamodeling/model-characterization/blob/main/static/emod-om-framework.png)


Alternatively, one can have project specific `utils` and `analyzer` scripts within a project folder and have them named differently for EMOD
and OpenMalaria (i.e.  `utils_om.py / utils_om.py` and `analyzer_em.py / analyzer_em.py `. 
This approach allows more flexible editing, i.e. when using project specific or experiment specific parameter definitions and analyzer files that are not integrated into the default scripts, or would change too much.
(example `sim_popsize`)




<details><summary><span>List of functions</span></summary>
<p>

_Table: Main scripts and functions_

| launch_test.py*                                 | helper.py                  |
|-------------------------------------------------|----------------------------|
| [ parameter definitions ]                       | parse_args                 |
| update_param_default  (emod)                    | make_dirs                  |
| update_param_climate  (emod)                    | get_time_param             |
| set_param_fn   (emod)                           | save_exp_scen              |
| build_campaign   (emod)                         | get_seasonal_eir           |
| update_campaign_multiple_parameters_wEIR (emod) | create_scenarios_csv       |
| update_campaign_multiple_parameters  (emod)     | as_list                    |
| update_eir_scale   (emod)                       | shell_header_quest         |
| sweep_burnin_simulations  (emod)                | write_txt                  |
| submit_create_run_EMOD  (emod)                  | submit_analyze_OpenMalaria |
| submit_run_OpenMalaria (OpenMalaria)            | submit_analyze_EMOD        |
|                                                 | submit_run_pyscript        |
|                                                 | emodpy_module              |
|                                                 | OM_module                  |
|                                                 | combine_emodom_results     |
|                                                 | str_to_digit               |
|                                                 | pretty_legend              |

* ) this file includes building the "json scaffold" for EMOD, and for each new simulation experiment a new launch.py
  should be created.

_Table: EMOD functions_

| EMOD/utils.py                  | EMOD/scaffolds               | EMOD/analyze_sim.py                        |
|--------------------------------|------------------------------|--------------------------------------------|
| set_param                      | forcedEIR                    | InsetChartAnalyzer                         |
| build_demog                    | interventions/treatment_camp | BenchmarkAnalyzer                          |
| build_standard_campaign_object | ...                          | MonthlyBenchmarkAnalyzer                   |
| add_monthly_reports            |                              | AnnualBenchmarkAnalyzer                    |
| add_annual_reports             |                              | MonthlyAgebinAnalyzer                      |
| _get_serialized_filenames      |                              | AnnualAgebinAnalyzer                       |
| _get_core_counts               |                              | TransmissionReport (dynamic EIR mode only) |
| get_workdir_from_simulations   |                              |                                            |
| create_sim_directory_map       |                              |                                            |
| build_burnin_df                |                              |                                            |

_Table: OpenMalaria functions_

| OpenMalaria/utils.py   | OpenMalaria/scaffolds | OpenMalaria/analyze_sim.py                                                                |
|------------------------|-----------------------|-------------------------------------------------------------------------------------------|
| create_scenarios_OM    | R0000GA.xml           | BaseAnalyzer  (optional for raw output)                                                   |
| submit_run_OpenMalaria | ...                   | SurveyAllAgeAnalyzer   (equivalent to InsetChartAnalyzer )                                |
|                        |                       | InputEIRAnalyzer (equivalent to TransmissionReport, <br/> requried for BenchmarkAnalyzer) |
|                        |                       | BenchmarkAnalyzer                                                                         |
|                        |                       | MonthlyBenchmarkAnalyzer                                                                  |
|                        |                       | AnnualBenchmarkAnalyzer                                                                   |
|                        |                       | MonthlyAgebinAnalyzer                                                                     |
|                        |                       | AnnualAgebinAnalyzer                                                                      |
|                        |                       | several helper functions                                                                  |

</p>
</details>



### Model inputs and scaffolds
In OpenMalaria, the simulation setup to run is not created 'on the fly' as for EMOD, but is pre-specified in the XML file.  
[...]


### EMOD serialization
One functional difference between EMOD and other malaria models is the process of serialization (to run multiple simulations on the same population in series).  
- Serialization allows the user to run a simulation, save their status and results at a specified point in time, and start another simulation (i.e. with modified campaigns) that continues from the point saved.   
- In EMOD, this is often applied to first run the  `burnin` the long initial simulation run, during which population immunity is established, followed by the `pickup` which defines the often typical scenario explorations.  
- Hence, to avoid running the long initial period everytime, the user can serialize the population at the end of the burnin and then run shorter simulations on that population with varying campaign parameters (that do not affect population characteristics).   
  
The following parameters need editing in `launch_test.py`:
- To run a burnin simulation :
    - Set `emod_step = ‘burnin’` .
    - Set `burnin = <num of years>` to define duration of the burnin period (which is also used in OpenMalaria, however runs much quicker than in EMOD).
    - The experiment ID for this burnin simulation will be needed when running the pickup simulation (and is saved automatically in <exp_name> folder, and also printed to console).
- To run a pickup simulation(s):
    - Set `emod_step = ‘pickup’`
    - Set `emod_serialized_id = <burnin experiment id>`
    - Pickup simulations cannot run without an attached experiment id.
- To run a burnin and pickup simulation (without serializing, as selected as default for testing):
    - Set `emod_step = None`



## Scenarios implemented
coming soon

### Base case 
(including case management)
coming soon


------------------------------------- 

## Running simulations

- Simulations are assumed to run on a linux based high performance cluster (HPC), the framework is not designed for running simulations locally
- Main programming language is `Python` , whereas `R` might be used as well where better suited, or for custom  plotting
- Install required software for OpenMalaria and EMOD (note on NUCLUSTER AND SciCore software has already been installed)  

_see detailed instructions [here](https://github.com/numalariamodeling/model-characterization#installation)_

### Manifest configuration

- When running for the first time, open and edit `manifest.py` to enter HPC specification and default directories
  - `hpc`: name of cluster (str) 
  - `sh_hpc_config`: specification for slurm submission (dict), example `sh_hpc_config={'A': 'b1139', 'p': 'b1139', 'em_modules': 'singularity', 'buyin': True}`
  - `projdir`: path to directory where to store experiment and simulation outputs 
  - `job_directory`: path to directory where to store experiments, i.e. `job_directory = os.path.join(projdir, 'experiments')`
  - `SIF_PATH`: path to EMOD emodpy image (see EMOD installtion)
  - `OM_PATH`: path to OpenMalaria requirements to run model (see OpenMalaria installation)
  - `om_input_path`: path to OpenMalaria sub-directory of this git repository cloned on HPC
  - `output_directory`: path to directory where to store simulation resultr (summarized outputs), i.e. `output_directory = os.path.join(projdir, 'simulation_outputs')`


### Simulation experiment configuration
The simulation inputs are directly defined in the python scripts, which will generate a scenario csv, rather than writing the csv and reading it in (this option will be made available)
The `launch_test.py` is the go-to script to get started and do test simulation runs, it does run a 'base-case' scenario with only including case management but no other interventions.  


- [ ] **Simulation experiment name, infractructure, directories and models to run**
  - [mem_increase_factor](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L23C1-L23C20): scaling factor on default memory requested, which usually can be left at 1 for test simulation, but may have to be 2 or 3 for larger simulations. The default memory requested also differs for the slurm job submission to run versus to analyze a simulation.
  - [custom_subdir](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L26): If `None`, no i.e. user specific subdir created, default `os.getlogin()`
  - [SUITEname](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L27): overall subdir to declare a group of simulations to run, default is `f'{entomology_mode}EIR'`
  - [exp_name](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L28): name of simulation experiment to run, default is `f'sim_{dt.now().strftime("%Y_%m_%d_%H_%M_%S")}'`, whereas a more meaningful name might be choosen for simulation experiments to use outputs for some result description rather than just for testing.
  - [models_to_run](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L36): Name of models to run (case-sensitive), options are 'EMOD' and/or 'OpenMalaria'
  - [om_scaffold](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L40): name of OpenMalaria input XML to use 


- [ ] **Population size, agebins and seeds**
  - [pop_size](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L44): number of individuals to simulate for human population, default for testing `1000`, which should not be used for actual simulations to generate results
  - [agebins](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L45): age groups to monitor (select finest age groups required, can be further combined in postprocessing)
  - [num_seeds_burnin](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L47): EMOD specific (even  if not declared as such), number of seeds to run for burnin if run separately
  - [num_seeds](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L47): number of seeds to run for simulation (applies to all models)
  - [sweep_list](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L58): List of parameter names that together uniquely identify a simulation scenario (and will be written into `scenarios.csv`)


- [ ] **Simulation time and reporting intervals**
  - [start_year](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L49): Calendar year at which monitoring period should start (after burnin)
  - [end_year](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L49): Calendar year at which monitoring period should end 
  - [burnin](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L51): Number of years to run prior to monitoring period (from these the simulation start year will be calculated) 
  - [om_survey_step](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L41): survey intervals for which outcomes are reported in OpenMalaria, default is `30d`. Note, in EMOD, monthly reports are per default included in monitored simulation period. 
  - [emod_step](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L32): EMOD allows to run burnin separate from the monitoring period (here equivalent to `pickup`), if `None` both similation times are run together, which can be computational and time-wise too extensive when running long burnin, large populations and high EIRs. 
  - [emod_serialized_id](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L33): ID of EMOD burnin experiment to pickup from, if `emod_step ='pickup'`
 

- [ ] **Case management parameters**    
  - [cm_start](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L72): do not change, can be removed, case managament would always start on day 1, except of having multiple intervention deployments to simulate coverage increase over time (not applicable here)
  - [cm_clinical](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L73): clinical case management coverage
  - [cm_severe](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L74): do not change, will be adapted depending on clinical case management, but to be at least 48%
  - [detectionLimit](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L75): detection limit for parasites per micoliter blood for detection of prevalent malaria infections


- [ ] **Transmission intensity and seasonality**    
  - [entomology_mode](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L22): select whether to run with vectors (`dynamic`) or without (`forced`)
  - [seasonality](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L78): name of pre-defined transmission seasonality profile to simulate (current options are `["perennial", "seasonal"]`)
  - [eir](https://github.com/numalariamodeling/model-characterization/blob/main/launch_test.py#L79): annual input EIR (when using `forced EIR`)

_Note the order of parameters differs for some in the python script_


### Submit run and analyze simulations

- In terminal navigate to repository  `cd ~/model-characterization`
- Run python script that defines the simulation i.e. `python launch_test.py` for a test run
- Check simulations via `squeue -u <username>`
- Wait for simulations to finish after which analyzer scripts and default plots will automatically start running  
- If you need to resubmit the `analyze_sim.py` script, it can be found in `experiments/<suite>/<exp_name>`
     ```
      cd /home/mrm9534/model-characterization/EMOD  
      python analyze_sim.py -d /projects/b1139/emod-om/experiments/forcedEIR/baseline_noCM_EIRseason -i
      fb508aba-2aa7-43b3-b365-ea7c227d7781
     ``` 
- Perform additional analysis or plot custom results 

![experiment config folder](https://github.com/numalariamodeling/model-characterization/blob/main/static/simulation_directories.png)



### Output files and metrics

Several custom output csv tables that can be used to generate figures and other results for model characterization.
The file names have been mostly aligned to EMOD, whereas the name of outcome metrics have been mostly aligned to
OpenMalaria, as 'more fixed' as in EMOD.


**Time-series:** 
  - `All_Age_InsetChart.csv`: _All age_ per timestep and basic simulation outputs for checking simulations 
  - `PfPR_ClinicalIncidence_mth.csv`: _Age-bin_ specific key malaria outcomes* over time aggregated by month-year 
  - `PfPR_ClinicalIncidence_yr.csv`: _Age-bin_ specific key malaria outcomes* over time aggregated by year 

**Aggregated times for relationship and seasonality trends (benchmarking):**
  - `Benchmark.csv`: _Age-group_ specific key malaria outcomes* and transmission outcomes**, aggregated over whole monitoring period 
  - `Benchmark_mth.csv` _Age-group_ specific key malaria outcomes* and transmission outcomes**, aggregated per month over whole monitoring period  
  - `Benchmark_yr.csv` _Age-group_ specific key malaria outcomes* and transmission outcomes**, aggregated per year over whole monitoring period  

**Additional output files:**
- `EIR.csv` and `EIR_mth.csv`: All age simulated EIR (added to benchmark output csvs), currently specific to OpenMalaria as not applicable to forced EIR in EMOD
- `Surveyoutput_base.csv`: Raw output for OpenMalaria from concatenating survey outputs, optional i.e. for testing.
- `Event reporters ..` to be added 

<details><summary><span>Click here to view key columns in output files </span></summary>
<p>


**Table:** Key columns in output files.


| category         | column            | description                                                                                               | OpenMalaria                                          | EMOD                                                                        |
|------------------|-------------------|-----------------------------------------------------------------------------------------------------------|------------------------------------------------------|-----------------------------------------------------------------------------|
| sweepvariables   | eir               | annual transmission intensity (all   ages, across all vectors)                                            |                                                      |                                                                             |
| sweepvariables   | cm_clinical       | clinical treatment coverage (all   ages)                                                                  |                                                      |                                                                             |
| sweepvariables   | cm_severe         | severe treatment coverage (all ages)                                                                      |                                                      |                                                                             |
| sweepvariables   | seasonality       | name of seasonality profile (all vectors)                                                                 | translates to monthly EIR and fourier transformation | translates to daily EIR                                                     |
|                  |                   |                                                                                                           |                                                      |                                                                             |
| setup, age, time | seed              | number of stochastic replication run                                                                      |                                                      | Run_Number                                                                  |
| setup, age, time | ageGroup          | min-max age for agebins or   aggregated into larger age groups (benchmark outputs)                        |                                                      |                                                                             |
| setup, age, time | agebin           | upper age limits as defined in   simulation input                                                         |                                                      |                                                                             |
| setup, age, time | date              | yyyy-mm-dd, day is set to 1, if not   using monthly intervals, month set to January                       |                                                      |                                                                             |
| setup, age, time | year              | simulation year in calendar format (i.e. 2000)                                                            | every 72 timesteps                                   | every 365 days                                                              |
| setup, age, time | month             | month number (1-12)                                                                                       | every 6 timesteps                                    | every 30 days                                                               |
|                  |                   |                                                                                                           |                                                      |                                                                             |
| outcome          | nHost             | total population size simulated                                                                           | default output, all age                              | Average Population by Age Bin    (Statistical Population in InsetChart)     |
| outcome          | nPatent           | number of population with parasite densities above detection limit                                        | default output, all age                              | calculated                                                                  |
| outcome          | nUncomp           | nunber of population having a clinical malaria episode                                                    | default output, all age                              | calculated                                                                  |
| outcome          | nSevere           | number of population having a severe malaria episode                                                      | default output, all age                              | calculated                                                                  |
| outcome          | prevalence        | proportion of population with parasite densities above detection limit                                    | calculated nPatent/nHost                             | PfPR by Age Bin in Summary Report                                           |
| outcome          | clinical_incidence | clinical malaria episodes per person per year                                                             | calculated                                           | Annual Clinical Incidence by Age Bin     (New Clinical Cases in InsetChart) |
| outcome          | severe_incidence  | severe malaria episodes per person    per year                                                            | calculated                                           | Annual Severe Incidence by Age Bin     (New Severe Cases in InsetChart)     |
| outcome          | prevalence_2to10  | proportion of population with parasite densities above detection limit in   population aged 2 to 20 years | calculated                                           | PfPR_2to10                                                                  |
| outcome          | inputEIR          | input EIR per reporting interval                                                                          | default output, all age                              | NA                                                                          |
| outcome          | simulatedEIR      | simulated EIR per reporting interval                                                                      | default output, all age                              | called 'EIR'   in InsetChart, not   applicable for forced EIR               |


</p>
</details>


### Customizing simulation and outputs
To customize a simulation, any of the defined parameters listed in [Simulation experiment configuration](https://github.com/numalariamodeling/model-characterization#simulation-experiment-configuration) can be changed.
Commonly modified parameters are eir, seasonality, burnin period, and sometimes cm_clinical, for base-case scenario runs.
Additional interventions are not possible using the `launch_test.py`, and instructions for simulating other interventions will come soon [Setting up new simulation scenarios](https://github.com/numalariamodeling/model-characterization#setting-up-new-simulation-scenarios)


-------------------------------------

## Installation

On the NU cluster `Quest` OpenMalaria and EMOD are already installed and accessible for all users in group.
On the STPH cluster `SciCore` OpenMalaria and EMOD are already installed and accessible for all users in group.

If you need to installl, below are the installation instructions:

<details><summary><span>Expand installation instructions</span></summary>
<p>

[EMODpy installation IDM](https://docs.idmod.org/projects/emodpy/en/v1.19.0/installation.html).
[EMODpy installation additions NU for NUCLUSTER](https://numalariamodeling.github.io/FE-2023-quarto-website/guides/install_guide.html).

[OpenMalaria installation STPH](https://github.com/SwissTPH/openmalaria/wiki/UserGuide#Installing-OpenMalaria)

NU IT research (Scott Coughlin) built a container and sent instructions which have been edited for completeness and are
shown below:
One can build the container on Quest using the remote Sylabs build environment

```
module load singularity
singularity remote login
```

An access token is already set for this remote. Replace it? [N/y] y
Generate an access token at https://cloud.sylabs.io/auth/tokens, and paste it here.
..
..

```
singularity build --remote OpenMalaria.sif OpenMalaria.def
```

Because calling containers is very annoying, Scott also added a module file in this folder which wraps the call to
openMalaria to make it easier to use.
Please see this example below which can be run in `/projects/b1139/OpenMalaria/`

```
cd OpenMalaria
module use /projects/b1139/OpenMalaria/modules/
module load openmalaria
openMalaria -s example_scenario.xml
```

</p>
</details>



------------------------------------


[EMOD](https://docs.idmod.org/projects/emod-malaria/en/latest/index.html)
and [OpenMalaria](https://github.com/SwissTPH/openmalaria/wiki) are both individual-based malaria epidemiology and
transmission models that have been widely used in malaria research.

<details><summary><span>Click here to expand resources</span></summary>
<p>


**EMOD** (Epidemiological MODeling software) has been developed and is maintained by
the [Institute for Disease Modeling (IDM)](https://www.idmod.org/), and also used by
the [Malaria Modeling Group at Northwestern University](https://www.numalariamodeling.org/).

**OpenMalaria** has been developed and is maintained by
the [Swiss Tropical and Public Health Institute (Swiss TPH)](https://www.swisstph.ch/en/about/eph/disease-modelling/).

Table 1: Overview of model software and infrastructure

|                   | EMOD                                                                                                   | OpenMalaria                                                                         | Malariasimulation                                                                   |
|-------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| Documentation     | https://docs.idmod.org/projects/emod-malaria/en/latest/index.html                                      | https://github.com/SwissTPH/openmalaria/wiki                                        | https://github.com/mrc-ide/malariasimulation                                        |
| Accessibility     | Open source                                                                                            | Open source                                                                         | Open source (R package)                                                             |
| Language          | C++                                                                                                    | C++                                                                                 | C++                                                                                 |
| First published   | 2013                                                                                                   | 2006-2008                                                                           |                                                                                     |
| Models            | Individual-based human model <br>Population based vector model  <br> PkPD submodel. <br> Spatial model | Individual-based human model <br>Population based vector model <br> (...) <br> <br> | Individual-based human model <br>Population based vector model <br> (...) <br> <br> |
| Framework         | Python (dtk-tools)                                                                                     | custom by user group                                                                | R >= 4.0.0                                                                          |                       
| OS                | Windows, Linux                                                                                         | Windows, Linux, (Mac OS)                                                            |                                                                                     |            
| Default timesteps | 1 day                                                                                                  | 5  day                                                                              |                                                                                     |                                                           
| Input file type   | json                                                                                                   | XML                                                                                 |                                                                                     |                                                       
| Output file type  | json                                                                                                   | txt                                                                                 |                                                                                     |                                          
| N input files     | 5+                                                                                                     | 1                                                                                   |                                                                                     |  
| N output files    | custom                                                                                                 | 2                                                                                   |                                                                                     |   
| Glossary          | [link](https://docs.idmod.org/projects/emod-malaria/en/latest/glossary.html)                           | [link](https://github.com/SwissTPH/openmalaria/wiki/Terminology)                    |                                                                                     |  

### Ensemble modeling and comparisons using both models

- **Public health impact and cost-effectiveness of the RTS,S/AS01 malaria vaccine: a systematic comparison of
  predictions from four mathematical models** <br>Penny MA, Verity R, Bever CA, Sauboin C, Galactionova K, Flasche S,
  White MT, Wenger EA, Van de Velde N, Pemberton-Ross P, Griffin JT, Smith TA, Eckhoff PA, Muhib F, Jit M, Ghani AC. .
  Lancet. 2016 Jan 23;387(10016):
  367-375. [doi: 10.1016/S0140-6736(15)00725-4.](https://pubmed.ncbi.nlm.nih.gov/26549466/)
- **Defining the relationship between infection prevalence and clinical incidence of Plasmodium falciparum malaria.
  **<br>Cameron, E., Battle, K., Bhatt, S. et al. Nat Commun 6, 8170 (
  2015). [https://doi.org/10.1038/ncomms9170](https://www.nature.com/articles/ncomms9170)
- **Role of mass drug administration in elimination of Plasmodium falciparum malaria: a consensus modelling study**<br>
  Brady OJ, Slater HC, Pemberton-Ross P, Wenger E, Maude RJ, Ghani AC, et al. The Lancet Global Health. 2017;0.
  doi:[10.1016/S2214-109X(17)30220-6](https://doi.org/10.1016/S2214-109X(17)30220-6)
- **OpenMalaria and EMOD: A Case Study on Model Alignment** <br>Ferris C, Raybaud B, Madey G. San Diego, CA, USA:
  Society for Computer Simulation International; 2015. pp. 1–9. http://dl.acm.org/citation.cfm?id=2874916.2874952
- [VecNet](http://web.archive.org/web/20170711052751/https://www.vecnet.org/index.php/about-vecnet)
  and [VecNet-DW](https://academic.oup.com/database/article/doi/10.1093/database/bax073/4372201?login=false) (
  discontinued)
- **Pre-existing partner-drug resistance to artemisinin combination therapies facilitates the emergence and spread of
  artemisinin resistance: a consensus modelling study.** <br> Watson OJ, Gao B, Nguyen TD, Tran TN-A, Penny MA, Smith
  DL, et al. The Lancet Microbe. 2022.
  doi:[10.1016/S2666-5247(22)00155-0](https://doi.org/10.1016/S2666-5247(22)00155-0)

</p>
</details>


------------------------------------

## Troubleshooting

- No results in simulation outputs
    - analyzer did not run correctly -> try rerunning by submitting corresponding sbatch file, or copy command in
      terminal
        - slurm job id dependency not satisfied
        - error in analyzer script
    - simulation failed -> check log/error files
        - simulations cancelled due to memory or time limit issue
        - simulation had not been submitted due to errors in the input files
    - ...
 
------------------------------------    

## Change log
- August 2023: start integrating Imperial College London's malaria model `malariasimulation`, start dynamic EIR
- July - August 2023: bugfixes and improvements to framework, timeseries, initial parameter exploration
- March 2023 - June 2023: initial python framework with CM only and forced EIR
- March 2023: Repository created following up on the lessons learned from the SwissTPH "MC benchmarking" framework in R


See planned next steps and issues at:  [/model-characterization/issues](https://github.com/numalariamodeling/model-characterization/issues#workspaces/emodopenmalaria-643ac4533584b28586ce8b39/roadmap)
