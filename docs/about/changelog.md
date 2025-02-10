# Changelog

See planned next steps and issues
at:  [/model-characterization/issues](https://github.com/ahadi-analytics/model-characterization/issues#workspaces/emodopenmalaria-643ac4533584b28586ce8b39/roadmap)


## 1.0.0 Initial release  

Expected for Q1 2025  

------------------------------------

## Pre-releases 

### 0.11.0-dev.1  (9 Feb 2025)
- Framework cleanup
- Bugfixes and improvements 
- Restored functionality of CC step
- Calibration  update

### 0.10.0-dev.1  (8 Jan 2025)
- Framework restructuring 
  - separated run_modes and test run
  
### 0.9.0-dev.1  (4 Jan 2025)
- Alignment improvements and bugfixes 
- Improved seasonality 
- Framework restructuring  
  - added setup_sim.py 
- Local launch   

### 0.8.0-dev.1  (12 Nov 2024)
- Other bugfixes and improvements 
  - EMOD multi-habitat  
  - age demography and age group aggregation  
  
### 0.7.0-dev.1  (25 Oct 2024)
- Updated and aligned age demographics 
- removed dependency between cm_clinical and cm_severe 
- Other bugfixes and improvements 
  - allow to run multiple seasonality patterns in same simulation
  - fixed burnin issue 
  - updated EMOD multiple calibration parameter setup 
  - removed config_exp.py 

### 0.6.0-dev.1  (9 Sep 2024)
- Framework restructuring 
  - introdued `utility`, `plotter` folders
  - added config_exp.py
- Bugfixes and improvements

### 0.5.0-dev.1  (16 Aug 2024)
- Bugfixes and improvements
- Initial 'production run' for all three models

### 0.4.0-dev.1  (31 Jul 2024)
- Calibration run added to framework using simple interpolation
- Bugfixes and improvements
  - case management in malariasimulation 
  - CC step improvements
- New calibration parameters tested for specific models
- terminology alignment
  - removed remaining 'emodom' terms used

### 0.3.0-dev.1  (23 Feb 2024)
- Improved integration of malariasimulation to 'MultiMalModPy'
- CC step initial setup
- Bugfixes and improvements 
- Alignment of analyzers
- Unified use of `exp` object
- Added ValueErrors and Warnings to helper.py
- EMOD step (burnin, pickup) automatized setup

### 0.2.0-dev.1  (26 Sep 2023)
- Initial integration of malariasimulation 
- Bugfixes and improvements 
- EMOD step (burnin, pickup) initial setup

### 0.1.0-dev.1  (22 May 2023)
- Initial upload EMOD and OpenMalaria 'emodom' framework

------------------------------------
