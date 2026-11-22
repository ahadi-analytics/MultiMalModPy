
# Malaria model structure 


<div style="background-color: #f4f4f4; padding: 10px; border-radius: 5px; border-left: 5px solid #FFB6C1;">
    <span style="font-weight: bold;">❗</span> Please refer to each model's source documentation. The information provided here is subject to change and may not reflect the latest updates of each model.
</div>


<br>

**EMOD**: EMOD incorporates age-dependent transmission risk, the development of partial immunity due to cumulative exposure, and maternal antibody protection.   
The malaria model structure for EMOD is detailed in the [malaria-model-overview](https://emod.idmod.org/emodpy-malaria/emod/malaria-model-overview/) and related publications.    

**malariasimulation**: The model structure for malariasimulation is outlined in the [model structure](https://mrc-ide.github.io/malariasimulation/articles/Model.html) and related publications.    

**OpenMalaria**: The model structure for OpenMalaria can be found in the [openmalaria/wiki](https://github.com/OpenMalaria-Org/openmalaria/wiki) and related publications.  


## Model components configured in MultiMalModPy    


### Time
 
**Model-specific timesteps**    

- **EMOD**: 1 day timestep  
- **malariasimulation**: 1 day timestep   
- **OpenMalaria**:  5 day timestep     
 
**Model-specific monitoring surveys**    

- **EMOD**: flexible, multiple options per simulation  (i.e. 5 days and 30 days, and 365 days)
- **malariasimulation**: 1 day timestep   
- **OpenMalaria**:  flexible, single option per simulation  (i.e. 5 days or 30 days)



### Population and age demography       

- **EMOD**:  [Population dynamics](https://emod.idmod.org/emodpy-malaria/emod/parameter-configuration-population/)   
- **malariasimulation**: [ModelDemography]()    
- **OpenMalaria**:  [Demography](https://github.com/OpenMalaria-Org/openmalaria/wiki/ModelDemography)   


### Transmission dynamics     

**EMOD** 

- 'dynamic' transmission, using [Larval Habitat](https://emod.idmod.org/emodpy-malaria/emod/vector-model-larval-habitat/) and [climate](https://emod.idmod.org/emodpy-malaria/emod/vector-model-climate-demographics/) as inputs.        
- 'forced' transmission, using [InputEIR](https://emod.idmod.org/emodpy-malaria/emod/parameter-campaign-node-inputeir/). 

**malariasimulation** 

- 'dynamic' transmission, using EIR together with monthly rainfall (see [seasonality](../guide/seasonality.md)) as input.    

**OpenMalaria** 

- 'dynamic' and 'forced' transmission [ModelTransmission](https://github.com/OpenMalaria-Org/openmalaria/wiki/ModelTransmission).  


