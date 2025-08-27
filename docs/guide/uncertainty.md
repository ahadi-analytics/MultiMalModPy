# Accounting for sources of uncertainty


## Randomness  

**EMOD**, **OpenMalaria**, and **malariasimulation** are each stochastic models that use a ‘seed’ (or the equivalent term ‘run number’ used in EMOD) 
to determine starting position of their respective (pseudo-) random number generators.
Thus seed selection can alter simulation outcomes that rely on stochastic decisions. 
For consistency the same set of seeds across all three models is run, for instance, selecting 20 seeds in the experiment set-up, will result in running 20 seeds across each model. 

## Model and parameter uncertainty  

- **OpenMalaria** provides a mechanism to account for model and parameter uncertainty by varying _model variants_. 
This approach allows the user to explore different model configurations and their impact on simulation outcomes. 
For more information, refer to the work by [Smith et al 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3260300/). 
In the initial framework release, only the base model is included. Future updates may include additional model variants.


- **EMOD’s** currently does not include built-in functionality for accounting for parameter uncertainty in its framework. 
However, an alternative approach for base calibration in EMOD will soon be available, enabling users to better account for parameter variability in future simulations. 
For details, see the guide on [alternative base calibration](../guide/model_specificities.md#using-alternative-base-calibration).   


- In **malariasimulation**, parameter uncertainty is addressed by drawing parameter values from posterior distributions around defined parameter sets. 
This technique allows for a more realistic representation of parameter variability, which can influence the outcomes of the simulation 
For more detailed information on how parameter sampling is implemented, see the section on [Paramerer sampling](../guide/model_specificities.md#parameter-sampling ). 

 