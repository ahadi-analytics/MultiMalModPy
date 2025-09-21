
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


### OpenMalaria on NUCLUSTER


These instructions were adapted from the original setup notes by **Scott Coughlin**, who provided the module file and Singularity definition file. 

**Download and extract OpenMalaria i.e. v48**

```   
cd /gpfs/projects/b1139/OpenMalaria/  
wget https://github.com/SwissTPH/openmalaria/releases/download/schema-48.0/openMalaria-ubuntu-24.04.tar.gz  
tar -xvzf openMalaria-ubuntu-24.04.tar.gz  
rm openMalaria-ubuntu-24.04.tar.gz  
mv openMalaria-ubuntu-24.04 om_v48  
```  

**Copy modules and definition file from previous version**   

```   
cp -r /gpfs/projects/b1139/OpenMalaria/om_v46/modules/ /gpfs/projects/b1139/OpenMalaria/om_v48/  
cp /gpfs/projects/b1139/OpenMalaria/OpenMalaria.def /gpfs/projects/b1139/OpenMalaria/om_v48/  
```  

**Build the container on Quest using the remote Sylabs build environment**  

```  
module load singularity  
singularity remote login  
# If prompted:  
# An access token is already set for this remote. Replace it? [N/y] y   
# Generate an access token at: https://cloud.sylabs.io/auth/tokens   
# Paste it when prompted   
 
singularity build --remote OpenMalaria.sif OpenMalaria.def    
``` 

 **Update the module file**    

Example module file (`openmalaria/48.0.lua`):    

```    
help([[  
This git-repository contains source-code for OpenMalaria, a simulator program for studying malaria epidemiology and the impacts of interventions against malaria.
]]) 

local pkgName = "openmalaria"  
local version = "48.0"  

whatis("Name: " .. pkgName)  
whatis("Version: " .. version)  

depends_on("singularity") 

local bashStr = 'singularity exec -B /gpfs/projects:/gpfs/projects /gpfs/projects/b1139/OpenMalaria/om_v48/OpenMalaria.sif /openmalaria/openMalaria-48.0/openMalaria "$@"' 

set_shell_function("openMalaria", bashStr) 
``` 

  

---

 