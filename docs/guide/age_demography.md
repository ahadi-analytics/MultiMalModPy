# Age and demography
_Implementation in MultiMalModPy_

<div style="background-color: #f4f4f4; padding: 12px; border-left: 5px solid #FF6B8B; border-radius: 5px; margin: 10px 0;">
    <strong>🔍</strong> For a detailed overview of how each model handles population and age demography, refer to the 
    <a href="../malaria_models/structure.md#population-and-age-demography" style="color: #0073e6; text-decoration: none;">
        Population and age demography
    </a> description under malaria models.
</div>



In MultiMalModPy, the user can specify the following time related parameters:
- `agebins` -  individual age categories used for detailed analysis in the simulation. 
- `age_groups_aggregates ` -  custom groupings of the agebins for aggregated analysis.  
- `emod_pop_size` , `malariasimulation_pop_size` , `openmalaria_pop_size` - population sizes (model specific)

Example:
``` 
agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]
age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100],  [0, 5], [0, 100]]
```


## Change age demography  

Changing the age stucture across the three models is currently not supported. 



