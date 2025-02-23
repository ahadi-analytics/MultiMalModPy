# Glossary and abbreviations


Terms marked with '📌' are newly introduced terms specific to **MultiMalModPy** or one of the models included.    
 
 
<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">A</span>  


<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">B</span>  

- 📌 **Burn-in**: A time period used to warm up the model, reaching equilibrium or initializing population immunity or the vector model. 
Outputs are typically not monitored during this phase, and handling varies across models.
 
<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">C</span>  

- 📌 **CC-step - Carrying capacity step change**:    
a theoretical "Carrying capacity step change"  

-  **CM - Case management**: Generally defines the effective treatment of uncomplicated (sometimes also referred to clinical) and severe malaria cases. 
The specific definition of how cases and clearance of parasites following treatment varies across models. 
CM is part of the pre-aligned options in MultiMalModPy and details can be found under [interventions/CM](../malaria_models/interventions.md#case-management).   

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">D</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">E</span>  

- 📌 **EMOD**: Epidemiological Modeling Software. One of the three individual based malaria models included in MultiMalModPy.    

- 📌  **Entomological mode**: Specifies the vector model to use, determining whether the simulation employs forced or dynamic 
<span title="A measure of the number of infectious mosquito bites received by an individual in a specific area over a given period" style="color: #007BFF; text-decoration: underline; cursor: pointer;">EIR (Entomological Inoculation Rate)</span>.

 
- 📌 **exp**: A serializable Python object that can be saved and loaded using the [pickle](https://docs.python.org/3/library/pickle.html) module.
It functions similarly to a YAML or config file but encapsulates all simulation and framework configurations necessary for running the process.

- 📌 **experiment ID**:  A unique identifier assigned to each simulation in EMOD.


<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">F</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">G</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">H</span>  

-  **HPC - High-performance-computing**.


<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">I</span>  

- 📌  **interpolation_data.csv**: A CSV file that contains simulation outputs for each model across various transmission levels,
used to align transmission intensity between the three models. 
The model-specific CSV files are stored in the `target_calibration` folder within the MultiMalModPy repository.


-  **ITN - Insecticide treated nets**: A vector control intervention that aims to protect the human host from the bites of female _Anopheles_ that are seeking a blood meal during the night.
The insecticide inside the net fabric also affects the mosquitoes in several ways. This intervention is not yet part of the pre-aligned options in MultiMalModPy.

- **IRS - Indoor residual spraying**:  A vector control intervention that targets female _Anopheles_ while resting on indoor walls of houses or huts. 
This intervention is not yet part of the pre-aligned options in MultiMalModPy.  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">J</span>  

- 📌 **job_directory**: The directory where raw simulation input/output files are stored, along with shell scripts that can be used to re-run any step of the simulation process.  
The `job_directory` is defined by the user in the `manifest.py`.


<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">K</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">L</span>  

- **LSM - Larval source management, including larviciding**:  This intervention is not yet part of the pre-aligned options in MultiMalModPy, but available for the individual models. 
However, a variant of the larviciding parameterization to control vectorial capacity was used to define a theoretical "Carrying capacity step change" (see CC-step).  


<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">M</span>  

- 📌 **malariasimulation**: One of the three individual based malaria models included in MultiMalModPy.  

- 📌  **manifest**: The Python script where user-specific configurations, such as paths and installed software versions, are defined (term adopted from IDMTools).

- **MDA - Mass drug administration**: This intervention is not part of the pre-aligned options in MultiMalModPy, but available for the individual models.    

- 📌 **Monitoring period**: Time period of the simulation during which transmission dynamics and disease states are tracked and recorded in the output.

- 📌 **MultiMalModPy**: Multi-Malaria-Modeling Framework  


<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">N</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">O</span>  

- 📌 **output_directory**: The directory where standardized simulation output files are stored, as well as result figures (plots).  
The `output_directory` is defined by the user in the `manifest.py`.

- 📌 **OpenMalaria**: One of the three individual based malaria models included in MultiMalModPy.  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">P</span>  

- **Pickup**: The simulation "picks up" from a previously saved state, referred to as serialization,
which captures the system's state after the burn-in period. This allows the simulation to continue from that point without 
needing to repeat the burn-in. The state is saved in the form of serialized files that can be used in subsequent runs.
Simulation outcomes are typically monitored from this phase onward.

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">Q</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">R</span>  

- **RCD - Reactive case detection**:  This intervention is not part of the pre-aligned options in MultiMalModPy, but available for the individual models.  


<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">S</span>  

- 📌 **scen_df / scenario csv**:  A CSV file containing all unique parameter combinations for a simulation scenario. Generated in `launch_sim.py`.

- 📌  **serialization**: Saves the population state at a specific time, allowing simulations to start from that point instead of re-running the burn-in period.

-  **Slurm**: formerly known as Simple Linux Utility for Resource Management is an open-source job scheduler for HPCs.  


- 📌 **Sweeps**: The sweep defines all combinations of parameter values to simulate every possible scenario.

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">T</span>  

- 📌 **Target output name** and **Target output value**: Refer to the outcome metrics used to adjust and set the transmission intensity in the simulation.

- **Transmission intensity**: Malaria transmission intensity can be expressed by entomological inoculation rate or a temporal larval habitat multiplier (EMOD only).

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">U</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">V</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">W</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">X</span>  

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">Y</span>

<span style="color:#1E5D7B; font-size: 1.1em; font-weight: bold;">Z</span>  









