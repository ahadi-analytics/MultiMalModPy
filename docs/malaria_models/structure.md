
# Malaria model structure 

_Comparison and description of each models structure component and related parameters relevant._  

 **This page is under active construction ...** 

<div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; border-left: 5px solid #FFB6C1;">
    <span style="font-weight: bold;">❗Disclaimer:</span> Please refer to each model's source documentation. The information provided here is subject to change and may not reflect the latest updates of each model.
</div>


<br>


|                       | EMOD                                                                            | OpenMalaria                                                                                                                                   | malariasimulation                                                |
|-----------------------|---------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| Model type            | discrete, stochastic, individual-based model                                    | stochastic, individual-based, single location simulation model of malaria in humans linked to a deterministic models of malaria in mosquitoes | discrete, stochastic, individual-based model                     |
| Sub-models included   | Individual-based humans  Population based vectors  PkPD submodel. Spatial model | Individual-based humans Population based vectors  PkPD submodel. …                                                                            | Individual-based humans Population or individual based vector(s) |
| Interventions modeled | CM, ITN, IRS, MDA, RCD, IPTi/PMC, RTS,S, Gene drive [...]                       | CM, ITN, IRS, MDA, RCD, LSM, RTS,S, [...]                                                                                                     | CM, MDA/SMC,  ITN, IRS, LSM, RTS,S, TBV                          |

Abbreviations of interventions defined in the [glossary](../getting_started/glossary.md)   

