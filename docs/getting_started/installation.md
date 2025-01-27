# Installation and requirements  


# Table of Contents
1. [Software requirements](#software_requirements)  
2. [Install and setup EMOD ](#install-and-setup-emod)  
3. [Install and setup OpenMalaria ](#install-and-setup-openmalaria)
4. [Install and setup malariasimulation](#install-and-setup-malariasimulation)  
5. [Setup when using the container ](#setup-when-using-the-container)  
6. [Activate virtual envionment ](#activate-virtual-environment)  


## Software requirements   

- MultiMalModPy 
- Python >= 4.0.0  
- R >= 4.0.0  
  - malariasimulation
  - malariaEquilibrium
  - lubridate
  - dplyr 
  - tibble 
  - readr 
  - umbrella
- EMOD
- OpenMalaria


<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>📝 NOTE:</em></strong> 
   Simulations are assumed to run on a linux based high performance cluster (HPC).
   Functionality to run locally is restricted for test runs using malariasimulation and OpenMalaria.
</div>  

<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>💡 TIP:</em></strong>
   Knowledge of shell, powershell, xml, json can be helpful when using MultiMalModPy.   
</div>  

<br>


## Install and setup EMOD  

- **EMOD**  
     - [EMODpy](https://docs.idmod.org/projects/emodpy/en/v1.19.0/installation.html)     
     - idmtools
     - emodpy-malaria    


**Helpful additional installation guides for the Northwestern University cluster:**   
-  [Faculty Enrichment Program Installation guide](https://numalariamodeling.github.io/FE-2023-quarto-website/guides/install_guide.html)
   

## Install and setup OpenMalaria  

User guide to install OpenMalaria: [OpenMalaria v46](https://github.com/SwissTPH/openmalaria/wiki/UserGuide#Installing-OpenMalaria)   

Custom installation and setup for MultiMalModPy:  
- [Install on HPC](#install-on-hpc)  
- [Installation when running locally](#installation-when-running-locally)

### Install on HPC   

<details><summary><span>Helpful additional installation guides for the Northwestern University cluster:</span></summary>   
<p>

NU IT research built a container and sent instructions which have been edited for completeness and are
shown below:
One can build the container on Quest using the remote Sylabs build environment.

Updating to the latest OpenMalaria version:

1) Create a new folder for the version to install

```
mkdir /projects/b1139/OpenMalaria/om_v46/
```

And copy into the new folder the latest schema files (not source code), available
from https://github.com/SwissTPH/openmalaria/releases.

Copy the OpenMalaria.def and modules from the prevvious release to the new one.
Note these files were created by Scott Coughlin to facilitate installation on Quest, without having to use cmake.

```
cp /projects/b1139/OpenMalaria/om_v43/OpenMalaria.def  /projects/b1139/OpenMalaria/om_v46/OpenMalaria.def
cp -r /projects/b1139/OpenMalaria/om_v43/modules  /projects/b1139/OpenMalaria/om_v46/
```

The def files includes the following lines and does not require change (for information shown below)

```
Bootstrap: docker
From: ubuntu:20.04

%post
    apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        git \
        cmake \
        libboost-dev \
        libgsl-dev \
        libxerces-c-dev \
        xsdcxx \
        zlib1g-dev \
        python3 \
        build-essential

    git config --global http.sslverify false
    git clone https://github.com/SwissTPH/openmalaria.git /openmalaria
    cd openmalaria && ./build.sh -r
```

However, the `modules/openmalaria/43.0.lua` needs to be renamed to the new version, and its content also updated to the
latest version.

```
help([[
This git-repository contains source-code for Open Malaria, a simulator program for studying malaria epidemiology and the impacts of interventions against malaria.
]])

local pkgName = "openmalaria"
local version = "46.0"

whatis("Name: " .. pkgName)
whatis("Version: " .. version)

depends_on("singularity")

local bashStr = 'singularity exec -B /projects:/projects /projects/b1139/OpenMalaria/om_v46/OpenMalaria.sif /openmalaria/openMalaria-46.0/openMalaria "$@"'

set_shell_function("openMalaria",bashStr)
```

Then, actually install the latest OpenMalaria by generating a container following as follows:

```
module load singularity
singularity remote login
```

```
module load singularity
singularity remote login
```

An access token is already set for this remote. Replace it? [N/y] y
Generate an access token at https://cloud.sylabs.io/auth/tokens, and paste it here.

```
singularity build --remote OpenMalaria.sif OpenMalaria.def
```

Because calling containers is very annoying, Scott also added a module file in this folder which wraps the call to
openMalaria to make it easier to use, which is located in the modules/openmalaria folder copied and modified in an
earlier step (lua file)

Test to run new version

```
cd /projects/b1139/OpenMalaria/om_v46/
module use /projects/b1139/OpenMalaria/om_v46/modules/
module load openmalaria
openMalaria -s example_scenario.xml
```

</p>
</details>   

<br>

### Installation when running locally  

Local run is currently only supported for 2 of the 3 models (malariasimulation and OpenMalaria).
In addition, the recommended use of running simulations locally is for testing and other `run_mode`s are disabled.

1. For each model, follow the installation guidelines under the links provided at the top of the page.
   Once installed, create a folder `dependencies` under this repository, with subfolders for each model.

2. For **OpenMalaria**, additional subfolders by version are needed i.e. `v46`, under which the downloaded files are
   located.  
   The OpenMalaria dependencies include:
    - `autoRegressionParameters.csv`
    - `densities.csv`
    - `openMalaria.exe`
    - `scenario_46.xsd`

3. Once all files are in place, update the `manifest.py` file to make the necessary path update configurations.
4. It is also recommended to add R (`Rscript`), Python (`python`) and OpenMalaria (`openMalaria`) to the environment
   variables (optional).


   

## Install and setup malariasimulation   

- **malariasimulation R packages**     

- [malariasimulation](https://github.com/mrc-ide/malariasimulation/)
   ```
     # install.packages("remotes")
     # library('remotes')
    install_github('mrc-ide/malariasimulation')
   ```

- [umbrella](https://github.com/mrc-ide/umbrella)
   ```
     # install.packages("devtools")
     # library('devtools')
     devtools::install_github("mrc-ide/umbrella")
   ```

- Other R packages:
  - lubridate
  - dplyr 
  - tibble 
  - readr 
  - umbrella



<br>


## Setup when using the container  

This section is under construction...  
A singularity container will be made available to allow running MultiMalModPy instantly, without the need for
installations. 


## Activate virtual environment 

### On Slurm, example for NU cluster
```
module purge all
module load python/3.8.4
module load singularity/3.8.1
module load git/2.8.2
module load R/4.2.3
source '/projects/b1139/environments/emodpy_bin/activate'
```

