# Create simulations



The `launch_sim.py` script launches simulation runs, with the possibility to change and
edit parameters directly in the python script or to read in parameter values from a csv file.

The configuration had been moved to the `helper.py` script, allowing the launch python script to overwrite parameters as
needed.



## Scenarios implemented

Scenarios csvs are stored in the `scenario_inputs` sub-directory:

- `baseline_eirsweep_noCM.csv`: most basic simulation without any interventions or treatment of cases  
  Forthcoming examples may include:
- `baseline_eirsweep_CM.csv`:
- `baseline_eirchange_noCM.csv`:
- `cc_step_test.csv`: ...
- `smc_eirsweep_noCM.csv`: ...
- ...

Details provided
in [scenario_inputs/README](https://github.com/numalariamodeling/model-characterization/blob/main/scenario_inputs/README.md)



## Customize simulations

## Advanced use


