# Parameters and model alignment


MultiMalModPy includes three types setup parameters for the user to specify:  

_Malaria_  
Define and align malaria-related input parameters across all models to ensure that the simulations are comparable. It involves setting up the key parameters that influence how the malaria environment is represented in the simulations.  

_Simulation_  
Define the specifics of each new "experiment," including the scenarios to be tested. The simulation/experiment parameters include the population, number of seeds, simulation duration and ‘burnin’ duration, age groups to monitor, and reporting interval for writing out outcome metrics. Scenario-defining parameters are those that can take in multiple values and determine transmission, seasonality, case management and potentially other interventions or parameter explorations.     

_Framework_     
Configure overarching parameters, such as selecting which models to run and specifying the outputs to be generated. The setup includes the installation and definition of directories to be used for the simulations to store input and output files. Additionally, cluster specific parameters are required to ensure a smooth processing of the simulations throughout the implemented pipeline.  


<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>NOTE:</em></strong> 
   Not all parameters can be aligned, even though those parameters shared are likely aligned.
   A detailed checklist of how the models were aligned will be made available soon.   
</div>  




-------------------------------- 


## Simulation parameters


#### Simulation time

#### Population size

#### Age 

#### Demography 

#### Output monitoring 




-------------------------------- 

## Malaria parameters

### Seasonality 

### Case management  

### Importation 

### Entomology mode 


-------------------------------- 


## Framework parameters
