# Default parameters

This page is under construction.

_Depending on latest stable calibration used._

## EMOD

_config.json_

| Parameter                                                  | Estimate                                            |
|------------------------------------------------------------|-----------------------------------------------------|
| Age_Dependent_Biting_Risk_Type                             | SURFACE_AREA_DEPENDENT                              |
| Age_Initialization_Distribution_Type                       | DISTRIBUTION_COMPLEX                                |
| Air_Temperature_Filename                                   | climate/seasonal_air_temperature_daily.bin          |
| Air_Temperature_Offset                                     | 0                                                   |
| Anemia_Mortality_Inverse_Width                             | 1                                                   |
| Anemia_Mortality_Threshold                                 | 0.654726663                                         |
| Anemia_Severe_Inverse_Width                                | 10                                                  |
| Anemia_Severe_Threshold                                    | 4.50775825                                          |
| Antibody_CSP_Decay_Days                                    | 90                                                  |
| Antibody_CSP_Killing_Inverse_Width                         | 1.5                                                 |
| Antibody_CSP_Killing_Threshold                             | 20                                                  |
| Antibody_Capacity_Growth_Rate                              | 0.09                                                |
| Antibody_IRBC_Kill_Rate                                    | 1.596                                               |
| Antibody_Memory_Level                                      | 0.34                                                |
| Antibody_Stimulation_C50                                   | 30                                                  |
| Antigen_Switch_Rate                                        | 7.65E-10                                            |
| Base_Air_Temperature                                       | 27                                                  |
| Base_Gametocyte_Fraction_Male                              | 0.2                                                 |
| Base_Gametocyte_Mosquito_Survival_Rate                     | 0.002011099                                         |
| Base_Gametocyte_Production_Rate                            | 0.06150582                                          |
| Base_Land_Temperature                                      | 27                                                  |
| Base_Rainfall                                              | 10                                                  |
| Base_Relative_Humidity                                     | 0.75                                                |
| Base_Sporozoite_Survival_Fraction                          | 0.25                                                |
| Birth_Rate_Dependence                                      | POPULATION_DEP_RATE                                 |
| Birth_Rate_Time_Dependence                                 | NONE                                                |
| Campaign_Filename                                          | campaign.json                                       |
| Climate_Model                                              | CLIMATE_BY_DATA                                     |
| Climate_Update_Resolution                                  | CLIMATE_UPDATE_DAY                                  |
| Clinical_Fever_Threshold_High                              | 1.5                                                 |
| Clinical_Fever_Threshold_Low                               | 0.5                                                 |
| Config_Name                                                |                                                     |
| Custom_Coordinator_Events                                  | []                                                  |
| Custom_Individual_Events                                   | ['Received_Treatment', 'Received_Severe_Treatment'] |
| Custom_Node_Events                                         | []                                                  |
| Custom_Reports_Filename                                    | custom_reports.json                                 |
| Cytokine_Gametocyte_Inactivation                           | 0.01667                                             |
| Death_Rate_Dependence                                      | NONDISEASE_MORTALITY_BY_AGE_AND_GENDER              |
| Demographics_Filenames                                     | ['demographics.json']                               |
| Egg_Hatch_Delay_Distribution                               | NO_DELAY                                            |
| Egg_Hatch_Density_Dependence                               | NO_DENSITY_DEPENDENCE                               |
| Egg_Saturation_At_Oviposition                              | SATURATION_AT_OVIPOSITION                           |
| Enable_Aging                                               | 1                                                   |
| Enable_Birth                                               | 1                                                   |
| Enable_Climate_Stochasticity                               | 0                                                   |
| Enable_Default_Reporting                                   | 1                                                   |
| Enable_Demographics_Birth                                  | 0                                                   |
| Enable_Demographics_Builtin                                | 0                                                   |
| Enable_Demographics_Reporting                              | 0                                                   |
| Enable_Demographics_Risk                                   | 1                                                   |
| Enable_Disease_Mortality                                   | 0                                                   |
| Enable_Drought_Egg_Hatch_Delay                             | 0                                                   |
| Enable_Egg_Mortality                                       | 0                                                   |
| Enable_Infectivity_Reservoir                               | 0                                                   |
| Enable_Initial_Prevalence                                  | 1                                                   |
| Enable_Interventions                                       | 1                                                   |
| Enable_Maternal_Antibodies_Transmission                    | 1                                                   |
| Enable_Maternal_Infection_Transmission                     | 0                                                   |
| Enable_Maternal_Protection                                 | 0                                                   |
| Enable_Natural_Mortality                                   | 1                                                   |
| Enable_Property_Output                                     | 0                                                   |
| Enable_Skipping                                            | 0                                                   |
| Enable_Spatial_Output                                      | 0                                                   |
| Enable_Superinfection                                      | 1                                                   |
| Enable_Susceptibility_Scaling                              | 0                                                   |
| Enable_Temperature_Dependent_Egg_Hatching                  | 0                                                   |
| Enable_Termination_On_Zero_Total_Infectivity               | 0                                                   |
| Enable_Vector_Aging                                        | 0                                                   |
| Enable_Vector_Migration                                    | 1                                                   |
| Enable_Vector_Migration_Local                              | 0                                                   |
| Enable_Vector_Migration_Regional                           | 0                                                   |
| Enable_Vector_Mortality                                    | 1                                                   |
| Enable_Vector_Species_Report                               | 0                                                   |
| Enable_Vital_Dynamics                                      | 1                                                   |
| Erythropoiesis_Anemia_Effect                               | 3.5                                                 |
| Falciparum_MSP_Variants                                    | 32                                                  |
| Falciparum_Nonspecific_Types                               | 76                                                  |
| Falciparum_PfEMP1_Variants                                 | 1070                                                |
| Fever_IRBC_Kill_Rate                                       | 1.4                                                 |
| Fever_Mortality_Inverse_Width                              | 1895.519716                                         |
| Fever_Mortality_Threshold                                  | 3.400500856                                         |
| Fever_Severe_Inverse_Width                                 | 27.56535804                                         |
| Fever_Severe_Threshold                                     | 3.983542997                                         |
| Gametocyte_Stage_Survival_Rate                             | 0.588569307                                         |
| Human_Feeding_Mortality                                    | 0.1                                                 |
| Incubation_Period_Constant                                 | 7                                                   |
| Incubation_Period_Distribution                             | CONSTANT_DISTRIBUTION                               |
| Individual_Sampling_Type                                   | TRACK_ALL                                           |
| Infection_Updates_Per_Timestep                             | 8                                                   |
| Infectious_Period_Exponential                              | 6                                                   |
| Infectious_Period_Gaussian_Mean                            | 6                                                   |
| Infectious_Period_Gaussian_Std_Dev                         | 1                                                   |
| Infectious_Period_Kappa                                    | 1                                                   |
| Infectious_Period_Lambda                                   | 1                                                   |
| Infectious_Period_Log_Normal_Mu                            | 6                                                   |
| Infectious_Period_Log_Normal_Sigma                         | 1                                                   |
| Infectious_Period_Max                                      | 1                                                   |
| Infectious_Period_Mean_1                                   | 1                                                   |
| Infectious_Period_Mean_2                                   | 1                                                   |
| Infectious_Period_Min                                      | 0                                                   |
| Infectious_Period_Peak_2_Value                             | 1                                                   |
| Infectious_Period_Poisson_Mean                             | 6                                                   |
| Infectious_Period_Proportion_0                             | 1                                                   |
| Infectious_Period_Proportion_1                             | 1                                                   |
| Infectivity_Scale_Type                                     | CONSTANT_INFECTIVITY                                |
| Innate_Immune_Variation_Type                               | NONE                                                |
| Insecticides                                               | []                                                  |
| Inset_Chart_Has_IP                                         | []                                                  |
| Inset_Chart_Has_Interventions                              | []                                                  |
| Inset_Chart_Include_Pregnancies                            | 0                                                   |
| Inset_Chart_Reporting_Include_30Day_Avg_Infection_Duration | 1                                                   |
| Land_Temperature_Filename                                  | climate/seasonal_air_temperature_daily.bin          |
| Land_Temperature_Offset                                    | 0                                                   |
| Larval_Density_Dependence                                  | UNIFORM_WHEN_OVERPOPULATION                         |
| Load_Balance_Filename                                      |                                                     |
| MSP1_Merozoite_Kill_Fraction                               | 0.511735322                                         |
| Malaria_Model                                              | MALARIA_MECHANISTIC_MODEL                           |
| Malaria_Strain_Model                                       | FALCIPARUM_RANDOM_STRAIN                            |
| Maternal_Antibodies_Type                                   | SIMPLE_WANING                                       |
| Maternal_Antibody_Decay_Rate                               | 0.01                                                |
| Maternal_Antibody_Protection                               | 0.1327                                              |
| Max_Individual_Infections                                  | 3                                                   |
| Max_MSP1_Antibody_Growthrate                               | 0.045                                               |
| Mean_Egg_Hatch_Delay                                       | 0                                                   |
| Mean_Sporozoites_Per_Bite                                  | 11                                                  |
| Memory_Usage_Halting_Threshold_Working_Set_MB              | 8000                                                |
| Memory_Usage_Warning_Threshold_Working_Set_MB              | 7000                                                |
| Merozoites_Per_Hepatocyte                                  | 15000                                               |
| Merozoites_Per_Schizont                                    | 16                                                  |
| Min_Adapted_Response                                       | 0.05                                                |
| Min_Days_Between_Clinical_Incidents                        | 14                                                  |
| Nonspecific_Antibody_Growth_Rate_Factor                    | 0.5                                                 |
| Nonspecific_Antigenicity_Factor                            | 0.415111634                                         |
| Number_Basestrains                                         | 1                                                   |
| Number_Of_Asexual_Cycles_Without_Gametocytes               | 1                                                   |
| Parasite_Mortality_Inverse_Width                           | 327.5159451                                         |
| Parasite_Mortality_Threshold                               | 851138.0382                                         |
| Parasite_Severe_Inverse_Width                              | 56.5754896                                          |
| Parasite_Severe_Threshold                                  | 851031.2877                                         |
| Parasite_Switch_Type                                       | RATE_PER_PARASITE_7VARS                             |
| PfHRP2_Boost_Rate                                          | 0.018                                               |
| PfHRP2_Decay_Rate                                          | 0.167                                               |
| Population_Density_Infectivity_Correction                  | CONSTANT_INFECTIVITY                                |
| Population_Scale_Type                                      | FIXED_SCALING                                       |
| Pyrogenic_Threshold                                        | 15000                                               |
| RBC_Destruction_Multiplier                                 | 3.29                                                |
| Rainfall_Filename                                          | climate/seasonal_rainfall_daily.bin                 |
| Rainfall_In_mm_To_Fill_Swamp                               | 1000                                                |
| Rainfall_Scale_Factor                                      | 1                                                   |
| Random_Number_Generator_Policy                             | ONE_PER_CORE                                        |
| Random_Number_Generator_Type                               | USE_PSEUDO_DES                                      |
| Relative_Humidity_Filename                                 | climate/seasonal_relative_humidity_daily.bin        |
| Relative_Humidity_Scale_Factor                             | 1                                                   |
| Report_Coordinator_Event_Recorder                          | 0                                                   |
| Report_Detection_Threshold_Blood_Smear_Gametocytes         | 40                                                  |
| Report_Detection_Threshold_Blood_Smear_Parasites           | 40                                                  |
| Report_Detection_Threshold_Fever                           | 1                                                   |
| Report_Detection_Threshold_PCR_Gametocytes                 | 0.05                                                |
| Report_Detection_Threshold_PCR_Parasites                   | 0.05                                                |
| Report_Detection_Threshold_PfHRP2                          | 5                                                   |
| Report_Detection_Threshold_True_Parasite_Density           | 0                                                   |
| Report_Gametocyte_Smear_Sensitivity                        | 0.1                                                 |
| Report_Node_Event_Recorder                                 | 0                                                   |
| Report_Parasite_Smear_Sensitivity                          | 0.1                                                 |
| Report_Surveillance_Event_Recorder                         | 0                                                   |
| Run_Number                                                 | 2                                                   |
| Semipermanent_Habitat_Decay_Rate                           | 0.01                                                |
| Serialized_Population_Reading_Type                         | NONE                                                |
| Serialized_Population_Writing_Type                         | NONE                                                |
| Simulation_Duration                                        | 5475                                                |
| Simulation_Timestep                                        | 1                                                   |
| Simulation_Type                                            | MALARIA_SIM                                         |
| Start_Time                                                 | 1                                                   |
| Temporary_Habitat_Decay_Factor                             | 0.05                                                |
| Vector_Larval_Rainfall_Mortality                           | NONE                                                |
| Vector_Migration_Food_Modifier                             | 0                                                   |
| Vector_Migration_Habitat_Modifier                          | 0                                                   |
| Vector_Migration_Modifier_Equation                         | LINEAR                                              |
| Vector_Migration_Stay_Put_Modifier                         | 0                                                   |
| Vector_Sampling_Type                                       | VECTOR_COMPARTMENTS_NUMBER                          |
| Wolbachia_Infection_Modification                           | 1                                                   |
| Wolbachia_Mortality_Modification                           | 1                                                   |
| x_Base_Population                                          | 1                                                   |
| x_Birth                                                    | 1                                                   |
| x_Other_Mortality                                          | 1                                                   |
| x_Temporary_Larval_Habitat                                 | 1.3484                                              |
| x_Vector_Migration_Local                                   | 1                                                   |

