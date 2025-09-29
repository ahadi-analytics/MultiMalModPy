# Model parameters  

This page provides a high-level summary of the simulation parameters types, format and definition used across the three models.   

<div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; border-left: 5px solid #FFB6C1;">  
    <span style="font-weight: bold;">❗</span> Please refer to each model's source documentation. The information provided here is indicative only and may not reflect the latest updates of each model.
</div>   

 <br> 

- **EMOD** includes a large and detailed set of parameters that control vector biology, host immunity, climate effects, 
and simulation configuration. These parameters are mostly configured via JSON or campaign scripts.   
- **malariasimulation** parameters are implemented in R and used to define host immunity, infection progression, and clinical outcomes. 
Emphasis is placed on age-structured immunity and probabilistic outcomes.  
- **OpenMalaria** parameters are implemented in XML.    


## EMOD  

Example parameter names obtained from [config.json](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/inputs/config.json).    
 
| Category                          | Description                                                                          | Example <br/> Parameters                                                                   |
|----------------------------------|--------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Climate & <br/>Environmental          | Governs temperature, rainfall,<br/> humidity, and seasonality effects                    | `Air_Temperature_Offset`  <br/>`Base_Rainfall` <br/> `Climate_Model`                       |
| Vector <br/>Biology                   | Controls larval habitat, vector aging, <br/>migration, and mortality                     | `Enable_Vector_Aging`  <br/>`Vector_Sampling_Type`  <br/>`Egg_Hatch_Density_Dependence`    |
| Host <br/>Immunity                    | Models maternal antibodies, immunity <br/>acquisition, and decay                         | `Enable_Maternal_Protection`  <br/>`Antibody_Memory_Level` <br/> `Antibody_CSP_Decay_Days` |
| Infection <br/>Dynamics               | Defines parameters for parasitemia, <br/>detectability, and transmission                 | `Fever_Severe_Threshold` <br/> `Antigen_Switch_Rate` <br/> `Simulated EIR`                 |
| Mortality & <br/>Health Outcomes      | Parameters influencing severe <br/>disease and mortality                                 | `Fever_Mortality_Threshold` <br/> `Anemia_Mortality_Threshold`                             |
| Simulation <br/>Configuration         | Core runtime and structural settings                                                | `Simulation_Timestep` <br/> `Start_Time` <br/> `Serialized_Population_Writing_Type`        |
| Reporting                        | Enables or disables built-in <br/>reporters and custom reports                           | `Enable_Default_Reporting` <br/> `Custom_Reports_Filename`                                 |
| Demographics & <br/>Population        | Includes aging, birth/death <br/>processes, and risk profiles                            | `Enable_Birth` <br/> `Demographics_Filenames`  <br/>`x_Base_Population`                    |



## malariasimulation  

Example parameter names obtained from [get_parameters](https://mrc-ide.github.io/malariasimulation/reference/get_parameters.html) function to view defined parameters in the model.  
Note list not exhaustive, and indicative only.    
 

| Category                                | Description                                                | Example <br/>Parameters               |
|----------------------------------------|------------------------------------------------------------|---------------------------------------|
| Fixed State <br/>Transitions                | Time lags between disease states                           | `du`                                  |
| Immunity Boost <br/>Grace Periods           | Time windows where immunity <br/>cannot be boosted again   | `ub`  <br/>`uc` <br/> `ud` <br/> `uv` |
| Immunity Decay <br/>Rates                   | Decay of maternal or acquired immunity                     | `rm` <br/> `rvm`                      |
| Detection Probability <br/>Modifiers        | How age and immunity influence <br/> detectability of infection | `ad` <br/> `d1` <br/> `gammad`        |
| Infectivity Towards<br/>Mosquitoes         | Transmission potential depending <br/>on disease status         | `cd`  <br/>`cu` <br/> `gamma1`        |
| Probability of <br/>Clinical/Severe Disease | Likelihood of clinical/severe <br/>cases given immunity and age | `ic0`  <br/>`phi0` <br/> `theta0`     |
| Pre-erythrocytic <br/>Infection Probabilities | Probability of initial <br/>infection post bite                 | `b0` <br/> `ib0`  <br/>`kb`           |
| Mortality <br/>Parameters                   | Influence of immunity on <br/>disease-related mortality         | `pcm`  <br/>`pvm`                     |


## OpenMalaria  

Example parameter names and definitions obtained from  OpenMalaria's [XML base file]().  
Note table not exhaustive, and indicative only, a full table has been published in [Reiker et al 2021](https://www.nature.com/articles/s41467-021-27486-z).   

| Category                                | Description                                                                             | Example <br/>Parameters                                                                |
|----------------------------------------|-----------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------|
| Infection Success &<br/> Inoculation        | Defines probabilities of <br/>successful infection based on exposure                        | `'-ln(1-Sinf)'`  <br/>`Estar` <br/> `Xstar_p`                                          |
| Host Variability & <br/>Immunity Dynamics   | Describes host heterogeneity <br/>and maternal/immune decay                                 | `sigma2i`  <br/>`decay_m`  <br/>`alpha`                                                |
| Cumulative Exposure <br/>Thresholds         | Thresholds for developing immunity<br/> or changing infection risk                           | `CumulativeYstar`  <br/>`CumulativeHstar`                                              |
| Density Bias & <br/>Detection               | Adjusts parasitemia thresholds <br/>and density measurements                                 | `Density bias` <br/> `Ystar1`  <br/>`Idete multiplier`                                 |
| Mortality <br/>Risk Factors                 | Factors influencing case fatality<br/>and indirect mortality from comorbidities            | `log oddsr CF community`  <br/>`Indirect risk cofactor`  <br/> `comorbidity intercept` |
| Parasite Density & <br/>Immune Response     | Models the parasite dynamics <br/>and immune clearance rates                                 | `Ystar half life` <br/> `Immune effector decay` <br/> `Asexual immunity decay`         |

