
# Updating Malaria Models in MultiMalModPy  


This guide describes how to update **EMOD**, **malariasimulation**, and **OpenMalaria** versions in MultiMalModPy, including dependency handling, configuration updates, and validation steps.

> ⚠️ If you’re updating any model version, you must also review the changes in `manifest.py`, containers (Docker/Singularity), and the documentation.

--- 

## General Update Workflow

1. Update or install the **new version** of the model or its dependencies.
2. Adjust `manifest.py` to reflect new supported version ranges or paths.
3. Rebuild containers if used (Docker/Singularity).
4. Validate backward compatibility with existing configurations.
5. Update the **Simulation Guide** and **Changelog**.

---


## EMOD   

EMOD is installed via `pip` from [IDM’s private PyPI](https://packages.idmod.org), and optionally uses a pre-built `.sif` image for HPC execution.  


Follow the [Installation Guide](../getting_started/installation.md#emod) and run:

   ``` 
   pip install emodpy-malaria==<new_version> --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
   pip install idmtools[slurm] --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
   ``` 

**Test using:**   
```
python launch_sim.py --models EMOD --test  
```

**Document Changes**
Update Simulation Guide sections related to EMOD behavior, parameter sets, or performance changes.
 
---

## malariasimulation    

- Update R version if required   
- Update versions in  `dependencies/install_packages.R`
- Update R package: via 
  - `source("dependencies/install_packages.R")`
  -  remotes::install_github("mrc-ide/malariasimulation")
- Update manifest.py with supported versions and `R_PATH`  
 

**Test using:**   
```
python launch_sim.py --models malariasimulation --test  
```



---

## OpenMalaria

- Follow the [installation instructions](../getting_started/installation.md#openmalaria) , and place files under: `dependencies/OpenMalaria/om_v<NEW_VERSION>`  
- If on HPC (NUCLUSTER), edit  `modules/openmalaria/<version>.lua.`  
- Update manifest.py  
  - OPENMALARIA_PATH = "/gpfs/projects/.../om_v46"  
  - OPENMALARIA_SUPPORTED_VERSIONS = ["v43", "v46"]  # Add latest version  
  
**Test using:**   
```
python launch_sim.py --models OpenMalaria --test  
```

---

 