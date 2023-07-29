# Characterization and comparison of EMOD and OpenMalaria
_[EMOD](https://docs.idmod.org/projects/emod-malaria/en/latest/index.html) | [OpenMalaria](https://github.com/SwissTPH/openmalaria/)_  

_Disclaimer: This repository is under active development, if something is not working, please contact us - or simply create an issue on GitHub that we can follow up on._

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


-------------------------------------  

**Repositories of malaria models used and frameworks utilized:**  
EMOD (
IDM): [idmtools](https://github.com/InstituteforDiseaseModeling/idmtools), [emodpy-malaria](https://github.com/InstituteforDiseaseModeling/emodpy-malaria),
emod-api, emodpy   
OpenMalaria (Swiss
TPH): [openmalaria](https://github.com/SwissTPH/openmalaria/) , ([r-openMalariaUtilities](https://github.com/SwissTPH/r-openMalariaUtilities))   

-------------------------------------

## Repository structure and simulation framework

- **EMOD** (required, EMOD inputs and specific functions)
- **OpenMalaria** (required, OpenMalaria inputs and specific functions)
- **custom_plotter** (optional, unstructured collection of custom figures scripts)
- **sim_popsize** (optional, example of a sub-question specific modification of the utilities provided in framework)
- **simulations** (optional, directory to eventually store sub-question specfic simulation scripts (adapted from launch_test.py, i.e. with SMC etc))
- **static** (readme images)
- `benchmark_plots.py` (required, default plots for model comparison)
- `functions.R` (optional, helper functions for custom R plots)
- `helper.py` (required)
- `launch_test.py` (define and submit a simulation experiment in EMOD and in OpenMalaria, via wrapper functions for separate submission)
- `manifest.py` (configuration file for system defaults and directories, model versions to run, HPC account)

Implemented simulation framework:  
**Option 1 (default for testing)**

- single `launch_test.py` python script to launch the simulation experiment with parameters defined directly in the file
- helper functions for EMOD and OpenMalaria, stored in 'utils.py' in model specific subfolders are sourced in
  the  `launch_test.py` python script
- The postprocessing via analyzers has the same structure, with analyzer files of the same name located in the model
  subfolders.
- Example: directory `simulations`

**Option 2 (alternative if requiring extensive modifications of default scripts)**

- Have project specific `utils` and `analyzer` scripts within project folder and have them named differently for EMOD
  and OpenMalaria (i.e.  `utils_om.py / utils_om.py` and `analyzer_em.py / analyzer_em.py `.
- This approach allows more flexible editing, i.e. when using project specific or experiment specific parameter
  definitions and analyzer
  files that are not integrated into the default scripts, or would change too much.
- Example: directory `sim_popsize`

![Simulation framework](https://github.com/numalariamodeling/model-characterization/blob/main/static/emod-om-framework.png)


<details><summary><span>Expand to view conceptual figure</span></summary>
<p>

![Schematic of simulation analysis worklfow](https://github.com/numalariamodeling/model-characterization/blob/main/static/flowchart.png)
</p>
</details>


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

------------------------------------- 
## Getting started

### Installation and software

- Both models are assumed to run on a linux based cluster and the framework is not designed to run simulations locally
- Python software is used for the general framework, while R might be used as well where better suited, or for custom
  plotting
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
  - `om_input_path`: path to OpenMalaria sub-directory of this repository cloned on HPC
  - `output_directory`: path to directory where to store simulation resultr (summarized outputs), i.e. `output_directory = os.path.join(projdir, 'simulation_outputs')`


### Running a simulation

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




### Output files

Several custom output csv tables that can be used to generate figures and other results for model characterization.
The file names have been mostly aligned to EMOD, whereas the name of outcome metrics have been mostly aligned to
OpenMalaria, as 'more fixed' as in EMOD.


**Time-series:** 
  - All age per timestep and basic simulation outputs for checking simulations (i.e. `All_Age_InsetChart.csv` )
  - Age-group specific key malaria outcomes* over time aggregated by month-year, or annual (i.e. `PfPR_ClinicalIncidence_mth.csv`)

**Aggregated times for relationship and seasonality trends (benchmarking):**
  - Age-group specific key malaria outcomes* and transmission outcomes**, aggregated over whole monitoring period (i.e. `\<model>_benchmark.csv   `)
  - Age-group specific key malaria outcomes* and transmission outcomes**, aggregated per month over whole monitoring period  (i.e. `\<model>_benchmark_mth.csv   `)

.* _mainly prevalence, clinical & severe incidence_  
.** _mainly EIR, prevalence 2-10_

<details><summary><span>Click here to view detailed table </span></summary>
<p>


**Table:** List of custom output csv tables for model characterization.

| Output files                                                           | Description                                                                                                                                                                                                                                                                                                                                | ncolumns (excluding custom sweep variables) | outcome measures                                                                                                                                                                                                        | EMOD                                                                                                                                                                                          | OpenMalaria                                                                                                                                                   |
|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------|
| All_Age_InsetChart.csv                                                 | basic simulation outcomes for the total population per timestep for the whole simulation duration if not specified otherwise, mainly used for checking whether simulation ran as expected.                                                                                                                                                 | ~16-34                                      | specific as defined in each model, not aligned in name or unit, usually including date, seed, prevalence, clinical & severe incidence, treatments, deaths measures                                                      | generated from InsetChart.json (or MalariaFilteredReport.json) output, which are tracking the whole population per timestep for a set of default outcome metrics                              | generated from the survey output aggregated for all age groups, per reporting interval for a set of selected variables in alignment to EMOD's InsetChart.json |
| PfPR_ClinicalIncidence_mth.csv                                         | simulation results in survey format over time per reporting interval per defined age groups for main outcomes of interest (prevalence, clinical  and severe incidence)  per month over time of monitoring period                                                                                                                           | 15                                          | simulation output over time (month and year) and by age group and unique scenario identifiers for model specific outcomes (not yet aligned), usually including time, age, seed, prevalence, clinical & severe incidence | generated from MalariaSummaryReport, which allows age specific outcomes at defined intervals for a specific duration of the simulation - kept at monthly levels if reporting intervals allows | currently named  OM_surveyoutput_mth.csv                                                                                                                      |
| PfPR_ClinicalIncidence_yr.csv (remove?)                                | simulation results in survey format over time per reporting interval per defined age groups for main outcomes of interest (prevalence, clinical and severe incidence) aggregated per year for the monitored period                                                                                                                         | 11                                          | simulation output over time (year) and by age group and unique scenario identifiers for model specific outcomes (not yet aligned) ,usually including time, age, seed, prevalence, clinical & severe incidence           | generated from MalariaSummaryReport, which allows age specific outcomes at defined intervals for a specific duration of the simulation - aggregated per year from monthly output              | currently named  OM_surveyoutput_yr.csv                                                                                                                       |
| \<model>_benchmark.csv                                                 | simulation results generated from the PfPR_ClinicalIncidence outputs, with outcomes aggregated across observation period and additional column for transmission intensity (EIR) used for describing general relationships across transmission and disease outcomes by age                                                                  | 11                                          | aligned, rows per scenario and age group, columns include nHost, prevalence, prevalence2-10, clinical_incidence, severe_incidence, (mortality), sweep variables (custom), index, eir specifications,  and age group     |                                                                                                                                                                                               |                                                                                                                                                               |
| \<model>_benchmark_mth.csv                                             | simulation results generated from the PfPR_ClinicalIncidence outputs, with outcomes aggregated across observation period and additional column for transmission intensity (EIR) used for describing seasonal trends for transmission and disease outcomes by age or selected age group                                                     | 12                                          | + month                                                                                                                                                                                                                 |                                                                                                                                                                                               |                                                                                                                                                               |
| \<model>_benchmark_yr.csv                                              | simulation results generated from the PfPR_ClinicalIncidence outputs, with outcomes aggregated across observation period and additional column for transmission intensity (EIR) used for describing long-term, annual trends for transmission and disease outcomes by age or selected age group (similar to PfPR_ClinicalIncidence_yr.csv) | 12                                          | + year                                                                                                                                                                                                                  |                                                                                                                                                                                               |                                                                                                                                                               |
| \<model>_EIR.csv  (optional, added to, <model>_benchmark.csv )         | simulated transmission intensity mean across monitoring period,  if available                                                                                                                                                                                                                                                              | 6                                           | at least inputEIR, simulatedEIR and unique scenario identification columns plus seeds                                                                                                                                   | only generated when running with vector model ('dynamic EIR')                                                                                                                                 | can be generated for both tranmission modes (forced or dynamic)                                                                                               |
| \<model>_EIR_mth.csv  (optional, added to, <model>_benchmark_mth.csv ) | simulated transmission intensity per month and year (_NOT_ aggregated over monitoring period),  if available                                                                                                                                                                                                                               | 7                                           | as above + year and month                                                                                                                                                                                               | only generated when running with vector model ('dynamic EIR')                                                                                                                                 | can be generated for both tranmission modes (forced or dynamic)                                                                                               |

</p>
</details>

### Troubleshooting

- No results in simulation outputs
    - analyzer did not run correctly -> try rerunning by submitting corresponding sbatch file, or copy command in
      terminal
        - slurm job id dependency not satisfied
        - error in analyzer script
    - simulation failed -> check log/error files
        - simulations cancelled due to memory or time limit issue
        - simulation had not been submitted due to errors in the input files
    - ...

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

|                   | EMOD                                                                                                   | OpenMalaria                                                                         |
|-------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|
| Documentation     | https://docs.idmod.org/projects/emod-malaria/en/latest/index.html                                      | https://github.com/SwissTPH/openmalaria/wiki                                        |
| Accessibility     | Open source                                                                                            | Open source                                                                         |
| Language          | C++                                                                                                    | C++                                                                                 |
| First published   | 2013                                                                                                   | 2006-2008                                                                           |
| Models            | Individual-based human model <br>Population based vector model  <br> PkPD submodel. <br> Spatial model | Individual-based human model <br>Population based vector model <br> (...) <br> <br> |
| Framework         | Python (dtk-tools)                                                                                     | custom by user group                                                                |                         
| OS                | Windows, Linux                                                                                         | Windows, Linux, (Mac OS)                                                            |              
| Default timesteps | 1 day                                                                                                  | 5  day                                                                              |                                                             
| Input file type   | json                                                                                                   | XML                                                                                 |                                                         
| Output file type  | json                                                                                                   | txt                                                                                 |                                            
| N input files     | 5+                                                                                                     | 1                                                                                   |    
| N output files    | custom                                                                                                 | 2                                                                                   |     
| Glossary          | [link](https://docs.idmod.org/projects/emod-malaria/en/latest/glossary.html)                           | [link](https://github.com/SwissTPH/openmalaria/wiki/Terminology)                    |    

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

## Change log

- July 2023: bugfixes and improvements to framework, start parameter exploration
- March 2023 - June 2023: initial python framework with CM only and forced EIR
- March 2023: Repository created following up on the lessons learned from the SwissTPH "MC benchmarking" framework in R

Next:

- calibrate dynamic EIR
- add SMC
- add/ improve error capturing and documentation
- add automatic cleanup options
- improve handling of SUITEnames and folder structure
- fix hardcoded age groups, allow flexible age groups (error in OpenMalaria postprocessing)
- event plotter

See all issues
here:  [/model-characterization/issues](https://github.com/numalariamodeling/model-characterization/issues#workspaces/emodopenmalaria-643ac4533584b28586ce8b39/roadmap)
