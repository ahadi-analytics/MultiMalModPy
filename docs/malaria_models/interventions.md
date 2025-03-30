# Interventions

This page provides an overview to the available interventions and their implementation in each model _as used in
MultiMalModPy_.  
The function and implementation/use in the framework can be found in the [API](), specifically the `intervention.py`
script for each model.

<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>⚠️NOTE:</em></strong> 
  For latest and complete documentation, please visit the documentation sites from the maintaining institutions under the provided links.
</div>  


**Other interventions than case management are not part of the initial release and will be added in near future.**

## Case management

Each model simulates case management differently and has a different definition of a malaria case. 

🚩 **Model alignment and implementation in MultiMalModPy:**   
_Box is checked if aligned_  
 
 ✗ **Mode of action**   _The level of detail varies across the models which cannot be aligned_  
 ✗ **Case definition**   _The case definition for each model has been checked and defaults for each model were kept._  
 ✔ **Drug used**   _All models use ACT as the first line treatment for uncomplicated malaria._  
 ✔ **Coverage**   _Treatment coverage is implemented differently in each model and was aligned to correspond to a 14 day coverage._  
 ✔ **Target population**   _Whole population targeted and treated equally, i.e. no distinction by age._  
 ✔ **Resistance**   _Drug resistance not included._  
 ✔ **Deployment time and duration**   _Intervention starts from the beginning of the simulation and stays constant throughout._  


### EMOD

