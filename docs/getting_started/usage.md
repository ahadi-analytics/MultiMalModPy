# How to use MultiMalModPy


### Setup and defining a simulation
The simulation process begins with user input of simulation parameters, specified in `setup_sim.py`. 
Once configured, simulations are submitted using launch_sim.py, and all defining parameters are stored in a serialized Python object (`exp.obj`).
This object ensures consistency throughout the simulation process.

Additionally, shell job submission scripts are generated to automate subsequent script execution,
streamlining the workflow. The `launch_sim.py` script provides flexibility by allowing users to modify parameters 
directly within the script or read them from a CSV file.

To further enhance modularity, the simulation configuration has been moved to the helper.py script, 
enabling `launch_sim.py` to dynamically overwrite parameters as needed.


###  Running a Simulation

1. Open a terminal and navigate to the repository:
```bash
cd ~/model-characterization
```

2. Run the Python script to define and launch the simulation:
```bash
python launch_sim.py
```
This executes a test run using the default settings specified in the script and `parse_launch_args` (see `helper.py`).

3. Monitor running simulations (if using SLURM):
```bash
squeue -u <username>
```

4. Once the simulations complete, analyzer scripts and default plots will automatically be generated.

**Example runs**
 
- Testrun: Run a quick test with predefined settings:
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria --test`

- Baseline run: Run simulations with default settings or modified defaults from the Python file:
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria`
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria  --rownum 0 --csv baseline_eirsweep_noCM`  

- Custom run: Run a simulation with specific interventions and test settings:
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria --intervention cc_step --test --emodstep burnin`
  - `python launch_sim.py  --models EMOD MalSim OpenMalaria  --rownum 0 --csv cc_step_test`  



### Simulation and raw outputs
Once initiated, the simulation process runs automatically. 
Model-specific utility functions generate distinct scenarios for each model, ensuring tailored execution. 
Simulations run independently for each model, producing raw output data. 
The runtime varies depending on the complexity and computational demands of each model.  

### Postprocessing and standardized outputs 
Each model’s relevant simulation outputs are loaded and combined, assigning the unique identifier that matches the index
in the scenario data table and saved as a CSV file.  
The outcome metrics are then renamed and conversions into the same units are performed (i.e. annualized incidence per
person). Outcomes are further aggregated to the specified time interval (5 days, monthly, annually, averaged across the whole
monitoring time), and user-specified age groups.  

**Time-series:**

- `mmmpy_yr.csv`: _Age-bin_ specific key malaria outcomes* over time aggregated by year
- `mmmpy_mth.csv`: _Age-bin_ specific key malaria outcomes* over time aggregated by month-year
- `mmmpy_5day.csv`: _Age-bin_ specific key malaria outcomes* over time aggregated by 5days-year


**Aggregated times for relationship and seasonality trends:**

- `mmmpy_timeavrg.csv`: _Age-group_ specific key malaria outcomes* and transmission outcomes**, aggregated over whole
  monitoring period

**Additional output files:**

- `EIR.csv`, `EIR_yr.csv`,  `EIR_mth.csv` and `EIR_daily.csv`: All age simulated EIR (added to benchmark output csvs)

#### Output measures

