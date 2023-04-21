# Characterization and comparison of EMOD and OpenMalaria

_Model features and simulated transmission and disease dynamics_

## Project goal
To have a simple framework to easily run simulations in OpenMalaria and in EMOD and compare 
projected outputs on transmission and disease metrics for user-defined scenarios (paramter selection). 


## Project tasks

1) Set up basic framework for EMOD and OpenMalaria
2) Explore and describe basic transmission and disease dynamics  
   - Severe cases and comorbidity 
   - Transmission seasonality and relationships 
   - Case managememt effects
3) Explore and describe effects of pertubation of the system
4) Explore and describe intervention impact
5) Documentation of findings and identified questions

_See tracked progress and issues on Github's [Zenhub](https://github.com/numalariamodeling/model-characterization/issues#workspaces/emodopenmalaria-643ac4533584b28586ce8b39/roadmap)_


## Repository and workflow structure  

![Schematic of simulation analysis worklfow](https://github.com/numalariamodeling/model-characterization/static/flowchart.png)



### Installation

[EMOD installation](https://docs.idmod.org/projects/emod-malaria/en/latest/install-overview.html) involves creating a
python virtual environment.
[OpenMalaria installation](https://github.com/SwissTPH/openmalaria/wiki/UserGuide#Installing-OpenMalaria) is simpler, as
it does not require any additional software to run, although additional software will be required for the simulation and
analysis workflow. 






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

