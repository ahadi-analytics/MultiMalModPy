# How to Launch Simulations - Example run



<div style="background-color: #f4f4f4; padding: 20px; border-left: 5px solid #00796b; margin: 20px 0; font-family: Arial, sans-serif; font-size: 16px; color: #333;">
  <strong style="font-size: 18px; color: #00796b;"><em>Continue on this page if:</em></strong>
  <ul style="padding-left: 20px; line-height: 1.6; margin-top: 10px; margin-bottom: 0;">
    <li>✅ You have installed all required software
    </li>
    <li> ✅Your simulation is configured in <code>manifest.py</code>
    </li>
    <li> ✅You want to run MultiMalModPy from a container without manual installation
    </li>
    <li> If not, revisit the
    </li>
     &nbsp;➡️ <a href="../getting_started/installation.md">Installation guide</a>
     &nbsp;➡️ <a href="../getting_started/configuration.md">First-time configuration</a>
  </ul>
</div>

 
**Before you start:**    

- **Where to find simulation files**
    - Simulation files will be generated in the `experiments` and the `simulation_outputs` folder.      
    - In the `experiments` folder, you will find log files for each step and model, as well as the input files used for the simulationper model.      
    - In the `simulation_outputs` folder, you can review the scenarios that were submitted in `scen_df.csv`, and  the outputs appear in the folder once the simulation finishes.     


- **Configure simulations to run**
    - If you want to customize your simulation settings, the easiest way is to modify the [setup_sim.py](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/setup_sim.py) file and adjust the parameters as needed.   
    - However, you can skip this step and proceed with the default settings for a simple test run.   
    - You can also run multiple simulations simultaneously using configurations from a CSV file.      


------------------------------------ 

## Using Python virtual environment (HPC or local)

-  Navigate to the cloned MultiMalModPy repository and activate the virtual environment.  
If you haven’t set up the virtual environment yet, follow the installation instructions [here](../getting_started/installation.md).      


- Launch test simulations.  

  - **HPC**:

``` 
python launch_sim.py --models EMOD malariasimulation OpenMalaria --test
```  

  - **Windows**:
      - Open a command-line interface (CLI) terminal such as CMD, PyCharm terminal, or RStudio terminal.

    
??? info "Show image run_from_pycharm"

    ![-launch_sim.py](../img/run_from_pycharm.png)  


<br/>

??? info "Show image"

    ![-run_simulations.R](../img/2025-02-02 19_34_10-run_simulations.R.png)  
    [View image file](https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/2025-02-02 19_34_10-run_simulations.R.png)
 

<br/>

You can choose to run all three models (EMOD, malariasimulation, and OpenMalaria) or specify only one or two by modifying the command accordingly.


- **Monitor Simulation Progress**
  - on **HPC**:   
      - Check you simulations via `squeue -u <username>`.  
  - on Windows:  
      - EMOD: type in terminal `idmtools container status`  
      - malariasimulation and OpenMalaria: terminal windows per model appear.  


??? info "View CMD terminals"

    **OpenMalaria PSI**

    ![OpenMalaria PSI](../img/run_OpenMalaria_local.png)  
    [View image file](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/docs/img/run_OpenMalaria_local.png)

    **malariasimulation PSI**

    ![malariasimulation PSI](../img/run_malariasimulation_local.png)  
    [View image file](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/docs/img/run_malariasimulation_local.png)




------------------------------------  

## Using singularity container (HPC)

- **Navigate to the Repository**   
    Open a terminal on your cluster and move into the MultiMalModPy repository using:
    ``` 
    cd <your_path>/MultiMalModPy    
    ```
    Replace <your_path> with the actual path where the repository is located.  

- **Load singularity and ensure image file exists**
    ``` 
    module load singularity
    ```
    If you haven’t downloaded the image file yet, follow the download it from [here](../getting_started/installation.md) and save it under any directory on your HPC.     

- You can look inside the container via:    
    ```
    singularity shell /path/to/emodpy4.1-OM46-R4.4.1.sif  
    ```

- **Launch the Simulation**  
   To run the simulation, use the following command:  
    
    ```   
    cd dependencies
    dos2unix run_mmmpy_container.sh
    bash run_mmmpy_container.sh  
    ```   
 
  
You can choose to run all three models (EMOD, malariasimulation, and OpenMalaria) or specify only one or two by modifying the command accordingly.    


??? info "View terminal"

    ![hpc_container_run_terminal](../img/hpc_container_run_terminal.png)  
    [View image file](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/docs/img/hpc_container_run_terminal.png)

      
