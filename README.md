

# Multi-Malaria-Modeling Python Framework (MultiMalModPy)
_A novel programmatic framework for running three individual-based malaria transmission models (EMOD, malariasimulation, OpenMalaria)._

[![EMOD](https://img.shields.io/badge/EMOD-v2.24-1A9E77?style=flat-square)](https://github.com/EMOD-Hub/EMOD)
[![OpenMalaria](https://img.shields.io/badge/OpenMalaria-v46-D76227?style=flat-square)](https://github.com/SwissTPH/openmalaria/releases/tag/schema-46.0)
[![malariasimulation](https://img.shields.io/badge/malariasimulation-v2.2.0-7672B2?style=flat-square)](https://github.com/mrc-ide/malariasimulation/releases/tag/v2.2.0)
[![Python Version](https://img.shields.io/badge/python-3.9.4-blue?style=flat-square)](https://www.python.org/downloads/release/python-394/) 
[![R Version](https://img.shields.io/badge/R->=4.0.0-blue?style=flat-square)](https://cran.r-project.org/) 

[Documentation](https://ahadi-analytics.github.io/MultiMalModPy/) | [Project overview](https://www.appliedhealthanalytics.org/analytic/comparative-analysis-of-mathematical-models) | [Releases](https://github.com/ahadi-analytics/MultiMalModPy/releases)

### Motivation and use  
Mathematical models are increasingly used to inform malaria decision-making, but independently developed models can differ in their structure, assumptions, inputs, and outputs.   
Understanding when models produce similar or different results and the underlying reason requires systematic comparison under harmonized conditions.  

MultiMalModPy provides a common programmatic framework to:

1) run EMOD, OpenMalaria, and malariasimulation individually or in combination under harmonized conditions;  
2) compare model inputs, outputs, baseline behaviour, and responses to changes in transmission; and  
3) support interpretation of similarities and differences between models.  

MultiMalModPy is being developed by AHADI and partners from the respective modelling teams.   
More information is available on the [project page](https://www.appliedhealthanalytics.org/analytic/comparative-analysis-of-mathematical-models).   

### Malaria models 

- **EMOD** (Epidemiological MODeling software) is developed by the [Institute for Disease Modeling (IDM)](https://www.idmod.org/), also used by  [AHADI](https://www.appliedhealthanalytics.org/analytic/comparative-analysis-of-mathematical-models) and by the [Malaria Modeling Group at Northwestern University](https://www.numalariamodeling.org/).  

- **malariasimulation** is developed and maintained by the [malaria modelling group at Imperial College London](https://www.imperial.ac.uk/malaria-modelling/).  

- **OpenMalaria** is developed and maintained by the [Global Disease Modelling team](https://www.thekids.org.au/our-research/early-environment/infection-and-vaccines/global-disease-modelling/) at [The Kids Research Institute Australia](https://www.thekids.org.au/), the Disease Modelling Unit at the [Swiss Tropical and Public Health Institute (Swiss TPH)](https://www.swisstph.ch/en/about/eph/disease-modelling/), and [sciCORE](https://scicore.unibas.ch/) at the University of Basel.  


### Development and issues  

The repository remains under active development. For reproducible analyses, use a tagged release rather than the current development version.  
If something is not working as expected, please [create an issue on GitHub](https://github.com/ahadi-analytics/MultiMalModPy/issues).  

