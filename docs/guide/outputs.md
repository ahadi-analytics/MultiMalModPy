
# Outputs

standardized csv files for selected outcome metrics per age group and either aggregated over time (Benchmark.csv), or aggregated for specific time intervals  (daily, 5-day, monthly or annual time-series) ( PfPRAgebin_<timeseriesname>.csv). In addition, EIR-vector-transmission related metrics across all ages are generated for different time-intervals or aggregated over time written into csv files named “EIR” and specified time aggregation.  

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

## Output measures


coming soon


## Customizing outputs

To customize a simulation, any of the defined parameters listed
in [Simulation experiment configuration](https://github.com/ahadi-analytics/model-characterization#simulation-experiment-configuration)
can be changed.
Commonly modified parameters are `eir`, `seasonality`, `burnin` period, and sometimes `cm_clinical`, for base-case
scenario runs.
Additional interventions are in progress and instructions for simulating other interventions will come soon.

