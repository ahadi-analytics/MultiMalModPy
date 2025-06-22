# Installation

**MultiMalModPy** is designed to run full-scale simulations on **Linux-based high-performance clusters (HPCs)**.  
However, it also supports **local test runs** using **Docker** or, optionally, a **native Python environment**.

Use this guide to:
- Choose and set up your preferred environment  
- Download and configure the necessary container or dependencies  
- Launch a basic test simulation to verify your setup  

<div style="background-color: #E9F2F9; padding: 15px; border-left: 5px solid #00796b; margin: 20px 0; font-family: Arial, sans-serif;"> <strong><em>⚠️ NOTE:</em></strong>  
   Local setups (Docker or native Python) are **limited to test runs only** and do not support full-scale or multi-node simulations. 
</div> 



## Prerequisites


<div style="background-color: #f4f4f4; padding: 20px; border-left: 5px solid #00796b; margin: 20px 0; font-family: Arial, sans-serif; font-size: 16px; color: #333;">
  <strong><em style="font-size: 18px; color: #00796b;">Software Requirements:</em></strong>  
  <ul style="padding-left: 20px; line-height: 1.5; margin-top: 5px; margin-bottom: 0px;">
    <li>Python 3.9.4</li>
    <li>R ≥ 4.0.0</li>
    <li>EMOD:
      <ul>
        <li>emodpy==1.22.1</li>
        <li>emodpy-malaria==4.1.0</li>
        <li>idmtools-platform-slurm==2.0.2</li>
      </ul>
    </li>
    <li>malariasimulation==2.0.0</li>
    <li>OpenMalaria v46+</li>
    <li>singularity/3.8.1 <em>or</em> Docker</li>
    <li>git/2.8.2</li>
  </ul>
</div>

📦 Note: All Python dependencies are listed in `dependencies/requirements.txt`

<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>💡 TIP:</em></strong>
   Knowledge of shell, powershell, xml, json can be helpful when using MultiMalModPy.   
</div>  

<br>

---------------- 

## Clone MultiMalModPy

