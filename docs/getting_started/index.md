# Overview


The framework is designed to allow running either one or all three of the models and the objective of this article is to present the programmatic setup with exemplary inputs and outputs not meant for model comparison. The framework takes user input to generate experimental scenarios and produces daily, monthly, and yearly outcome measures. The framework also enables the comparative evaluation of baseline model behavior. 

## Setup  
MultiMalModPy includes three types setup parameters for the user to specify:  

_Malaria Setup_  
This section requires users to align malaria-related input parameters across all models to ensure that the simulations are comparable. It involves setting up the key parameters that influence how the malaria environment is represented in the simulations.  

_Simulation Setup_  
The users define the specifics of each new "experiment," including the scenarios to be tested. The simulation/experiment parameters include the population, number of seeds, simulation duration and ‘burnin’ duration, age groups to monitor, and reporting interval for writing out outcome metrics. Scenario-defining parameters are those that can take in multiple values and determine transmission, seasonality, case management and potentially other interventions or parameter explorations.     

Framework Setup   
In this section, users configure overarching parameters, such as selecting which models to run and specifying the outputs to be generated. The setup includes the installation and definition of directories to be used for the simulations to store input and output files. Additionally, cluster specific parameters are required to ensure a smooth processing of the simulations throughout the implemented pipeline.  