**EMOD**: EMOD incorporates age-dependent transmission risk, the development of partial immunity due to cumulative exposure, and maternal antibody protection. 
The malaria model structure for EMOD is detailed in the [malaria-model-overview](https://docs.idmod.org/projects/emod-malaria/en/2.20_a/malaria-model-overview.html) and related publications.  
**malariasimulation**: The model structure for malariasimulation is outlined in the [model structure](https://mrc-ide.github.io/malariasimulation/articles/Model.html) and related publications.  
**OpenMalaria**: The model structure for OpenMalaria can be found in the [openmalaria/wiki](https://github.com/SwissTPH/openmalaria/wiki) and related publications.

-----------------------  

## Human infection and immune system response    
For detailed documentation, [go to the Documentation and source code reference links](../malaria_models/documentation-and-sourcecode.md).

### Types of immunity modeled 
- **EMOD**:  
- **OpenMalaria**:   
- **malariasimulation**: Maternal immunity, anti-disease immunity, infection-blocking immunity, anti-parasite immunity.    

### How parasites are modeled within the human host 
- **EMOD**: In the microsolver, clinical and parasitological immunity is tracked through innate and adaptive immune responses to specific antigens. A detailed parasite count is tracked over time for each infected individual.  
- **OpenMalaria**: Base model uses 5-day time-steps. It tracks individual infections, with parasite density sampled from the Malaria Therapy dataset. Innate immunity and acquired immunity are based on cumulative parasite density and infections over the host's life. No immunity decay in the base model.  
- **malariasimulation**: Does not have an in-host model to track parasites.  

### Delay between bite and blood-stage infection 
- **EMOD**: 
- **OpenMalaria**: Latency period set to 3 days.  
- **malariasimulation**: Latency period (de) is set to 12 days.  

### Blood-stage parasite clearance maximum kill rate    
- **EMOD**: Fever_IRBC_Kill_Rate set to 1.4.  
- **OpenMalaria**:   
- **malariasimulation**:    

### Innate immunity  
- **EMOD**: Innate_Immune_Variation_Type set to PYROGENIC_THRESHOLD_VS_AGE.  
- **OpenMalaria**: Sampled from a normal distribution, with the variance as a fitted parameter.   
- **malariasimulation**: 

### Maternal antibody protection*    
- **EMOD**: Maternal_Antibodies_Type set to SIMPLE_WANING.   
- **OpenMalaria**: Base factor and decay are two fitted parameters.    
- **malariasimulation**:  

### New infections (Infection incidence)  
- **EMOD**: The number of individuals infected on a given day. Multiple infections can occur in a single individual per day. The Malaria_Model parameter controls the maximum number of new infections per person per day.  
- **OpenMalaria**:The number of human hosts with an infection (patent or not) during the reporting timestep. The number of infections is sampled from a Poisson distribution.  
- **malariasimulation**:The number of human hosts infected during the current time step (day).   

### Superinfections (Multiple infections an individual can have)  
- **EMOD**: Each infection can have its own antigenic repertoire, which may be partially overlapping.  
- **OpenMalaria**: Superinfections occur with summed parasite densities.  
- **malariasimulation**: Only one clinical case per infection is allowed. Superinfection can occur from the asymptomatic (A) and sub-patent (U) infection compartments, with the new infection taking precedence over the original infection.  

----------------------- 

##  Malaria disease progression and health system (case management)  
For detailed documentation, [go to the Documentation and source code reference links](../malaria_models/documentation-and-sourcecode.md).

 
### Clinical Cases      
- **EMOD**: A clinical case begins when fever surpasses a certain threshold, and the clinical incident continues until the fever subsides below another threshold.  
- **OpenMalaria**:   The probability of a clinical attack of malaria is related to the peripheral parasite densities via a pyrogenic threshold, which responds dynamically to the parasite load (Smith et al., 2006).  
- **malariasimulation**: On infection, individuals pass through the liver (pre-patent stage) and then either develop clinical disease (with a probability φ determined by their current level of anti-disease immunity) or develop patent (detectable under microscopy) asymptomatic infection (1−φ).  

### Pyrogenic Threshold    
- **EMOD**: Defines Innate_Immune_Variation_Type, either none, individual variation using the susceptibility distribution, or varying by age.   
- **OpenMalaria**:  For each host, the pyrogenic threshold is dynamically updated (differential equation) at each time-step based on the previous value and current total parasite density.  
- **malariasimulation**:  The infection process does not account for parasite density or the pyrogenic threshold.   

### Health System Memory    
- **EMOD**: The number of days with fever below the low threshold before a new incident can start, when fever again exceeds the high threshold. The default for Min_Days_Between_Clinical_Incidents is 14.  
- **OpenMalaria**: The duration of the period for which a recurrent bout of illness counts as the same episode is set to healthSystemMemory="32" (6 timesteps = 30 days).   
- **malariasimulation**: No parameter specified. The default ‘residency’ for clinical cases before recovering is 5 days (1/rD with rD = 0.2).  


### Clinical Disease Progression 
- **EMOD**: Fever is triggered by cytokine production through the innate immune response. A clinical case begins when fever surpasses a certain threshold, and the clinical incident continues until fever subsides below another threshold.    
- **OpenMalaria**:The pyrogenic threshold is dynamically updated every timestep based on the total parasite density in the host.    
- **malariasimulation**: The number of individuals who develop infections in a given time step is calculated from those who receive bites. The probability of developing a clinical case is determined by their maternal and acquired immunity. Individuals who do not develop clinical malaria develop asymptomatic malaria instead.    

### Severe Cases (Severe Malaria Episode) 
- **EMOD**: The probability of severe malaria depends on excessive fever, anemia, and parasite counts.  
- **OpenMalaria**:  The probability of severe episodes is based on a severe threshold (fitted parameter).  
- **malariasimulation**: Severe cases are calculated at each time step from the individuals infected in that time step. The probability of developing severe infection is determined by the individual's maternal and acquired immunity to severe infections.  

### Case Management Coverage for Clinical Cases  
- **EMOD**: A percentage of new clinical cases is cleared within a varying time period drawn from a distribution each day.  
- **OpenMalaria**:  Every time-step, there is a 5-day probability of getting treatment. By default, the infection is cleared in the same time-step, but treatment is flexible.  
- **malariasimulation**: Probability that new clinical cases receive treatment in the current timestep. The number of people who receive effective treatment is scaled by drug efficacy.  

### Case Management Coverage for Severe Cases  
- **EMOD**: A percentage of new severe cases is cleared within a varying time period drawn from a distribution each day.  
- **OpenMalaria**: Similar to clinical case management.  
- **malariasimulation**: Does not distinguish between clinical and severe cases when simulating case  management.  

### Non-malaria Fevers   
- **EMOD**: /  
- **OpenMalaria**: /  
- **malariasimulation**: /  


----------------------- 

##  Malaria diagnostics and detection thresholds

### <span title="Threatens diagnostic of RDT" style="color: #007BFF; text-decoration: underline; cursor: pointer;">HRP2 deletions</span>  
- **EMOD**: Separate outcome "PF_HRP2" Detection_Threshold is measured in picograms of HRP2 per microliter of blood.  
- **OpenMalaria**: Needs to be specified separately and will replace the current default diagnostics.  
-  **malariasimulation**: Not currently tracked.


### <span title="Density per micro liter blood (blood stage parasites)" style="color: #007BFF; text-decoration: underline; cursor: pointer;">Parasite density threshold for prevalence measures</span>  
- **EMOD**: Different outcome channels for each diagnostic method (PCR, microscopy, mRDT). Includes Report_Detection_Threshold_Blood_Smear_Parasites and Report_Detection_Threshold_Blood_Smear_Gametocytes. Default set to 40.  
- **OpenMalaria**: The selected threshold determines whether the diagnostic corresponds to microscopy or mRDT. The same or different diagnostics can be specified for case management, monitoring survey outputs, and test-and-treat interventions.  
- **malariasimulation**: Not explicitly implemented, but true prevalence is considered.  

### <span title="Proportion of population carrying malaria blood-stage parasites out of total population" style="color: #007BFF; text-decoration: underline; cursor: pointer;">True prevalence</span>  
- **EMOD**: The fraction of the population detectable by the TRUE_PARASITE_DENSITY version of MalariaDiagnostic. The detectability is controlled by the parameter Report_Detection_Threshold_True_Parasite_Density. Does not include super-infections.  
- **OpenMalaria**: The sum of all detectable infections where blood-stage parasite density is above the detection limit across all human hosts. This includes super-infections.  
- **malariasimulation**: The sum of all infections detectable by microscopy within a given age range is represented by n_detect_agelower_ageupper. True prevalence is considered.  