- **Monitor Simulation Progress**   
      - Check simulations via 
       ```  
       squeue -u <username>
       ```  

------------- 

<br>


## Using Docker (local)

- To run MultiMalModPy inside a Docker container, double-click on `dependencies/run_mmmpy_docker.bat`.  
- Alternatively, you can follow manual steps as below (for developer, or troubleshooting).     


??? info "Manual steps to run using docker"

     
    **Ensure the Docker image is available on your computer**   
    - If you haven’t installed it yet, refer to the [installation page](../getting_started/installation.md#local-docker-image)     
    
    **Set up your directory path:**   
    - In the example command below, replace `PATH_TO_REPO` with the directory path to your _MultiMalModPy_ folder on your computer, excluding the _MultiMalModPy_ directory itself. 
      - Example, if MultiMalModPy is in `C:/Users/<user>/Documents/MultiMalModPy`, then type  `C:/Users/<user>/Documents/`
    
    **Modify manifest.py:**     
    - Open the file and add the following line:  
        ```
        container_run = True             
        ```
    
    **Run the Docker container:**     
    - Use the following command, replacing PATH_TO_REPO with the actual path:  
     
    ```
    docker run -it -v PATH_TO_REPO:/mnt/c/projects mmmpy_local:rocky8 /bin/bash -c "source /opt/envs/mmmpy_container/bin/activate && cd /mnt/c/projects/MultiMalModPy && python launch_sim.py --models malariasimulation OpenMalaria --test"                           
    ```
    
    **What This Command Does:** 
    - Mount the local directory in which MultiMalModPy is located to /mnt/c/projects in the Docker container.  
      - Activate the Python virtual environment inside the container.  
      - Navigate to the MultiMalModPy directory inside the container and run the simulation script (`launch_sim.py`) with the specified models and test flag.  
    
    Example Terminal Output: 
    
        ```
        PS C:\Users\mrung\Documents\MultiMalModPy> docker run -it -v C:/Users/mrung/Documents/:/mnt/c/projects mmmpy_local:rocky8 /bin/bash -c "source /opt/envs/mmmpy_container/bin/activate && cd /mnt/c/projects/MultiMalModPy && python launch_sim.py --models malariasimulation OpenMalaria --test"
        
        No interventions specified
        Warning: the popsize specified for malariasimulation (1000) is not in the interpolation dataset, since running simulation as test. Using interpolation data with lowest popsize (50000)
        Warning: the popsize specified for OpenMalaria (1000) is not in the interpolation dataset, since running simulation as test. Using interpolation data with lowest popsize (50000)
        Warning: A burn-in period of at least 80 years is recommended for OpenMalaria. Currently, a shorter burn-in of 10 years has been configured, which may lead to inaccurate results.
        Warning: A population of at least 10000 is recommended for OpenMalaria. Current pop_size 1000  may lead to inaccurate results.
        Warning: A burn-in period of at least 80 years is recommended for malariasimulation. Currently, a shorter burn-in of 10 years has been configured, which may lead to inaccurate results.
         --------| Running sims_dynamic_perennial_10_28_39 for malariasimulation, OpenMalaria: 3 varying parameters: target_output_values, case_management, seasonality. Run mode:  custom |--------
        ```

   

<br>  

-------------------- 


## Postprocessing
- HPC: 
  - Since the postprocessing runs automatically once the simulation job finishes, there is  no extra step required to process simulation outputs.   

- Windows: 
  - Analyzers do run automatically.  
  - **Plotting (Manual Step)**: Unlike when running on HPC, the plotting step is not automated on local setup when not running inside a container. 
     - After the simulations (including the analyzer) have finished, navigate to the experiment folder and manually run the plotter.bat file by double-clicking it.  

In case of further content-debugging or customization needs, you can go to `Customize and troubleshoot analyzer` section.   



## Example outputs   


The output CSV files and figures will appear in the `simulation_outputs` folder.  

![Example outputs](../img/example_output_csv.png)   


## View log files    

If the files are missing, check the `log` files for error messages and verify whether any raw simulation outputs were generated.  
The log files are located in the experiment folder under 'log'.

<div style="background-color: #E9F2F9; padding: 15px; border-left: 5px solid #00796b; margin: 20px 0; font-family: Arial, sans-serif;"> <strong><em>📝 NOTE</em></strong>
  To debug or rerun specific steps, use the saved `.sh` files to execute each step separately and identify the issue.    
  <strong>malariasimulation</strong> and <strong>OpenMalaria</strong>. 
</div> 

Details on the process scripts (.sh, .err, .out etc.) are described [here]().


