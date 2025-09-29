# Release Notes   


<div style="margin: 20px 0;">
  <a href="https://github.com/ahadi-analytics/MultiMalModPy" style="display: inline-block; margin-right: 15px;">
    <button class="btn btn-primary btn-lg" type="button">
      GitHub Repository
      <img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" 
           alt="GitHub Logo" 
           style="width: 20px; height: 20px; vertical-align: middle; margin-left: 8px;">
    </button>
  </a>
</div>
 
---



## Stable Releases

### 1.0.0 (Expected Q4 2025)    

**Initial full release** of MultiMalModPy.  

---

## Pre-Releases  

### 0.12.0-dev.1 (4 Jul 2025) 

- Added support for running **EMOD** locally via `idmtools` container 
- Updated seasonal interpolation datasets across models  
- Improved plot layout customization and formatting  
- Fixed bugs in analyzers, plotter, and **EMOD** serialization  
- Refined local and containerized run modes  
- Enhanced documentation and install scripts  
- General framework cleanup     

### 0.11.0-dev.1  (9 Apr 2025)  

- Refactored internal structure and cleaned up `manifest.py`  
- Improved plotter behavior and output handling for better customization and clarity  
- Fixed bugs related to `cc_step`, interpolation, **EMOD** outputs, and local execution  
- Enhanced support for containerized runs (e.g., Singularity on HPC)  
- Updated seasonal and calibration datasets for **OpenMalaria** and **malariasimulation**  
- Streamlined run argument parsing and added shell script support  
- Improved logging, parameter validation, and handling of `runmode` logic  
- Updated documentation, added online doc files, and renamed project structure  

### 0.10.0-dev.1  (8 Jan 2025)  

- Enabled simple `local launch` for test runs with **malariasimulation** and **OpenMalaria**   
- Improved support for CSV-based runs and expanded run_mode logic     
- Introduced separate `run_mode=test` option and refined argument parsing    
- Added climate and population size checks to ensure valid **EMOD** runs  
- Enhanced plotter functionality with better handling of age groups, sweep order, and sample plots  
- Cleaned up and reorganized figures, adding support for custom outputs  
- Applied multiple bugfixes across interpolation, experiment setup, and analyzers

  
### 0.9.0-dev.1  (2 Jan 2025)  

- Alignment improvements and bugfixes across model-characterization branches  
- Improved seasonality handling and interpolation stability  
- Framework restructuring and repository cleanup  
- Added `setup_sim.py` and restored key configuration files  
- Fixed **EMOD** population sizing and pfpr issues  
- Reintroduced and updated function docstrings  
- Enabled module loading with added `__init__.py` files  
- Applied automatic code formatting and restored missing documentation  

### 0.8.0-dev.1  (12 Nov 2024)  

- Other bugfixes and improvements 
  - **EMOD** multi-habitat  
  - age demography and age group aggregation  
  
### 0.7.0-dev.1  (25 Oct 2024)


- Updated and aligned age demographics 
- removed dependency between cm_clinical and cm_severe 
- Other bugfixes and improvements 
  - allow to run multiple seasonality patterns in same simulation
  - fixed burnin issue 
  - updated **EMOD** multiple calibration parameter setup 
  - removed config_exp.py 

### 0.6.0-dev.1  (9 Sep 2024)  

- Framework restructuring 
  - intriduced  `utility`, `plotter` folders
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

- Improved integration of **malariasimulation** to 'MultiMalModPy'
- CC step initial setup
- Bugfixes and improvements 
- Alignment of analyzers
- Unified use of `exp` object
- Added ValueErrors and Warnings to helper.py
- EMOD step (burnin, pickup) automatized setup

### 0.2.0-dev.1  (26 Sep 2023)  

- Initial integration of **malariasimulation** 
- Bugfixes and improvements 
- **EMOD** step (burnin, pickup) initial setup

### 0.1.0-dev.1  (22 May 2023)  

- Initial upload **EMOD** and **OpenMalaria** 'emodom' framework

---



