# Characterization and comparison of EMOD and OpenMalaria

_Model features and simulated transmission and disease dynamics_


## Project goal
To characterize the basic transmission and disease dynamics of malaria simulated using EMOD and OpenMalaria.

Objectives:
1) Model characterization - basic transmission and disease dynamics:
   - Explore and describe basic transmission and disease dynamics
2) Model behaviour - effects of pertubation of the system: 
   - Treatment of cases
   - Infection and disease prophylaxis
   - Vector control effects on mosquito life and feeding cycle

_View project progress [here](https://github.com/numalariamodeling/model-characterization/issues#workspaces/emodopenmalaria-643ac4533584b28586ce8b39/roadmap)._

## Simulation framework

Conceptually:
![Schematic of simulation analysis worklfow](https://github.com/numalariamodeling/model-characterization/blob/main/static/flowchart.png)

Implementation in this repository:
![Simulation framework](https://github.com/numalariamodeling/model-characterization/blob/main/static/emod-om-framework.png)


_Table: Main scripts and functions_

| launch_test.py*                                | helper.py                  |
|------------------------------------------------|----------------------------|
| [ parameter definitions ]                      | parse_args                 |
| update_param_default  (emod)                   | make_dirs                  |
| update_param_climate  (emod)                   | get_time_param             |
| set_param_fn   (emod)                          | save_exp_scen              |
| build_campaign   (emod)                        | get_seasonal_eir           |
| update_campaign_multiple_parameters_ser (emod) | create_scenarios_csv       |
| update_campaign_multiple_parameters  (emod)    | as_list                    |
| update_eir_scale   (emod)                      | shell_header_quest         |
| sweep_burnin_simulations  (emod)               | write_txt                  |
| submit_create_run_EMOD  (emod)                 | submit_analyze_OpenMalaria |
|                                                | submit_analyze_EMOD        |
|                                                | submit_run_pyscript        |
|                                                | emodpy_module              |
|                                                | OM_module                  |
|                                                | combine_emodom_results     |
|                                                | str_to_digit               |
|                                                | pretty_legend              |
* ) this file includes building the "json scaffold" for EMOD, and for each new simulation experiment a new launch.py should be created.

_Table: EMOD functions_   

| EMOD/utils.py                  | EMOD/scaffolds               | EMOD/analyze_sim.py   |
|--------------------------------|------------------------------|-----------------------|
| set_param                      | forcedEIR                    | InsetChartAnalyzer    |
| build_demog                    | interventions/treatment_camp | BenchmarkAnalyzer     |
| build_standard_campaign_object | ...                          | MonthlyAgebinAnalyzer |
| add_monthly_reports            |                              | AnnualAgebinAnalyzer  |
| add_annual_reports             |                              | TransmissionReport    |
| _get_serialized_filenames      |                              |                       |
| _get_core_counts               |                              |                       |
| get_workdir_from_simulations   |                              |                       |
| create_sim_directory_map       |                              |                       |
| build_burnin_df                |                              |                       |

 
_Table: OpenMalaria functions_   

| OpenMalaria/utils.py   | OpenMalaria/scaffolds | OpenMalaria/analyze_sim.py |
|------------------------|-----------------------|----------------------------|
| create_scenarios_OM    | R0000GA.xml           | to_df                      |
| submit_run_OpenMalaria | ...                   | format_df                  |
|                        |                       | add_measure_names          |
|                        |                       | pivot_wider                |
|                        |                       | InputEIRAnalyzer           |
|                        |                       | BaseAnalyzer               |
|                        |                       | BenchmarkAnalyzer          |
|                        |                       | MonthlyAgebinAnalyzer      |
|                        |                       | AnnualAgebinAnalyzer       |


## Running a simulation
- In terminal navigate to repository  `cd ~/model-characterization`
- Run python script that defines the simulation `python launch_test.py`
- Check simulations via `squeue -u <username>`
- Wait for simulations to finish and process results as necessary for project
- If you need to resubmit the `analyze_sim.py` script, it can be found in `experiments/<suite>/<exp_name>`

### Troubleshooting
- No results in simulation outputs
  - did the analyzer run, try rerunning?
  - simulation failed? check log/error files
- ...

## Installation


[EMODpy installation IDM](https://docs.idmod.org/projects/emodpy/en/v1.19.0/installation.html).
[EMODpy installation additions NU for NUCLUSTER](https://numalariamodeling.github.io/FE-2023-quarto-website/guides/install_guide.html).

[OpenMalaria installation STPH](https://github.com/SwissTPH/openmalaria/wiki/UserGuide#Installing-OpenMalaria) 

<details><summary><span>OpenMalaria venv on NUCLUSTER</span></summary>
<p>

NU IT research (Scott Coughlin) built a container and sent instructions which have been edited for completeness and are shown below:
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

Because calling containers is very annoying, Scott also added a module file in this folder which wraps the call to openMalaria to make it easier to use. 
Please see this example below which can be run in `/projects/b1139/OpenMalaria/`
```
cd OpenMalaria
module use /projects/b1139/OpenMalaria/modules/
module load openmalaria
openMalaria -s example_scenario.xml
```


</p>
</details>


### GitHUb repositories
EMOD, IDM  
- [idmtools](https://github.com/InstituteforDiseaseModeling/idmtools)  
- [emodpy-malaria](https://github.com/InstituteforDiseaseModeling/emodpy-malaria)  
- emod-api  
- emodpy   

OpenMalaria
- [openmalaria](https://github.com/SwissTPH/openmalaria/) 
- ([r-openMalariaUtilities](https://github.com/SwissTPH/r-openMalariaUtilities)) 



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
| Documentation     | https://docs.idmod.org/projects/emod-malaria/en/latest/index.html                       | https://github.com/SwissTPH/openmalaria/wiki                                                                       |
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

