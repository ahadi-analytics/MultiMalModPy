# Overview of MultiMalModPy

MultiMalModPy includes  model-agnostic (global) and model-specific Python scripts. 
The global scripts define parameters and manage the simulation, while the model-specific scripts handle sub-processes 
such as input generation, output processing, and model features. 
All parameters from the global scripts are written into a serializable `exp` object used by each model during 
pre- and post-processing. 

![folder structure](../img/MultiMalModPy_framework_for_web.png)

**1. Setup and launch** requires user input of the parameters for the simulation to run (setup_sim.py). 
Simulations are submitted via launch_sim .py and all defining parameters are stored  in a seralized python object (exp.obj),
used throughout the proce ss.  
Shell job submission scripts are created to automatically run subsequent scripts.

**2. Simulations run** automatically after model-specific utiliy functions created scenarios for each model.
Simulations run independently per model and generate raw outputs. Simulation running time varies from model to model.

**3. Postprocessing** is initiated  once simulations finish. 
The model-specific raw outputs and outcome measures are aggregated over time and by age and formatted.

**4. Visualization of outputs** starts automatically after the analyzer.
The standardized CSV files per model are used to generatea set of pre-defined figures.  Figures included are:
relationship between outcomes, time-series and agecurves. 
The figures can be modified and extended by the user. 


## Repository structure

**Back-end:**  
Subdirectories for each model contain model-specific functions to handle the input and output processing for each
model.   
To add new functionolaity or custom simulation setups, the **functions** and **interventions.py** under each model
directory as well as the **experiments.py** will need to be edited.

**Front-end:**  
User-facing script are directly under the root directory, and include three scripts:
`manifest.py`, `setup_sim.py`, and `launch_sim.py`.


<span style="font-size: 18px;">📦<strong>MultiMalModPy</strong></span>  
┣ <span style="font-size: 16px;">📂<strong>EMOD</strong></span>  
┃ ┗ 📂**functions**    
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_calib_params.py_     
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_interventions.py_      
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_EMOD_functions.py_      
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_forced_EIR.py_   
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_reporters.py_      
┃ ┗ 📂**inputs**     
┃ &nbsp;&nbsp;&nbsp; ┗ 📂**weather**     
┃ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ┗ 📜perennial_rainfall_daily.bin.json      
┃ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; ┗ 📜...     
┃ ┗ 📜analyze_sim.py    
┃ ┗ 📜utils.py  
┣ <span style="font-size: 16px;">📂<strong>malariasimulation</strong></span>    
┃ ┗ 📂**functions**     
┃ &nbsp;&nbsp;&nbsp; ┗📜_get_seasonality_parameters.R_  
┃ &nbsp;&nbsp;&nbsp; ┗📜_interventions.R_  
┃ &nbsp;&nbsp;&nbsp; ┗📜_run_simulations.R_  
┃ ┗ 📜_malariasimulation.R_  
┃ ┗ 📜_analyze_sim.py_    
┃ ┗ 📜_utils.py_  
┣ <span style="font-size: 16px;">📂<strong>OpenMalaria</strong></span>  
┃ ┗ 📂**functions**   
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_interventions.py_     
┃ ┗ 📂**scaffolds**     
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_R0000GA.xml_  
┃ ┗ 📂**snippets**     
┃ &nbsp;&nbsp;&nbsp; ┗ 📜_demographics.xml_     
┃ ┗ 📜_analyze_sim.py_    
┃ ┗ 📜_utils.py_   
┣ 📜_manifest.py_   
┣ 📜_setup_sim.py_   
┗ 📜_launch_sim.py_

## Inputs, simulation and output directories

![folder structure](../img/folder_structure.png)


