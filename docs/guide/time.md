# Time in the simulations
_Implementation in MultiMalModPy_

<div style="background-color: #f4f4f4; padding: 12px; border-left: 5px solid #FF6B8B; border-radius: 5px; margin: 10px 0;">
    <strong>🔍</strong> For a detailed overview of how each model handles time, refer to the 
    <a href="../malaria_models/structure.md#time" style="color: #0073e6; text-decoration: none;">
        Time 
    </a> description under malaria models.
</div>


In MultiMalModPy, the user can specify the following time related parameters:
- `start_year` 
- `end_year` 
- `emod_burnin`  `malariasimulation_burnin`  , `openmalaria_burnin`
- `openmalaria_survey_step` 


Example from [setup_sim.py](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/setup_sim.py#L53C14-L53C96): 

``` 
start_year = 2000
end_year = 2005
emod_burnin = 110
malariasimulation_burnin = 100
openmalaria_survey_step = '5d'
```

From those values, the burnin period is calculated automatically.  
**EMOD** allows to serialize simulations after the burnin period and before the monitoring period, as described in [model_specificities](../guide/model_specificities.md#serialization).


<div style="background-color: #E9F2F9; padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>NOTE:</em></strong>  
  In OpenMalaria, surveys track events since the last survey and capture the current state at the survey’s start (e.g., the number of patent hosts).  
  
  - The minimum survey interval is <strong>5 days</strong>.  
  - Only <strong>one</strong> survey interval can be specified per scenario.  
</div>