To get started with MultiMalModPy, the recommended approach is
to [fork](https://github.com/ahadi-analytics/MultiMalModPy/fork)  the repository and clone it to your local machine or
cluster.
Forking makes it easier to keep your version up-to-date and contribute changes back to the project.

If you simply want to run the software without modifying it,
you can also [**download the latest release**](https://github.com/ahadi-analytics/MultiMalModPy/releases) directly.


You can clone the repository (or your fork) using the terminal or Git GUI clients like GitHub Desktop or Sourcetree or other Git GUI clients:
- Navigate to the MultiMalModPy GitHub page, or your fork.
- Click the Code button.
- Copy the HTTPS or SSH URL.
- Clone via terminal: 
  - HTTPS
    ``` 
    cd <target_directory>  
    git clone https://github.com/ahadi-analytics/MultiMalModPy.git  
    ```
  - [SSH](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
  
    ``` 
    cd <target_directory>  
    git clone git@github.com:ahadi-analytics/MultiMalModPy.git
    ```
- Or use **Git GUI client’s “Clone repository” feature**.
- Paste the URL and choose your local folder to clone into.

### Update `manifest.py`  
Make sure to update the manifest.py file with the necessary configurations. For first-time setup, refer to
the  [first time configurations](../getting_started/configuration.md)

---------------- 

## Create a Virtual Environment

MultiMalModPy works best when used within a python virtual environment, as it helps manage dependencies and keep your project
isolated from other Python projects.

Follow the steps below to set up a virtual environment:

### Install Python and virtualvenv
Make sure you have Python 3.8+ installed on your system. You can verify this by running in your terminal:

```
python --version
```

If you're working on an HPC cluster, you can load the Python module available on the system
via `module load python/3.9.16` (to check existing python versions run `module spider python`)
Alternatively, if running locally, and Python isn't installed, you can download and install the latest version from
python.org.

If you don't have virtualenv installed, you can install it via pip:

```
pip install virtualenv
```

### Create the Virtual Environment 

#### Via sh/bat file
Navigate to the MultiMalModPy/dependencies folder and run 

On macOS/Linux:
```
cd dependencies
bash create_mmmpy_venv.sh
```

On Windows: 
click on `create_mmmpy_venv.bat`

#### Via terminal 
Alternatively, run each step separately via terminal

**Create the Virtual Environment**  
Navigate to the directory where you want to store your project, and then run the following command to create a virtual
environment:

```
virtualenv my_venv
```

This will create a folder named `my_venv` in your project directory that will contain the virtual environment.

**Activate the Virtual Environment**   


On Windows:  `.\my_venv\Scripts\activate`
On macOS/Linux: `source my_venv/bin/activate`

_Once activated, your terminal prompt will change to show the name of the virtual environment (e.g., (my_venv))._

<a href="https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/activated_venv_terminal.png" target="_blank">
![my_venv](../img/activated_venv_terminal.png)
</a>

<br>


**Install Dependencies**  

Now that the virtual environment is activated, install MultiMalModPy's dependencies by running:
`pip install -r dependencies/requirements.txt`

This will ensure that all required packages are installed within the virtual environment.


---------------- 

## Install Malaria Models 

### EMOD

 For system requirements on HPC using slurm, refer to the  [idmtools SLURM prerequisites](https://docs.idmod.org/projects/idmtools/en/latest/platforms/slurm/index.html#prerequisites)
 For system requirements using windowsm, refer to the [idmtools container prerequisites](https://docs.idmod.org/projects/idmtools/en/latest/platforms/container/index.html#prerequisites) 

#### Activate your Python virtual environment 

- **macOS/Linux:** 
`source my_venv/bin/activate`

- **Windows:**  
`.\my_venv\Scripts\activate`

Optional: clean previous installed packages, only needed when a new idmtools Singularity image is
available : `rm –fr ~/.local/lib/python* `


#### Pull the Singularity image (HPC only)
Download the Singularity image containing Python and MPI: 
```
curl https://packages.idmod.org:443/artifactory/idm-docker-public/idmtools/rocky_mpi/dtk_run_rocky_py39.sif -o dtk_run_rocky_py39.sif
```

#### Install emodpy-malaria

```
pip install emodpy-malaria --ignore-installed --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple 
```

You may see a warning about your pip version. This can be safely ignored but consider upgrading pip with:

<span style="color:#FFAA33">WARNING: You are using pip version 22.0.4; however, version 25.0 is available.
You should consider upgrading via the '~/my_venv/bin/python -m pip install --upgrade pip' command.</span>

#### Install `idmtools_platform_slurm` :

- **HPC**:
```
pip install idmtools[slurm] --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
```

- **Windows:**
(see [idmtools
/idmtools_platform_container](https://github.com/InstituteforDiseaseModeling/idmtools/tree/e0e045e4049d33d99c8f7fc54ba0563bd4577c9e/idmtools_platform_container#readme))
```
pip install idmtools[container] --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
```


This may take a few minutes to build.
If the 'pip install' warning appears, you can ignore it.
The outcome should look as below:

<a href="https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/install_idmtools_platform_slurm_terminal.png" target="_blank">
![my_venv](../img/install_idmtools_platform_slurm_terminal.png)
</a>

<br>

#### Verify installation

Run the following command to confirm idmtools is installed correctly:

```
idmtools --help
```

#### Update `manifest.py`  
Make sure to update the manifest.py file with the necessary configurations. For first-time setup, refer to
the  [first time configurations](../getting_started/configuration.md)


<br>

---------------- 

###  OpenMalaria


#### Install OpenMalaria by following developer's site instructions 

Installation instructions can be found on
the [OpenMalaria wiki](https://github.com/SwissTPH/openmalaria/wiki/UserGuide#Installing-OpenMalaria) .

- **HPC** (example NU cluster):

<details><summary><span>Installation instructions for the Northwestern University cluster:</span></summary>   
<p>

NU IT research built a container and sent instructions which have been edited for completeness and are
shown below:
One can build the container on Quest using the remote Sylabs build environment.

Updating to the latest OpenMalaria version:

Create a new folder for the version to install

```
mkdir /gpfs/projects/b1139/OpenMalaria/om_v46/
```

And copy into the new folder the latest schema files (not source code), available
from https://github.com/SwissTPH/openmalaria/releases.

Copy the OpenMalaria.def and modules from the prevvious release to the new one.
Note these files were created
by [Scott Coughlin](https://www.it.northwestern.edu/departments/it-services-support/research/staff/coughlin.html) to
facilitate installation on Quest, without having to use cmake.

```
cp /gpfs/projects/b1139/OpenMalaria/om_v43/OpenMalaria.def  /gpfs/projects/b1139/OpenMalaria/om_v46/OpenMalaria.def
cp -r /gpfs/projects/b1139/OpenMalaria/om_v43/modules  /gpfs/projects/b1139/OpenMalaria/om_v46/
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

local bashStr = 'singularity exec -B /projects:/projects /gpfs/projects/b1139/OpenMalaria/om_v46/OpenMalaria.sif /openmalaria/openMalaria-46.0/openMalaria "$@"'

set_shell_function("openMalaria",bashStr)
```

Then, actually install the latest OpenMalaria by generating a container following as follows:

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
cd /gpfs/projects/b1139/OpenMalaria/om_v46/
module use /gpfs/projects/b1139/OpenMalaria/om_v46/modules/
module load openmalaria
openMalaria -s example_scenario.xml
```

</p>
</details>   

<br>


- Windows (local machine):

  - Create additional subfolders for OpenMalaria version i.e. `v46` under `dependencies`**
  - Download or copy **OpenMalaria dependencies**: 
    - Visit the OpenMalaria release page and download the requred version.  
    - Alternatively, copy the files over from the installation on HPC for the respective version.
      - `autoRegressionParameters.csv`
      - `densities.csv`
      - `openMalaria.exe`
      - `scenario_46.xsd`


#### Update `manifest.py` 

Make sure to update the manifest.py file with the necessary configurations. For first-time setup, refer to
the  [first time configurations](../getting_started/configuration.md)

Define `OPENMALARIA_PATH` to point to the location of the required OpenMalaria files:


- **Linux (HPC)**: 
  - OPENMALARIA_PATH, example for NU cluster:  

  ```
  OPENMALARIA_PATH = "/gpfs/projects/b1139/OpenMalaria/om_v43/"
  ```
  
  - OPENMALARIA_venv, if using the OpenMalaria module, configure `OPENMALARIA_venv` to load the necessary environment modules
  
  ```
  OPENMALARIA_venv = f'\n\nmodule use {OPENMALARIA_PATH}/modules/ \nmodule load openmalaria\n'
  ```
  

- **Windows (local machine)**:

  - Define `OPENMALARIA_PATH` to point to the location of the required OpenMalaria files:

  ```
  OPENMALARIA_PATH = os.path.join(ROOT_DIR, 'dependencies/OpenMalaria/om_v46')
  ```
  
  `OPENMALARIA_venv` is not used when running on local machine (`OPENMALARIA_venv = ''`)


---------------- 

### malariasimulation

#### Install R or load R module

- **Linux (HPC)**: 
`module load R/>=4.4.0` (required >=4.4.0).

- **Windows (local machine)**:
  - Download and install the latest version of [R](https://www.r-project.org/) from CRAN.
  - For Windows users, also install [Rtools](https://cran.r-project.org/bin/windows/Rtools/)  from CRAN Rtools to ensure compatibility with package compilation.

#### Install R packages

Open a R console and run `source(file.path('dependencies/install_packages.R'))`
Select a CRAN mirror, and packages will be installed thereafter:  
`--- Please select a CRAN mirror for use in this session ---`

Install any additional R packages you may want to use for your project.

#### Update `manifest.py` 

- **Linux (HPC)**: 
  - No edits needed for malariasimulation when running on HPC.

- **Windows (local machine)**:
  -  Define the path to your local R installation:
  ``` 
  r_local = "C:/Program Files/R/R-4.2.3/bin"
  ``` 
  - No edits needed for `malariasimulation_input_path` which defines the location of malariasimulation

  ``` 
   malariasimulation_input_path = os.path.join(os.path.expanduser('~'), 'MultiMalModPy/malariasimulation/')
  ```

<br>

---------------- 

## Run MultiMalModPy without installing models using containers

### Using singularity container (HPC)
A singularity container allows running MultiMalModPy instantly, without the need for
installations. You can download it from [https://cloud.sylabs.io/library/rungma/multimalmodpy/mmmpy_hpc:rocky8](https://cloud.sylabs.io/library/rungma/multimalmodpy/mmmpy_hpc:rocky8) .

To pull the container run: 
```
singularity pull --arch amd64 library://rungma/multimalmodpy/mmmpy_hpc:rocky8
```

Details on how to run simulations from within a container are described in the [Example run](../getting_started/example_run.md#using-singularity-container)

### Using Docker  (local)

Navigate to dependencies and double click on `run_mmmpy_docker.bat`

??? info "Docker Manual Setup and Troubleshooting"

    #### 1️⃣ Install Docker Desktop

    Download and install from 🔗 [Docker Desktop](https://www.docker.com/products/docker-desktop/).  
    Ensure the Docker daemon is running:

    ```
    docker info
    ```

    If it's not running, open Docker Desktop (especially on Windows).

    #### 2️⃣ Pull the Docker Image

    Pull the container image from Docker Hub:

    ```
    docker pull mrm9534/mmmpy_local:rocky8
    ```

    🔗 [View image on Docker Hub](https://hub.docker.com/r/mrm9534/mmmpy_local)


    #### 3️⃣ Verify the Image

    Confirm the image exists locally:

    ```
    docker images
    ```

    Look for `mrm9534/mmmpy_local` with the tag `rocky8`.


    #### 4️⃣ Run the Docker Container

    Start the container in interactive mode:

    ```
    docker run -it --name mmmpy_container mrm9534/mmmpy_local:rocky8 /bin/bash
    ```

    To resume an existing container instead of creating a new one:

    ```
    docker ps -a               # List all containers
    docker start -ai mmmpy_container
    ```

    You should see a terminal like:

    ```
    [root@74350592befb /]#
    ```

    🛑 To exit the container, type:

    ```
    exit
    ```


    #### 5️⃣ Activate the Python Virtual Environment

    Check for available environments:

    ```
    ls /opt/envs/
    ```

    You'll likely see `mmmpy_container` or `mmmpy_local`.

    Activate the correct one:

    ```
    source /opt/envs/mmmpy_container/bin/activate
    ```

    Your prompt should look like:

    ```
    (mmmpy_container) [root@74350592befb envs]#
    ```

    Verify the Python setup:

    ```
    python --version
    pip list
    ```

    #### Run a Test Simulation (from Host System)

    If you're inside the container, `exit` first.

    Then run from your host terminal:

    ```
    docker run -it -v <USERPATH>:/mnt/c/projects \
      mrm9534/mmmpy_local:rocky8 \
      /bin/bash -c "source /opt/envs/mmmpy_container/bin/activate && cd /mnt/c/projects/MultiMalModPy && python launch_sim.py --models malariasimulation OpenMalaria --test"
    ```

    🔁 Replace `<USERPATH>` (e.g., `C:\Users\YourName\Documents`) with the full path to your MultiMalModPy folder.  

    📘 More details: [Example Run – Docker Container](../getting_started/example_run.md#using-docker-container)  

<br />

---------------- 

## Troubleshooting  

### EMOD Test Run Issues  

If your test run using EMOD fails, it may be due to missing dependencies or version conflicts. Below are common issues and how to resolve them:  

**Missing python package or version conflict**  

<span style="color:#ff3232">
ERROR: Could not find a version that satisfies the requirement click==7.1.2
ERROR: No matching distribution found for click==7.1.2
</span>

Solution:
Manually install the required version:
`pip install click==7.1.2`

If the installation of idmtools with SLURM support fails, you might see an error like this:

??? info "Show image"

    ![-idmtools_slurm_error_terminal](../img/idmtools_slurm_error_terminal.png)  
    [View image file](https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/idmtools_slurm_error_terminal.png)


Solution:
Retry the installation using:

  ```  
  pip install idmtools[slurm] --index-url=https://packages.idmod.org/api/pypi/pypi-production/simple
  ```  

**Dependency Version Conflict**  

  <span style="color:#ff3232"> ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
  This behaviour is the source of the following dependency conflicts. emodpy 1.22.1 requires click~=7.1, 
  but you have click 8.1.8 which is incompatible. </span> 
  - Run required package installation i.e.  

        pip install click==8.1.7    

  If a dependency conflict remains, let us know and try again to verify installation.

**EMOD ValueError (Likely Due to Wrong emodpy-malaria Version)**  

- EMOD ValueError: If it seems that EMOD is running, but you get a ValueError, this indicates that a wrong version of '
  emodpy-malaria' has been installed.
  Please let us know and we will update the online documentation.    
  An example is shown in the screenshot below:

??? info "Show image"

    ![-emodpy_malaria_version_error_example](../img/emodpy_malaria_version_error_example.png)  
    [View image file](https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/emodpy_malaria_version_error_example.png)

<br>