## malariasimulation

**malariasimulation** offers a [get_parameters](https://mrc-ide.github.io/malariasimulation/reference/get_parameters.html) function to view all parameters in the model.
Default values were determined by using the median across 50 random sets of parameter draws.

| Parameter     Symbol | Parameter Type                             | Parameter Description                                        | Parameter Default | Parameter Min | Parameter Max |
|----------------------|--------------------------------------------|--------------------------------------------------------------|-------------------|---------------|---------------|
| du                   | fixed state transitions                    | the delay for humans to move from state U to S               | 110               | 69.5898       | 146.062       |
| ub                   | immunity boost grace periods               | period in  which pre-erythrocytic immunity cannot be boosted | 7.2               | 1.06229       | 25.8764       |
| uc                   | immunity boost grace periods               | period in  which clinical immunity cannot be boosted         | 6.06              | 1.48711       | 13.58         |
| ud                   | immunity boost grace periods               | period in  which immunity to detectability cannot be boosted | 9.44512           | 1.05122       | 26.5402       |
| uv                   | immunity boost grace periods               | period in  which severe immunity cannot be boosted           | 11.4321           | 0.0409431     | 117.171       |
| rm                   | immunity decay rates                       | decay rate for  maternal immunity to clinical disease        | 67.6952           | 56.0482       | 93.1118       |
| rvm                  | immunity decay rates                       | decay rate for  maternal immunity to severe disease          | 76.8365           | 37.8859       | 139.677       |
| ad                   | immunity reducing probability of detection | scale  parameter relating age to immunity                    | 7993.5            | 6554.22       | 10094.6       |
| d1                   | immunity reducing probability of detection | minimum  probability due to immunity                         | 0.160527          | 0.0540254     | 0.314522      |
| fd0                  | immunity reducing probability of detection | time-scale at   which immunity changes with age              | 0.007055          | 0.00000471    | 0.042121      |
| gammad               | immunity reducing probability of detection | shape parameter relating age to immunity                     | 4.8183            | 3.11894       | 8.16328       |
| id0                  | immunity reducing probability of detection | scale parameter                                              | 1.577533          | 0.0567825     | 15.44549      |
| kd                   | immunity reducing probability of detection | shape parameter                                              | 0.476614          | 0.190643      | 1.26744       |
| cd                   | infectivity towards mosquitoes             | infectivity of clinically diseased humans towards mosquitoes | 0.068             | 0.0262169     | 0.193139      |
| cu                   | infectivity towards mosquitoes             | infectivity of sub-patent infection                          | 0.0062            | 0.0000708     | 0.029169      |
| gamma1               | infectivity towards mosquitoes             | parameter for infectivity   of asymptomatic humans           | 1.82425           | 0.123118      | 16.5369       |
| pcm                  | mortality parameters                       | new-born  clinical immunity relative to mother's             | 0.774368          | 0.420769      | 0.998944      |
| pvm                  | mortality parameters                       | new-born  severe immunity relative to mother's               | 0.195768          | 0.0925639     | 0.855581      |
| ic0                  | probability of clinical infection          | scale  parameter                                             | 18.02366          | 10.63586      | 36.79639      |
| kc                   | probability of clinical infection          | shape  parameter                                             | 2.36949           | 1.76969       | 3.21076       |
| phi0                 | probability of clinical infection          | maximum  probability due to no immunity                      | 0.792             | 0.352825      | 0.986045      |
| phi1                 | probability of clinical infection          | maximum  reduction due to immunity                           | 0.00074           | 0.00000228    | 0.003369      |
| b0                   | probability of pre-erythrocytic infection  | maximum  probability due to no immunity                      | 0.59              | 0.349146      | 0.989847      |
| ib0                  | probability of pre-erythrocytic infection  | scale parameter                                              | 43.9              | 13.25245      | 148.795       |
| kb                   | probability of pre-erythrocytic infection  | shape parameter                                              | 2.16              | 0.908016      | 3.44781       |
| av                   | probability of severe infection            | age dependent modifier                                       | 2493.41           | 924.234       | 5067.72       |
| fv0                  | probability of severe infection            | age dependent modifier                                       | 0.141195          | 0.0043904     | 0.994957      |
| gammav               | probability of severe infection            | age dependent modifier                                       | 2.91282           | 0.272665      | 5.95187       |
| iv0                  | probability of severe infection            | scale parameter                                              | 1.09629           | 0.3073822     | 3.734202      |
| kv                   | probability of severe infection            | shape  parameter                                             | 2.00048           | 1.27469       | 3.17738       |
| theta0               | probability of severe infection            | maximum probability due to no immunity                       | 0.074989          | 0.0085529     | 0.204342      |
| theta1               | probability of severe infection            | maximum reduction due to immunity                            | 0.000119          | 0.0000077     | 0.000846      |

## OpenMalaria

Table layout adapted from supplementary file from [Reiker et al 2021](https://www.nature.com/articles/s41467-021-27486-z)

| Parameter                    | Meaning                                                                              | Unit/ dimension           | Estimate |
|------------------------------|--------------------------------------------------------------------------------------|---------------------------|----------|
| '-ln(1-Sinf)'                | Lower limit of success probability of inoculations                                   | Proportion                | 0.050736 |
| Estar                        |                                                                                      | Inoculations/personnight  | 0.03247  |
| Simm                         | Lower limit of success probability of inoculations in  immune individuals            | Proportion                | 0.092699 |
| Xstar_p                      | Critical value of cumulative number of entomologic  inoculations                     | Inoculations              | 4158.408 |
| gamma_p                      | Steepness of relationship between success of inoculation                             | Dimensionless constant    | 0.607779 |
| sigma2i                      | Variation between hosts on parasite densities (variance of log-normal distribution)  |                           | 8.731388 |
| CumulativeYstar              | Critical value  of cumulative number of parasite days                                |                           | 3.42E+09 |
| CumulativeHstar              | Critical value   of cumulative number of infections                                  | Infections                | 79.63425 |
| '-ln(1-alpha_m)'             | Maternal protection at birth                                                         | Dimensionless             | 5.459868 |
| decay_m                      | Decay of maternal protection                                                         | Per year                  | 5.273989 |
| sigma2_0                     | Fixed variance component for densities                                               |                           | 0.963133 |
| Xstar_v                      | Critical value of cumulative number of infections for variance in parasite densities | Infections                | 0.889578 |
| Ystar2                       |                                                                                      | Parasites/microliter      | 26.2003  |
| alpha                        | Factor determining increase in                                                       |                           | 147000.4 |
| Density bias (non Garki)     | Density bias (non Garki)                                                             | Dimensionless             | 0.177379 |
| sigma2                       | Mass action parameter                                                                | Dimensionless             | 0.05     |
| log oddsr CF community       | Case fatality for severe episodes in the community compared to hospital              | Log odds                  | 1.86078  |
| Indirect risk cofactor       | Co-morbidity intercept relevant to indirect mortality                                | Proportion                | 0.004234 |
| Non-malaria infant mortality | Non-malaria intercept for infant mortality                                           | Deaths / 1000 live births | 61.75034 |
| Density bias  (Garki)        | Density bias (Garki)                                                                 | Dimensionless             | 4.796108 |
| Severe Malaria Threshhold    | Parasitaemia threshold for severe episodes type Y/                                   |                           | 14753690 |
| Immunity Penalty             | Immune penalty                                                                       |                           | 1        |
| Immune effector decay        | Immune effector decay                                                                |                           | 0        |
| comorbidity intercept        | Prevalence of comorbidity/susceptibility at birth relevant to severe episodes        | proportion                | 0.006827 |
| Ystar half life              |                                                                                      | Years                     | 1.383771 |
| Ystar1                       |                                                                                      |                           | 1177.043 |
| Asexual immunity decay       |                                                                                      |                           | 0        |
| Ystar0                       |                                                                                      |                           | 68.86192 |
| Idete multiplier             |                                                                                      | Dimensionless             | 2.797524 |
| critical age for comorbidity |                                                                                      | Years                     | 0.152848 |

