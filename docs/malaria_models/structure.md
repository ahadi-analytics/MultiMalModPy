
# Malaria model structure 


<div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; border-left: 5px solid #FFB6C1;">
    <span style="font-weight: bold;">❗</span> Please refer to each model's source documentation. The information provided here is subject to change and may not reflect the latest updates of each model.
</div>


<br>

**EMOD**: EMOD incorporates age-dependent transmission risk, the development of partial immunity due to cumulative exposure, and maternal antibody protection.   
The malaria model structure for EMOD is detailed in the [malaria-model-overview](https://docs.idmod.org/projects/emod-malaria/en/2.20_a/malaria-model-overview.html) and related publications.    

**malariasimulation**: The model structure for malariasimulation is outlined in the [model structure](https://mrc-ide.github.io/malariasimulation/articles/Model.html) and related publications.    

**OpenMalaria**: The model structure for OpenMalaria can be found in the [openmalaria/wiki](https://github.com/SwissTPH/openmalaria/wiki) and related publications.  


## Model components configured in MultiMalModPy    

The sections below outline key components of the simulation framework. 
They provide relevant details to guide users but are not presented in a strict order or consistent level of detail.  


### Time
 
 **Model-specific timesteps**    
- **EMOD**:
  - 1 day timestep
- **malariasimulation**: 
   -  1 day timestep
- **OpenMalaria**: 
   - 5 day timestep  


### Population and age demography       

- **EMOD**:  [Population dynamics](https://docs.idmod.org/projects/emod-malaria/en/latest/parameter-configuration-population.html?highlight=birth)
- **malariasimulation**: [ModelDemography]() 
- **OpenMalaria**:  [Demography](https://github.com/SwissTPH/openmalaria/wiki/ModelDemography)



### Transmission intensity     

The models handle transmission intensity primarily in two ways:  
- Forced EIR: The EIR is explicitly set and remains constant.  
- Dynamic EIR: The EIR emerges from mosquito population dynamics and host-vector interactions.  

- **EMOD**:
  - forced transmission model, using EIR as input
  - dynamic transmission model, using Larval Habitat Availability as input 
- **malariasimulation**: 
   -  dynamic transmission model, using EIR together with monthly rainfall (see [seasonality](../guide/seasonality.md)) as input  
- **OpenMalaria**: 
  - forced transmission model, using EIR as input
  - dynamic transmission model, using EIR as input