- Documentation main 
  page:[malaria-model-antimalarial-drugs](https://docs.idmod.org/projects/emodpy-malaria/en/latest/emod/malaria-model-antimalarial-drugs.html)   
- Function: [treatment_seeking.py](https://github.com/EMOD-Hub/emodpy-malaria/blob/main/emodpy_malaria/interventions/treatment_seeking.py)   
- Related publications: [Gerardin et al 2015](https://bmcinfectdis.biomedcentral.com/articles/10.1186/s12879-015-0887-y)  
- Additional: [malaria_drug_params.csv](https://github.com/EMOD-Hub/emodpy-malaria/blob/main/emodpy_malaria/malaria_drug_params.csv)   

<details><summary><span>treatment_seeking</span></summary>   
<p>

```python
def add_treatment_seeking(campaign,
                          start_day: int = 1,
                          targets: list = None,
                          drug: list = None,
                          node_ids: list = None,
                          ind_property_restrictions: list = None,
                          drug_ineligibility_duration: float = 0,
                          duration: int = -1,
                          broadcast_event_name: str = 'Received_Treatment'):
    camp_events = _get_events(campaign=campaign, start_day=start_day, targets=targets, drug=drug, node_ids=node_ids,
                              ind_property_restrictions=ind_property_restrictions,
                              drug_ineligibility_duration=drug_ineligibility_duration, duration=duration,
                              broadcast_event_name=broadcast_event_name)
    for event in camp_events:
        campaign.add(event)
```

``` 

 targets is a list of dictionaries defining the trigger event and coverage for and
    properties of individuals to target with the intervention with all possible options being:
    [{"trigger":"NewClinicalCase","coverage":0.8,"agemin":15,"agemax":70, "rate":0.3}]
    "rate" is the inverse of the average delay in time to treatment seeking from an exponential distribution
    "trigger" must be defined, but everything else has defaults:
    coverage = 1, affects all
    agemin/agemax = 0/125, affects all
    rate = 0, no delay, seek treatment immediately

```

</p>
</details>    

 
<details><summary><span>json snippet (example)</span></summary>    
<p>

```json

{
  "class": "CampaignEvent",
  "Event_Coordinator_Config": {
    "class": "StandardInterventionDistributionEventCoordinator",
    "Demographic_Coverage": 1,
    "Individual_Selection_Type": "DEMOGRAPHIC_COVERAGE",
    "Intervention_Config": {
      "class": "NodeLevelHealthTriggeredIV",
      "Actual_IndividualIntervention_Config": {
        "class": "DelayedIntervention",
        "Actual_IndividualIntervention_Configs": [
          {
            "class": "AntimalarialDrug",
            "Cost_To_Consumer": 0,
            "Disqualifying_Properties": [],
            "Dont_Allow_Duplicates": 0,
            "Drug_Type": "Artemether",
            "Intervention_Name": "AntimalarialDrug_Artemether",
            "New_Property_Value": ""
          },
          {
            "class": "AntimalarialDrug",
            "Cost_To_Consumer": 0,
            "Disqualifying_Properties": [],
            "Dont_Allow_Duplicates": 0,
            "Drug_Type": "Lumefantrine",
            "Intervention_Name": "AntimalarialDrug_Lumefantrine",
            "New_Property_Value": ""
          },
          {
            "class": "BroadcastEvent",
            "Broadcast_Event": "Received_Treatment",
            "Disqualifying_Properties": [],
            "Dont_Allow_Duplicates": 0,
            "Intervention_Name": "BroadcastEvent",
            "New_Property_Value": ""
          }
        ],
        "Coverage": 1,
        "Delay_Period_Distribution": "EXPONENTIAL_DISTRIBUTION",
        "Delay_Period_Exponential": 3.3333333333333335,
        "Disqualifying_Properties": [],
        "Dont_Allow_Duplicates": 0,
        "Intervention_Name": "DelayedIntervention",
        "New_Property_Value": ""
      },
      "Blackout_Event_Trigger": "",
      "Blackout_On_First_Occurrence": 0,
      "Blackout_Period": 0,
      "Demographic_Coverage": 0.0,
      "Disqualifying_Properties": [],
      "Distribute_On_Return_Home": 0,
      "Dont_Allow_Duplicates": 0,
      "Duration": -1,
      "Intervention_Name": "NodeLevelHealthTriggeredIV",
      "New_Property_Value": "",
      "Node_Property_Restrictions": [],
      "Property_Restrictions": [],
      "Target_Age_Max": 115,
      "Target_Age_Min": 0,
      "Target_Demographic": "ExplicitAgeRanges",
      "Target_Gender": "All",
      "Target_Residents_Only": 0,
      "Targeting_Config": {
        "HasIP": {},
        "HasIntervention": {},
        "IsPregnant": {},
        "TargetingLogic": {}
      },
      "Trigger_Condition_List": [
        "NewClinicalCase"
      ]
    },
    "Node_Property_Restrictions": [],
    "Number_Repetitions": 1,
    "Property_Restrictions": [],
    "Property_Restrictions_Within_Node": [],
    "Target_Demographic": "Everyone",
    "Target_Gender": "All",
    "Target_Residents_Only": 0,
    "Targeting_Config": {
      "HasIP": {},
      "HasIntervention": {},
      "IsPregnant": {},
      "TargetingLogic": {}
    },
    "Timesteps_Between_Repetitions": -1
  },
  "Nodeset_Config": {
    "class": "NodeSetAll"
  },
  "Start_Day": 1
}

```

</p>
</details>   

<br>

### malariasimulation

- Documentation main page: [treatment](https://mrc-ide.github.io/malariasimulation/articles/Treatment.html)
- Function: [set_clinical_treatment](https://github.com/mrc-ide/malariasimulation/blob/master/R/drug_parameters.R#L49)
- Related publications:  [Okell et al (2014).](https://doi.org/10.1038/ncomms6606)

<details><summary><span>set_clinical_treatment</span></summary>   
<p>

```R
set_clinical_treatment <- function(parameters, drug, timesteps, coverages) {
  stopifnot(all(coverages >= 0) && all(coverages <= 1))
  n_drugs <- length(parameters$drug_efficacy)
  if (drug < 1 | drug > n_drugs) {
    stop('Drug index is invalid, please set drugs using set_drugs')
  }
  drug_index <- which(parameters$clinical_treatment_drugs == drug)
  if (length(drug_index) == 0) {
    drug_index <- length(parameters$clinical_treatment_drugs) + 1
  }
  parameters$clinical_treatment_drugs[[drug_index]] <- drug
  parameters$clinical_treatment_timesteps[[drug_index]] <- timesteps
  parameters$clinical_treatment_coverages[[drug_index]] <- coverages
  last_timestep <- max(unlist(parameters$clinical_treatment_timesteps))

  for (t in seq(last_timestep)) {
    if (sum(get_treatment_coverages(parameters, t)) > 1) {
      stop('The sum of drug coverages cannot be greater than 1 at any timestep')
    }
  }
  parameters
}
```

</p>
</details>   

<br>

### OpenMalaria  

- Documentation main page:  
    - [ScenarioHealthSystem](https://github.com/SwissTPH/openmalaria/wiki/ScenarioHealthSystem)  
    - [ScenarioPharmacology](https://github.com/SwissTPH/openmalaria/wiki/ScenarioPharmacology#antimalarial-drug-modelling)  
- Function: [set_clinical_treatment](https://github.com/mrc-ide/malariasimulation/blob/master/R/drug_parameters.R#L49)  
- Related publications:  [Galactionova et al (2015).](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0127818) 

<details><summary><span>ImmediateOutcomes</span></summary>   
<p>

<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>⚠️ NOTE:</em></strong> 
  Multiple options for simulating 'case management' exist. Below is the  implementation as used in MultiMalModPy.
</div>  

```XML  

<ImmediateOutcomes name="example name">
    <drugRegimen firstLine="ACT" inpatient="QN" secondLine="ACT"/>
    <initialACR>
        <ACT value="1.0"/>
        <QN value="1.0"/>
        <selfTreatment value="0.0"/>
    </initialACR>
    <compliance>
        <ACT value="1.00"/>
        <selfTreatment value="1.0"/>
    </compliance>
    <nonCompliersEffective>
        <ACT value="0"/>
        <selfTreatment value="0"/>
    </nonCompliersEffective>
    <treatmentActions> <!-- only from schema 32 -->
        <ACT name="clear blood-stage infections">
            <clearInfections stage="blood" timesteps="1"/>
        </ACT>
        <QN name="clear blood-stage infections">
            <clearInfections stage="blood" timesteps="1"/>
        </QN>
    </treatmentActions>
    <pSeekOfficialCareUncomplicated1 value="0.04"/>
    <pSelfTreatUncomplicated value="0.0"/>
    <pSeekOfficialCareUncomplicated2 value="0.04"/>
    <pSeekOfficialCareSevere value="0.48"/>
</ImmediateOutcomes>

```

</p>
</details>   


<br>




<!---

## Vector control

### Insecticide treated bed nets (ITN)

#### EMOD
#### malariasimulation
#### OpenMalaria

### Indoor residual spraying (IRS)

#### EMOD
#### malariasimulation
#### OpenMalaria

### Larval Source Management (LSM)

#### EMOD
#### malariasimulation
#### OpenMalaria


## Chemoprevention

### Seasonal Malaria Chemoprevention (SMC)

#### EMOD
#### malariasimulation
#### OpenMalaria


### Perennial Malaria Chemoprevention (PMC)

#### EMOD
#### malariasimulation
#### OpenMalaria


## Vaccine

### Malaria vaccine

#### EMOD
#### malariasimulation
#### OpenMalaria

-->