# Characterization and comparison of EMOD, OpenMalaria, and malariasimulation

_[EMOD](https://docs.idmod.org/projects/emod-malaria/en/latest/index.html) | [OpenMalaria](https://github.com/SwissTPH/openmalaria/) | [malariasimulation](https://github.com/mrc-ide/malariasimulation/tree/master)_

_Disclaimer: This repository is under active development, if something is not working, please contact us - or simply
create an issue on GitHub that we can follow up on._

**Formal framework documentation moved to**: https://github.com/numalariamodeling/MultiMalModPy 


------------------------------------- 

## Project objectives

To characterize and compare the simulated transmission and disease dynamics of malaria in **EMOD**, **OpenMalaria**
and *malariasimulation** using a customized python framework that facilitates alignment and comparison of inputs and
outputs. Specifically:

1) To align models for comparability of model outcomes
    - Explore and describe basic transmission and disease dynamics
2) To understand model behaviour at baseline
3) To understand model response to perturbation of the system:
    - Change in carrying capacity (`CC step`)
    - Infection clearance and short term prevention (`SMC`)
    - Treatment of cases and contribution of cases to onward transmission
    - Vector control effects on mosquito life and feeding cycle

-------------------------------------


## Malaria models

**EMOD** (Epidemiological MODeling software) has been developed and is maintained by
the [Institute for Disease Modeling (IDM)](https://www.idmod.org/), and also used by
the [Malaria Modeling Group at Northwestern University](https://www.numalariamodeling.org/).

**OpenMalaria** has been developed and is maintained by
the [Swiss Tropical and Public Health Institute (Swiss TPH)](https://www.swisstph.ch/en/about/eph/disease-modelling/).

**malariasimulation** has been developed and is maintained by
the [Imperial College London](https://www.imperial.ac.uk/malaria-modelling/).


<details><summary><span>Click here to expand model view</span></summary>
<p>



Table 1: Overview of model software and infrastructure

|                   | EMOD                                                                                                   | OpenMalaria                                                                         | Malariasimulation                                                                          |
|-------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Documentation     | https://docs.idmod.org/projects/emod-malaria/en/latest/index.html                                      | https://github.com/SwissTPH/openmalaria/wiki                                        | https://github.com/mrc-ide/malariasimulation                                               |
| Accessibility     | Open source                                                                                            | Open source                                                                         | Open source (R package)                                                                    |
| Language          | C++                                                                                                    | C++                                                                                 | C++                                                                                        |
| First published   | 2013                                                                                                   | 2006-2008                                                                           |                                                                                            |
| Models            | Individual-based human model <br>Population based vector model  <br> PkPD submodel. <br> Spatial model | Individual-based human model <br>Population based vector model <br> (...) <br> <br> | Individual-based human model <br>Population based vector model <br> (...) <br> <br>        |
| Framework         | Python (emodpy, idm-tools)                                                                             | Python or R, varying by user group                                                  | R >= 4.0.0                                                                                 |                       
| OS                | Windows, Linux                                                                                         | Windows, Linux, (Mac OS)                                                            | Windows, Linux                                                                             |            
| Default timesteps | 1 day                                                                                                  | 5  day                                                                              | 1 day                                                                                      |                                                           
| Input file type   | json                                                                                                   | XML                                                                                 | R script                                                                                   |                                                       
| Output file type  | json                                                                                                   | txt                                                                                 | R script                                                                                   |                                          
| N input files     | 5+                                                                                                     | 1                                                                                   | 1                                                                                          |  
| N output files    | custom                                                                                                 | 2                                                                                   | 1                                                                                          |   
| Glossary          | https://docs.idmod.org/projects/emod-malaria/en/latest/glossary.html                                   | https://github.com/SwissTPH/openmalaria/wiki/Terminology                            | `help(malariasimulation)`, https://mrc-ide.github.io/malariasimulation/articles/Model.html |  



</p>
</details>

-------------------------------------

## Installation

On the NU cluster `Quest` **EMOD**, **OpenMalaria** and **malariasimulation** are already installed and accessible for
all users in group.
On the STPH cluster `SciCore` **EMOD**, **OpenMalaria** and **malariasimulation** are already installed and accessible
for all users in group.
_Note:  **malariasimulation** requires installing an R package to the user specific or group specific R library used._

**If you need to install, below are the installation instructions:**

Weblinks:

- [EMODpy installation](https://docs.idmod.org/projects/emodpy/en/v1.19.0/installation.html).
- [OpenMalaria installation](https://github.com/SwissTPH/openmalaria/wiki/UserGuide#Installing-OpenMalaria)
- [malariasimulation installation](https://github.com/numalariamodeling/model-characterization/tree/main/malariasimulation#requirements-for-running-malsim-r-scripts)

<details><summary><span>Installation on Northwestwerns University HPC cluster</span></summary>
<p>

#### EMOD

- [EMODpy installation additions NU for NUCLUSTER](https://numalariamodeling.github.io/FE-2023-quarto-website/guides/install_guide.html).

#### OpenMalaria

NU IT research (Scott Coughlin) built a container and sent instructions which have been edited for completeness and are
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
..
..

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



------------------------------------

## Troubleshooting

- No results in simulation outputs
    - analyzer did not run correctly -> try rerunning by submitting corresponding sbatch file, or copy command in
      terminal
        - slurm job id dependency not satisfied
        - error in analyzer script
    - simulation failed -> check log/error files
        - simulations cancelled due to memory or time limit issue
        - simulation had not been submitted due to errors in the input files
    - ...

------------------------------------    

## Change log
- January 2025 - Introduced setup_sim, local launch and bugfixes, updated seasonality, cleanup for public version.  
- September 2024 - Framework restructuring and preparation/cleanup for public version. The initial structure is archived in the branch [production_run_initial_structure](https://github.com/numalariamodeling/model-characterization/tree/production_run_initial_structure)
- August 2024 - Production runs, carrying capacity step with automatically defined scaling factors leveraging calibrun
- July 2024 - Input transmission paramter calibration to a defined output target for either EIR of PfPR2to10  - introduced calibrun
- March 2024 - Carrying capacity step change and additional vector outcomes, switch to OpenMalaria v46, separation of
  plotting scripts
- Jan 2024: refinement in framework to support flexible simulations, further bugfixes in model specific scripts
- Oct - Dec 2023: refinement in framework for dynamic EIR and seasonality across all three models
- Sep - Oct 2023: refinement in framework and outcome alignment for `malariasimulation` outcomes
- August 2023: start integrating Imperial College London's malaria model `malariasimulation`, start dynamic EIR
- July - August 2023: bugfixes and improvements to framework, timeseries, initial parameter exploration
- March 2023 - June 2023: initial python framework with CM only and forced EIR
- March 2023: Repository created following up on the lessons learned from the SwissTPH "MC benchmarking" framework in R

See planned next steps and issues
at:  [/model-characterization/issues](https://github.com/numalariamodeling/model-characterization/issues#workspaces/emodopenmalaria-643ac4533584b28586ce8b39/roadmap)
