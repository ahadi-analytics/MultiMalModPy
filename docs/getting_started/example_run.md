# Example run 


This example guides you through running simulations, assuming all requirements are met — meaning the 
necessary software is installed and user settings are properly configured in manifest.py.  
You can visit the [installation ](../getting_started/installation.md) or the [first-time-configuration](../getting_started/configuration.md) pages if you need to modify your setup.

## HPC  

**Step 1: Navigate to the Repository and Activate the Virtual Environment**

**1a) Navigate to the Repository**
Open a terminal on your cluster and move into the MultiMalModPy repository using:
``` 
cd <your_path>/MultiMalModPy  
```
Replace <your_path> with the actual path where the repository is located.

**1b) Activate the Virtual Environment**  
To ensure dependencies are properly managed, activate the virtual environment:
``` 
source <your_path>/my_venv//bin/activate  
```  
If you haven’t set up the virtual environment yet, follow the installation instructions [here](../getting_started/installation.md).  

**Step 2: Configure Simulation to run (Optional for First Test Run)**
If you want to customize your simulation settings, the easiest way is to modify the `setup_sim.py` file and adjust the parameters as needed.
However, if this is your first test run, you can skip this step and proceed with the default settings.
Later, you’ll also learn how to run multiple simulations simultaneously using configurations from a CSV file. 

**Step 3: Launch simulations**
 3a) To launch a simulation, use the following command:  
``` 
python launch_sim.py --models EMOD malariasimulation OpenMalaria --test
```  
You can choose to run all three models (EMOD, malariasimulation, and OpenMalaria) or specify only one or two by modifying the command accordingly.  
Check you simulations via `squeue -u <username>`. 

While simulations are running, check the `experiments` and the `simulation_outputs` folder of your current simulation running.
In the `experiments` folder, you will find log files for each step and model, as well as the input files used for the simulationper model.
In the `simulation_outputs` folder, you can review the scenarios that were submitted in `scen_df.csv`, and  the outputs appear in the folder once the simulation finishes.    


3b) Postprocessing (optional if manual re-run is required)
Since the postprocessing runs automatically once the simulation job finishes, there is  no extra step required to process simulation outputs.  
In case of futher content-debugging or custmization needs, you can go to `Customize and troubleshoot analyzer` section.  

**Step 4: View output**  
The figures will appear under  `simulation_outputs` .

<div style="background-color: #E9F2F9; padding: 15px; border-left: 5px solid #00796b; margin: 20px 0; font-family: Arial, sans-serif;"> <strong><em>DONE!</em></strong>  
  If you see the CSV files and generated figures, congratulations—you've successfully run your first MultiMalModPy test simulation! 🎉  
 </div> 

<div style="background-color: #E9F2F9; padding: 15px; border-left: 5px solid #00796b; margin: 20px 0; font-family: Arial, sans-serif;"> <strong><em>📝 NOTE!</em></strong>  
  If the files are missing, check the log files for error messages and verify whether any raw simulation outputs were generated.  
  To debug or rerun specific steps, use the saved .sh files to execute each step separately and identify the issue.      <strong>malariasimulation</strong> and <strong>OpenMalaria</strong>. 
</div> 

---------------------- 


## Local  

### From batch  

Open a CLI terminal (i.e. CMD, Pycharm, or RStudio terminal). In the example shown, a Pycharm terminal is used.  
And type in terminal the following command for a local test run.  

```   
python .\launch_sim.py --models malariasimulation OpenMalaria --test   
```  

**Pycharm**  
![launch_sim.py](../img/run_from_pycharm.png)      


The resulting terminal output looks as below, after which two pop up windows appear:


<a href="https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/launch_sim.py" target="_blank">   
![launch_sim.py](../img/launch_sim.py)  
</a>  

OpenMalaria 

<a href="https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/run_OpenMalaria_local.png" target="_blank"> 
![OpenMalaria PSI](../img/run_OpenMalaria_local.png)  
</a>


malariasimulation


<a href="https://github.com/ahadi-analytics/MultiMalModPy/tree/main/docs/img/run_malariasimulation_local.png" target="_blank">  
![malariasimulation PSI](../img/run_malariasimulation_local.png)  
</a>

### Local, interactive run 



## Simulation directories

**Experiments**  

`simulations_local/experiments/20250202_TEST/sims_dynamic_perennial__19_33_36`

**Simulation outputs**
`simulations_local/simulation_outputs/20250202_TEST/sims_dynamic_perennial__19_33_36`



# Example outputs  

![Example outputs](../img/example_output_csv.png)  

For details, see [Input and output files](../malaria_models/input_output.md)
