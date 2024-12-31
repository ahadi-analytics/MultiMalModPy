# Visualize outputs

## Default figures 

The framework comes with three standardized plotting scripts:    
-  [plot_timeseries.py](../api/plotter/plot_timeseries.md) the timeseries for selected outcome measures,   
-  [plot_agecurves.py](../api/plotter/plot_agecurves.md) the relation of outcome measures by age groups,  
-  [plot_relationship.py](../api/plotter/plot_relationship.md) relationship between disease transmission and disease outcomes.  


## Customizing figures 
Each of the existing plotting scripts allow for the user to define what outcomes should be displayed in the
color, the columns, axis and so on. Edits can be directly made in the respective scripts.

## Adding new figures 
Additional plotting scripts from the user can be added to the `plotter` subdirectory.
It is recommended to have the filename start with `plot_` for consistency and to facilitate integrating the new plotter into the framework.

At the beginning it will be easiest to run the new plotters manually after the default outputs were 
successfully  generated.

For instance:   
`python plotter/plot_custom1.py  --models EMOD malariasimulation OpenMalaria` 


