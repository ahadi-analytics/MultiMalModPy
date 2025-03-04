# Accounting for sources of uncertainty


## Randomness  

**EMOD**, **OpenMalaria**, and **malariasimulation** are each stochastic models that use a ‘seed’ (or the equivalent term ‘run number’ used in EMOD) 
to determine starting position of their respective (pseudo-) random number generators.
Thus seed selection can alter simulation outcomes that rely on stochastic decisions. 
For consistency the same set of seeds across all three models is run, for instance, selecting 20 seeds in the experiment set-up, will result in running 20 seeds across each model. 

## Model and parameter uncertainty  

- **OpenMalaria** allows to take into account model and parameter uncertainty through varying ‘model variants’ [Smith et al 2012](https://pmc.ncbi.nlm.nih.gov/articles/PMC3260300/). 
In the initial framework release, only the [base model]() is included.  


- **EMOD’s** functionality to account for parameter uncertainty is not yet available in the framework. 
An [alternative base calibration](../getting_started/model_specificities.md#using-alternative-base-calibration#emod) will soon become available.   


- In **malariasimulation**, accounting for parameter uncertainty to better reflect potential variability in the simulation 
results has been integrated by drawing parameter values from posterior distributions around defined parameter sets.
Details are described under model-specific features [Paramerer sampling](../getting_started/model_specificities.md#parameter-sampling ). 

 