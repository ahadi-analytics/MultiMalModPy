# Case management  


## Model-specific structure    

Model-specific structure of case management is described  [here](../malaria_models/interventions.md#case-management-).


## Implementation in MultiMalModPy

In MultiMalModPy, the user can specify single constant coverage levels for clinical and for severe case management.  

In [setup_sim.py](https://github.com/ahadi-analytics/model-characterization/blob/main/setup_sim.py#L53C14-L53C96) , 
the user species case_management as a   List of tuples defining case management intervention configurations.  

``` 
case_management = [(0, 0),(0.15,0.5)]  # format: [(cm_clinical, cm_severe), (...)]
```

When running simulations via CSV, the tuples are included in a single cell as shown in the [example1.csv](https://github.com/ahadi-analytics/model-characterization/blob/main/scenario_csv/example1.csv).




