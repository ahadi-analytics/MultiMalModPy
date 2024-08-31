
# Simulation configuration

Parameter specifications for framework and simulation setup:

- [ ] **Simulation experiment name, infrastructure, directories and models to run**
    - `mem_increase_factor`: scaling factor on default memory requested, which usually can be left at 1 for test
      simulation, but may have to be
      4 or 8 for larger simulations. The default memory requested also differs for the slurm job submission to run
      versus to analyze a simulation.
    - `custom_subdir`:  If `None`, no i.e. user specific subdir created, default `os.getlogin()`
    - `SUITEname`: overall subdir to declare a group of simulations to run, default is `f'{entomology_mode}EIR'`
    - `exp_name`: name of
      simulation experiment to run, default is `f'sim_{dt.now().strftime("%Y_%m_%d_%H_%M_%S")}'`, whereas a more
      meaningful name might be choosen for simulation experiments to use outputs for some result description rather than
      just for testing.
    - `models_to_run`: Name of models to run (case-sensitive), options are **EMOD** , **OpenMalaria** and/or  **MalSim**
    - `om_scaffold`: name of **OpenMalaria** input XML to use
    - `MalSim_script`: name of **malariasimulation** R script to use

- [ ] **Population size, agebins and seeds**
    - `pop_size`: number of individuals to simulate for human population, default for testing `1000`, which should not
      be used for actual
      simulations to generate results
    - `agebins`: age groups to monitor (select finest age groups required, can be further combined in postprocessing)
    - `age_groups_aggregates`: Age groups to aggregate to in postprocessing
    - `num_seeds_burnin`: EMOD specific (even if not declared as such), number of seeds to run for burnin if run
      separately
    - `num_seeds`: number of
      seeds to run for simulation (applies to all models)

- [ ] **Simulation time and reporting intervals**
    - `start_year`: Calendar year at which monitoring period should start (after burnin)
    - `end_year`: Calendar year at which monitoring period should end
    - `burnin`: Number of years to run prior to monitoring period (from these the simulation start year will be
      calculated) - 80 years is recommended for all models to establish immunity in the simulated population
    - `om_survey_step`: survey intervals for which outcomes are reported in OpenMalaria, default is `30d`. Note, in
      EMOD, monthly reports are per default included in monitored simulation period.
    - `emod_step`: EMOD allows to run burnin separate from the monitoring period (here equivalent to `pickup`),
      if `None` both similation times
      are run together, which can be computational and time-wise too extensive when running long burnin, large
      populations and high EIRs.
    - `emod_serialized_id`: ID of EMOD burnin experiment to pickup from, if `emod_step ='pickup'`

- [ ] **Transmission intensity and seasonality**
    - `entomology_mode`:    select whether to run with vectors (`dynamic`) or without (`forced`)
    - `seasonality`: name of pre-defined transmission seasonality profile to simulate (current options
      are `["perennial", "seasonal"]`)
    - `eir`: annual input EIR (or equivalent, depending on model and entomology mode)


- [ ] **Case management parameters**
    - `cm_start`: do not change, can be removed, case managament would always start on day 1, except of having multiple
      intervention
      deployments to simulate coverage increase over time (not applicable here)
    - `cm_clinical`: clinical case management coverage
    - `cm_severe`: do not change, will be adapted depending on clinical case management, but to be at least 48%
    - `detectionLimit`: detection limit for parasites per micoliter blood for detection of prevalent malaria infections

- [ ] **CC step parameters**
    - `carrying_capacity_step`: Defined the step change from to in a list,
      example `['10%-25%', '10%-50%', '25%-10%', '25%-50%', '50%-10%', '50%-25%']`
    - `eir_scalar_emod`: defines the scalar for each carrying_capacity_step defined that will achieve the desired step
      change for EMOD
    - `eir_scalar_malsim`: defines the scalar for each carrying_capacity_step defined that will achieve the desired step
      change for malariasimulation
    - `eir_scalar_om`: defines the scalar for each carrying_capacity_step defined that will achieve the desired step
      change for OpenMalaria

- [ ] **Simulation experiment setup of sweeps and postprocessing**
    - `sweep_list`: List of parameter names that together uniquely identify a simulation scenario (and will be written
      into `scenarios.csv`)
    - `plots_to_run`: List of types of plots to run automatically after the simulations finished

