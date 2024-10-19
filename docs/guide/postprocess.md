# Postprocess outputs 

## Raw outputs
Coming soon...





## Standardized Outputs

### Run analyzer 
- In terminal navigate to repository  `cd ~/model-characterization`
- Run python script that defines the simulation i.e. `python launch_sim.py` for a test run using defaults specified in
  the script and `parse_launch_args` (see helper.py)
    - Other options defined in the [run_launch_sim.sh](https://github.com/numalariamodeling/model-characterization/blob/main/run_launch_sim.sh)
    - `python launch_sim.py --emodstep burnin --models EMOD MalSim OpenMalaria`
    - `python launch_sim.py --models EMOD MalSim OpenMalaria --rownum 0 --csv baseline_eirsweep_noCM`
- Check simulations via `squeue -u <username>`
- Wait for simulations to finish after which analyzer scripts and default plots will automatically start running
- If you need to resubmit the `analyze_sim.py` script, it can be found in `experiments/<suite>/<exp_name>`
     ```
      cd /home/b1139/model-characterization/EMOD  
      python analyze_sim.py -d /projects/b1139/emod-om/experiments/forcedEIR/baseline_noCM_EIRseason -i
      fb508aba-2aa7-43b3-b365-ea7c227d7781
     ``` 
- Perform additional analysis or plot custom results


### Outputs files
Standardized csv files for selected outcome metrics per age group and either aggregated over time (Benchmark.csv), or aggregated for specific time intervals  (daily, 5-day, monthly or annual time-series) ( PfPRAgebin_<timeseriesname>.csv). In addition, EIR-vector-transmission related metrics across all ages are generated for different time-intervals or aggregated over time written into csv files named “EIR” and specified time aggregation.  

**Time-series:**

- `All_Age_SamplePlot.csv`: _All age_ per timestep and basic simulation outputs for checking simulations
- `PfPR_ClinicalIncidence_mth.csv`: _Age-bin_ specific key malaria outcomes* over time aggregated by month-year
- `PfPR_ClinicalIncidence_yr.csv`: _Age-bin_ specific key malaria outcomes* over time aggregated by year

**Aggregated times for relationship and seasonality trends:**

- `Benchmark.csv`: _Age-group_ specific key malaria outcomes* and transmission outcomes**, aggregated over whole
  monitoring period


**Additional output files:**

- `EIR.csv`, `EIR_yr.csv` and `EIR_mth.csv`: All age simulated EIR (added to benchmark output csvs)
- `Surveyoutput_base.csv`: Raw output for OpenMalaria from concatenating survey outputs, optional i.e. for testing.
- `Event reporters ..` to be added

### Output measures


coming soon


### Customizing outputs

To customize a simulation, any of the defined parameters listed
in [Simulation experiment configuration](https://github.com/numalariamodeling/model-characterization#simulation-experiment-configuration)
can be changed.
Commonly modified parameters are `eir`, `seasonality`, `burnin` period, and sometimes `cm_clinical`, for base-case
scenario runs.
Additional interventions are in progress and instructions for simulating other interventions will come soon.


## Result figures

### Default figures 

The framework comes with three standardized plotting scripts:    
-  [plot_timeseries.py](../api/plot_timeseries.md) the timeseries for selected outcome measures,   
-  [plot_agecurves.py](../api/plot_agecurves.md) the relation of outcome measures by age groups,  
-  [plot_relationship.py](../api/plot_relationship.md) relationship between disease transmission and disease outcomes.  


### Customizing figures 
Each of the existing plotting scripts allow for the user to define what outcomes should be displayed in the
color, the columns, axis and so on. Edits can be directly made in the respective scripts.

### Adding new figures 
Additional plotting scripts from the user can be added to the `plotter` subdirectory.
It is recommended to have the filename start with `plot_` for consistency and to facilitate integrating the new plotter into the framework.

At the beginning it will be easiest to run the new plotters manually after the default outputs were 
successfully  generated.

For instance:   
`python plotter/plot_custom1.py  --models EMOD malariasimulation OpenMalaria` 



