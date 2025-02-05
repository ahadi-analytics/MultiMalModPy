# MultiMalModPy


![Python Version](https://img.shields.io/badge/python-3.9-blue?style=flat-square) 
![R Version](https://img.shields.io/badge/R-4.2-blue?style=flat-square) 
![Docs](https://img.shields.io/badge/docs-MkDocs-brightgreen?style=flat-square) 
![License](https://img.shields.io/badge/license-Apache%202.0-orange?style=flat-square) 
![EMOD](https://img.shields.io/badge/EMOD-v2.20-1A9E77?style=flat-square)
![OpenMalaria](https://img.shields.io/badge/OpenMalaria-v46-D76227?style=flat-square)
![malariasimulation](https://img.shields.io/badge/malariasimulation-v1.60-7672B2?style=flat-square)
<!--- DOI -->  


_**Multi** **Mal**aria **Mod**eling **Py**thon Framework_  


A novel programmatic framework for running three individual-based malaria transmission models.

--------------------------------

### Malaria models included:   

- **EMOD** (Epidemiological MODeling software) has been developed and is maintained by
the [Institute for Disease Modeling (IDM)](https://www.idmod.org/), and also used by
the [Malaria Modeling Group at Northwestern University](https://www.numalariamodeling.org/).  

-  **OpenMalaria** has been developed and is maintained by
the [Global Disease Modelling team](https://www.thekids.org.au/our-research/early-environment/infection-and-vaccines/global-disease-modelling/) of [The Kids Reseach Institute Australia](https://www.thekids.org.au/), the Disease Modelling Unit of the [Swiss Tropical and Public Health Institute (Swiss TPH)](https://www.swisstph.ch/en/about/eph/disease-modelling/) and [sciCORE](https://scicore.unibas.ch/) of the University of Basel.

-  **malariasimulation** has been developed and is maintained by
the [Imperial College London](https://www.imperial.ac.uk/malaria-modelling/).  


For more information about MultiMalModPy, please see the [documentation](https://ahadi-analytics.github.io/MultiMalModPy/).

### Motivation for using MultiMalModPy: 
To characterize and compare the simulated transmission and disease dynamics of malaria in **EMOD**, **OpenMalaria**
and *malariasimulation** using a customized python framework that facilitates alignment and comparison of inputs and
outputs. Specifically:

1) To align models for comparability of model outcomes
    - Explore and describe basic transmission and disease dynamics
2) To understand model behaviour at baseline
3) To understand model response to perturbation of the system, for instance:
    - Change in carrying capacity (`CC step`)
    - Infection clearance and short term prevention (`SMC`)
    - Treatment of cases and contribution of cases to onward transmission
    - Vector control effects on mosquito life and feeding cycle

--------------------------------

_Disclaimer: This repository is under active development, if something is not working, please contact us - or simply
create an issue on GitHub that we can follow up on._
