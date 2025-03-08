
# Developer and Advanced User Guide
 This site includes a mix of additional topics for maintaining and enhancing the online documentation as well as the MultiMalModPy framework.




## Importation 

### EMOD  

Importation in EMOD is setup using the [add_outbreak_individual](https://docs.idmod.org/projects/emodpy-malaria/en/latest/emodpy_malaria.interventions.outbreak.html#emodpy_malaria.interventions.outbreak.add_outbreak_individual) function from emodpy-malaria.  
The specific python code snippet, as used in MultiMalModPy [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/functions/EMOD_functions.py#L113), is shown below:  

```python
ncases_per_year_per1000pop = (exp.emod_importation_rate * exp.emod_pop_size) / 1000
add_outbreak_individual(camp, start_day=1, target_num_individuals=ncases_per_year_per1000pop,
                        repetitions=-1, timesteps_between_repetitions=365)
```

### OpenMalaria  

Importation in OpenMalaria is setup using [importedInfections](https://github.com/SwissTPH/openmalaria/wiki/ModelIntervMisc#import-infections):
The specific XML chunk, as used in MultiMalModPy [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/OpenMalaria/scaffolds/R0000GA.xml#L72), is shown below:  

```XML 
<importedInfections>
    <timed>
        <rate time="0" value="@importation_rate@"/>
    </timed>
</importedInfections>
```

## Entomology mode

### EMOD  

Relevant code chunks are under EMOD_functions.py [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/functions/EMOD_functions.py#L100) and
 under EMOD/utils.py [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/utils.py#L61).

'Forced' EIR uses the [add_scheduled_input_eir](https://docs.idmod.org/projects/emodpy-malaria/en/latest/emodpy_malaria.interventions.inputeir.html#emodpy_malaria.interventions.inputeir.add_scheduled_input_eir) function from emodpy-malaria.

```python
## If forced EIR, treated as campaign in EMOD
if row.entomology_mode == 'forced':
    set_inputEIR_seasonality(camp, float(row.model_input_em), row.seasonality)
```

```python
if entomology_mode == 'dynamic':
    task.common_assets.add_directory(os.path.join(manifest.input_dir, "example_weather"), relative_path="climate")
```

They also require different sweeping, defined in `config_sweep_builder` (and `config_sweep_builder_pickup`) [see code](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/EMOD/utils.py#L251C1-L265C42).
You can find details on parameter sweeping for building scenarios under [simulation guide/scenarios]()

### OpenMalaria  

`entomology_mode` in OpenMalaria defines the feedback from human infectiousness to subsequent Entomological Infection Rate (EIR).   
`entomology_mode` in OpenMalaria is setup by literally defining the ['mode of entomology'](https://github.com/SwissTPH/openmalaria/wiki/ModelTransmission#simulation-mode):
The specific XML chunk, as used in MultiMalModPy [here](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/OpenMalaria/scaffolds/R0000GA.xml#L131C6-L131C21), is shown below:  

```XML 
<entomology mode="@entomology_mode@" name="Namawala" scaledAnnualEIR="@eir@">
```




## Sweep parameters

### EMOD
```python
    if exp.entomology_mode == 'forced':
        matAP = 0.1327
        sweeps = [[ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
                   partial(set_param, param='Maternal_Antibody_Protection', value=matAP * mAb_vs_EIR(row.model_input_emod)),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
    elif exp.entomology_mode == 'dynamic':
        sweeps = [[ItvFn(all_campaigns, exp, row=row, intervention_list = exp.intervention_list),
                   CfgFn(habitat_setup, exp, row=row),
                   SwpFn(climate_setup,  seasonality = row.seasonality),
                   partial(set_param, param='x_Temporary_Larval_Habitat', value=row.model_input_emod),
                   partial(set_param, param='Run_Number', value=s)]
                  for i, row in scen_df.iterrows()
                  for s in range(nseeds)]
```