| Column             | Description                                                                                                        | EMOD                                                                                                                                                 | malariasimulation                                                                                                                     | OpenMalaria                                                                                                                                                              |   |
|:-------------------|:-------------------------------------------------------------------------------------------------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------|:--------------------------------------------------------------------------------------------------------------------------------------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---|
| index              | unique identifier (scenario * seed)                                                                                | Assigned as tag in the simulations                                                                                                                   | Assigned to csv scenario file name                                                                                                    | Assigned to xml scenario input file names                                                                                                                                |   |
| (input)            |                                                                                                                    |                                                                                                                                                      |                                                                                                                                       |                                                                                                                                                                          |   |
| date               | Simulation time converted to calendar dates                                                                        | Simulation start date + days that passed in the simulation                                                                                           | Simulation start date + days that passed in the simulation                                                                            | days = survey * 5 <br/>  date = year & month & ‘1’ for monthly aggregation)<br/>   month = days/365.0001/12 <br/>  year = days/365.0001                                  |   |
| year               | Simulation time to calendar year                                                                                   | daily timesteps/365                                                                                                                                  | daily timesteps/365                                                                                                                   | 73 5-day timesteps                                                                                                                                                       |   |
| ageGroup           | Age of human host population  Additional age aggregation performed for custom broader age groups specified by user | Age groups to write out specified in reporter,<br/> can be different from the agebins defined to specify demography                                  | Rendering of age groups need to be specified for each outcome,  <br/> can be different from the agebins defined to specify demography | Age groups that are written out are the same as  defined age bins in the demography section.  <br/>                                                                      |   |
| nHost              | human host population                                                                                              | Input population size is used as scaling factor for   population size defined in the demography file        <br/>  _'Average Population by Age Bin'_ | Input population size is written into corresponding   R parameter             Population is  written out per index   and age group n  | Input population size is written out per index and age group <br/>   _measure 0-‘nHost‘_ |   |
| prevalence         | Proportion of individuals with   patent infections                                                                 | Based on microscopy with defined diagnostic   threshold, written out per index, time, age bin  <br/>          _'PfPR by Age Bin'_                    | Calculated from `n_detect/ nHost` per index, time,   age bin            secondary outcome                                             | Calculated from `nPatent / nHost` per index, time,   age bin       _secondary outcome_                                                                              |   |
| prevalence_2to10   | Proportion of individuals with   patent infections in 2-10 year olds                                               | As above, written out for age 2 to 10 (separate   outcome in model)    <br/>   _PfPR_2to10_                                                          | Rendered separately  for age 2 to 10 (separate outcome in model) (?)                                                                  | As above, calculated mean across   `prevalence` of individuals aged 2 to 10 years                                                                                        |   |
| clinical_incidence | Number of clinical cases per   person per year (ppy)                                                               | Written out per index, time, age bin   <br/>    _Annual Clinical Incidence by Age Bin_                                                               | Calculated from `n_inc_clinical, nHost` and reporting   interval   <br/>  _secondary outcome_                                         | Calculated from `nUncomp, nHost` and reporting   interval <br/> _secondary outcome_                                                                                      |   |
| severe_incidence   | Number of severe cases per   person per year (ppy)                                                                 | Written out per index, time, age bin   <br/>       _Annual Severe Incidence by Age Bin_                                                              | Calculated from `n_inc_severe, nHost` and reporting   interval   <br/>  _secondary outcome_                                           | Calculated from `nSevere nHost` and reporting   interval  <br/>  _secondary outcome_                                                                                     |   |
| Simulated EIR      | Simulated EIR  - Time unit corresponds to the same as of the output file (daily, monthly, yearly)                  |                                                                                                                                                      |                                                                                                                                       |                                                                                                                                                                          |   |
| n_infectious_mos   | Number of infectious mosquitoes                                                                                    |                                                                                                                                                      |                                                                                                                                       |                                                                                                                                                                          |   |
| n_total_mos_pop    | Number of host-seeking mosquitoes                                                                                  |                                                                                                                                                      |                                                                                                                                       |                                                                                                                                                                          |   |



### Visualization of outputs
Once postprocessing is complete, visualization begins automatically through the analyzer module. 
Standardized CSV output files for each model are used to generate a set of predefined figures, including relationships between outcomes,
time-series plots, and age-specific trends. 
These figures provide an initial visual analysis of the results and can be modified or extended by the user to 
accommodate specific research needs.  

The framework comes with three standardized plotting scripts:    
-  [plot_timeseries.py](../../_scratch/api/plotter/plot_timeseries.md) the timeseries for selected outcome measures,   
-  [plot_agecurves.py](../../_scratch/api/plotter/plot_agecurves.md) the relation of outcome measures by age groups,  
-  [plot_relationship.py](../../_scratch/api/plotter/plot_relationship.md) relationship between disease transmission and disease outcomes.  


#### Customizing figures 
Each of the existing plotting scripts allow for the user to define what outcomes should be displayed in the
color, the columns, axis and so on. Edits can be directly made in the respective scripts.

#### Adding new figures 
Additional plotting scripts from the user can be added to the `plotter` subdirectory.
It is recommended to have the filename start with `plot_` for consistency and to facilitate integrating the new plotter into the framework.

At the beginning it will be easiest to run the new plotters manually after the default outputs were 
successfully  generated.

For instance:   
`python plotter/plot_custom1.py  --models EMOD malariasimulation OpenMalaria` 





