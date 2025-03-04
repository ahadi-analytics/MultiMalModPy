
# Dependencies


## Container

### Use container

#### Local


To view any images existing in docker.desktop  
```
docker images
```

View all runs:  
```
docker ps -a 
```

```
docker run -it mmmpy_local:rocky8 /bin/bash

```


To list any content:   

```
ls
cd opt/envs
ls

/opt/envs/mmmpy_local/bin/
```

Run MultiMalModPy from inside the container


```
docker run -it -v C:/Users/mrung/gitrepos:/mnt/c/Users/mrung/gitrepos mmmpy_local:rocky8 /bin/bash -c "source /opt/envs/mmmpy_local/bin/activate && cd /mnt/c/Users/mrung/gitrepos/model-characterization && python launch_sim.py --models OpenMalaria --test"  

```

Run plotter  
```
docker run -it -v C:/Users/mrung/gitrepos:/mnt/c/Users/mrung/gitrepos mmmpy_local:rocky8 /bin/bash -c "source /opt/envs/mmmpy_local/bin/activate && cd /mnt/c/Users/mrung/gitrepos/model-characterization && python -m plotter.plot_timeseries -d /mnt/c/Users/mrung/gitrepos/simulations_local/simulation_outputs/sbc538/20241213_test/sims_entomologymode_seasonality_intervention_10_16_59 --modelname OpenMalaria"

```




### Re-build container 

In case of new versions for one of the three models, the container will need to be updated.

####  Rename a docker image, optional if the same tag should be kept
1. Tag the existing image with a new name (e.g., mmmpy_local_old):

```
docker tag mmmpy_local:rocky8 mmmpy_local_old:rocky8
```

2. Remove the original tag
```
docker rmi mmmpy_local:rocky8
```

#### Update Docker image file

Steps: 
- Modify the `Dockerfile.rocky8` as needed, i.e. by updating the version to install
- Download and install Docker from https://app.docker.com/  (requires to create an account)
- Navigate to `MultiMalModPy/dependencies`, assuming you are already at the repository root:
    ```
    cd dependencies
    ```
- In terminal run (including the dot):
    ```
    docker build -f Dockerfile.rocky8 -t mmmpy_local:rocky8 .
    ```
  This takes around 60 minutes.
- View all docker images to verify its completion
    ```
    docker images
    ```
- **Optional**, save docker file to specific location (note it is already existing on your local machine)
  This is only required when the container should be moved to another machine.
  Also this step takes quite long for an image of size ~3.7GB.
    ```
    docker save -o emod_rocky8.tar emod:rocky8
    ```
    
#### HPC (singularity)   

Steps:  
- Modify the `Singularity.recipe` as needed, i.e. by updating the version to install
- Log into Quest and load the singularity modules
    ```
    module load singularity
    ```
- Authenticate against the remote builder. Will request that you create a token and copy the token in order to authenticate.
  - Create an account and generate access token under  https://cloud.sylabs.io/auth/tokens   
  - Then run in terminal:
      ```
      singularity remote login
      ```
    
- Build the container using the remote builder
    ```
    singularity build --remote emod-with-om-46-R-4.4.1.sif Singularity.recipe
    ```

### Understanding where things are in the container  


- **OpenMalaria**: The container currently only has v46.0 and it lives in the container here:
    ```
    /openmalaria-schema-46.0/build
    ```

  - Any future Open Malaria XX.X would live in the container here:  

      ```
      /openmalaria-schema-XX.X/build
      ```

- **EMOD**: The `mmmpy` virtual environment lives here:  
    ```
    /opt/envs/mmmpy
    ```

- **malariasimulation**: The R executable, required for malariasimulation, can be found here  
    ```
    /opt/R/4.4.1/bin/R
    ```
  
### Invoking the container (developer mode)


- Set things in manifest.py  
    ```
    OPENMALARIA_venv = f'\n\nexport PATH=/openmalaria-schema-46.0/build/:$PATH\n'
    EMOD_venv = f'source /opt/envs/emodpy_om/bin/activate'
    ```

-  Run `launch_sim_test.py` with the container
    Note the `<YOUR DIRECTORY>` at the end of the line. Replace this with the location of the image.
    ```
    module purge
    module load singularity
    singularity exec -B /etc/passwd -B /etc/slurm -B `which sbatch ` -B `which srun ` -B `which sacct ` -B `which scontrol ` -B `which salloc ` -B `which scancel ` -B `which squeue ` -B /usr/lib64/slurm/ -B /usr/lib64/liblua-5.1.so -B /usr/lib64/liblua-5.1.so:/usr/lib64/liblua.so -B /usr/lib64/libjson-c.so.2 -B /usr/lib64/libjson-c.so.2.0.1 -B /usr/lib64/libmunge.so.2 -B /usr/lib64/libmunge.so.2.0.0 -B /usr/lib64/libpmi2.so -B /usr/lib64/libpmi2.so.0 -B /usr/lib64/libpmi2.so.0.0.0 -B /usr/lib64/libpmi.so -B /usr/lib64/libpmi.so.0 -B /usr/lib64/libpmi.so.0.0.0 -B /usr/local/pmix -B /usr/local/hwloc -B /usr/local/ucx-1.13.0 -B /usr/local/ucx-1.10.0 -B /usr/local/ucx-1.8.1 -B /usr/local/spack -B /usr/local/spack_v20d1 -B /usr/local/libevent/ -B /run -B /projects -B /scratch --writable-tmpfs /<YOUR DIRECTORY>/emod-with-om-46-R-4.4.1.sif /opt/envs/emodpy_om/bin/python3 launch_sim.py --models EMOD -- test
    ```

_These instructions were provided by Northwestern Research IT and the format adapted for the online documentation._





