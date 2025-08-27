# Model parameters

This page provides a high-level summary of the simulation parameters types, format and definition used across the three models.

<div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; border-left: 5px solid #FFB6C1;">
    <span style="font-weight: bold;">❗</span> Please refer to each model's source documentation. The information provided here is indicative only and may not reflect the latest updates of each model.
</div>

**EMOD**: EMOD includes a large and detailed set of parameters that control vector biology, host immunity, climate effects,
and simulation configuration. These parameters are mostly configured via JSON or campaign scripts.  

**malariasimulation**: malariasimulation parameters are implemented in R and used to define host immunity, infection progression, and clinical outcomes. 
Emphasis is placed on age-structured immunity and probabilistic outcomes.   

**OpenMalaria**: OpenMalaria parameters are implemented in XML. 


## EMOD

Example parameter names obtained from [config.json]().
 
| Category                          | Description                                                                          | Example Parameters                                                                 |
|----------------------------------|--------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| Climate & Environmental          | Governs temperature, rainfall, humidity, and seasonality effects                    | `Air_Temperature_Offset`, `Base_Rainfall`, `Climate_Model`                        |
| Vector Biology                   | Controls larval habitat, vector aging, migration, and mortality                     | `Enable_Vector_Aging`, `Vector_Sampling_Type`, `Egg_Hatch_Density_Dependence`    |
| Host Immunity                    | Models maternal antibodies, immunity acquisition, and decay                         | `Enable_Maternal_Protection`, `Antibody_Memory_Level`, `Antibody_CSP_Decay_Days` |
| Infection Dynamics               | Defines parameters for parasitemia, detectability, and transmission                 | `Fever_Severe_Threshold`, `Antigen_Switch_Rate`, `Simulated EIR`                 |
| Mortality & Health Outcomes      | Parameters influencing severe disease and mortality                                 | `Fever_Mortality_Threshold`, `Anemia_Mortality_Threshold`                         |
| Simulation Configuration         | Core runtime and structural settings                                                | `Simulation_Timestep`, `Start_Time`, `Serialized_Population_Writing_Type`         |
| Reporting                        | Enables or disables built-in reporters and custom reports                           | `Enable_Default_Reporting`, `Custom_Reports_Filename`                             |
| Demographics & Population        | Includes aging, birth/death processes, and risk profiles                            | `Enable_Birth`, `Demographics_Filenames`, `x_Base_Population`                     |



## malariasimulation

Example parameter names obtained from [get_parameters](https://mrc-ide.github.io/malariasimulation/reference/get_parameters.html) function to view defined parameters in the model.
Note list not exhaustive, and indicative only.  
 

| Category                                | Description                                                                   | Example Parameters     |
|----------------------------------------|-------------------------------------------------------------------------------|------------------------|
| Fixed State Transitions                | Time lags between disease states                                              | `du`                  |
| Immunity Boost Grace Periods           | Time windows where immunity cannot be boosted again                          | `ub`, `uc`, `ud`, `uv`|
| Immunity Decay Rates                   | Decay of maternal or acquired immunity                                        | `rm`, `rvm`           |
| Detection Probability Modifiers        | How age and immunity influence detectability of infection                     | `ad`, `d1`, `gammad`  |
| Infectivity Towards Mosquitoes         | Transmission potential depending on disease status                            | `cd`, `cu`, `gamma1`  |
| Probability of Clinical/Severe Disease | Likelihood of clinical/severe cases given immunity and age                    | `ic0`, `phi0`, `theta0` |
| Pre-erythrocytic Infection Probabilities | Probability of initial infection post bite                                   | `b0`, `ib0`, `kb`     |
| Mortality Parameters                   | Influence of immunity on disease-related mortality                            | `pcm`, `pvm`          |


## OpenMalaria

Example parameter names and definitions obtained from  OpenMalaria's [XML base file]().
Note table not exhaustive, and indicative only, a full table has been published in [Reiker et al 2021](https://www.nature.com/articles/s41467-021-27486-z)

| Category                                | Description                                                                             | Example Parameters                    |
|----------------------------------------|-----------------------------------------------------------------------------------------|---------------------------------------|
| Infection Success & Inoculation        | Defines probabilities of successful infection based on exposure                        | `'-ln(1-Sinf)'`, `Estar`, `Xstar_p`   |
| Host Variability & Immunity Dynamics   | Describes host heterogeneity and maternal/immune decay                                 | `sigma2i`, `decay_m`, `alpha`         |
| Cumulative Exposure Thresholds         | Thresholds for developing immunity or changing infection risk                           | `CumulativeYstar`, `CumulativeHstar`  |
| Density Bias & Detection               | Adjusts parasitemia thresholds and density measurements                                 | `Density bias`, `Ystar1`, `Idete multiplier` |
| Mortality Risk Factors                 | Factors influencing case fatality and indirect mortality from comorbidities            | `log oddsr CF community`, `Indirect risk cofactor`, `comorbidity intercept` |
| Parasite Density & Immune Response     | Models the parasite dynamics and immune clearance rates                                 | `Ystar half life`, `Immune effector decay`, `Asexual immunity decay` |

