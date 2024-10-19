# plot_relationship.py

The functions prevalence2to10_to_incidence, prevalence2to10_to_incidence_by_age_and_model, eir_to_outcome, and input_to_simulated_eir 
produce comparative visualizations that explore the relationships between different malaria epidemiological metrics. 
These functions facilitate the analysis of how PfPR2to10 influences clinical and severe incidence across various age groups and models,
as well as the impact of the entomological inoculation rate (EIR) on outcome variables. By generating detailed plots, 
they enhance understanding of the dynamics between prevalence, incidence, and model inputs, aiding in the assessment of malaria transmission dynamics.

Function Documentations for:  
 [prevalence2to10_to_incidence](#`prevalence2to10_to_incidence`)  
 [prevalence2to10_to_incidence_by_age_and_model](#`prevalence2to10_to_incidence_by_age_and_model`)  
 [eir_to_outcome](#`eir_to_outcome`)  
 [input_to_simulated_eir](#`input_to_simulated_eir`)  
 

------------------ 


## `prevalence2to10_to_incidence` 

### Overview

The `prevalence2to10_to_incidence` function generates line plots that display the relationship between PfPR2to10 and either clinical or severe incidence. 
It groups the results by a specified variable and creates separate panels for each model.
The function saves the generated plots to a specified directory.

### Parameters

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes prevalence and incidence data.                                                               |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple panels on the plot. Default is `'modelname'`.                        |
| `facet_var`          | `str`, optional    | Variable used to create subplots based on its unique values. Default is `'seasonality'`.                             |
| `channel`            | `str`              | Variable representing the y-axis data to be plotted (e.g., clinical incidence).                                      |
| `agegrps`            | `list`, optional    | List of age groups to be used for aggregating data. Default is `None`.                                               |

### Returns

  `None`: The function saves the plots to the specified directory.

### Usage Example  

```   
import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'prevalence_2to10': [0.1, 0.2, 0.3, 0.4, 0.5],
    'clinical_incidence': [0.05, 0.1, 0.15, 0.2, 0.25],
    'modelname': ['Model A', 'Model B', 'Model A', 'Model B', 'Model A'],
    'seasonality': ['Season 1', 'Season 2', 'Season 1', 'Season 2', 'Season 1'],
    'ageGroup': ['0-5', '0-5', '6-10', '6-10', '11-15'],
}

df = pd.DataFrame(data)

# Call the function
prevalence2to10_to_incidence('path/to/save/directory', df)

```


------------------ 

## `prevalence2to10_to_incidence_by_age_and_model`   

### Overview   

The `prevalence2to10_to_incidence_by_age_and_model` function generates line plots that depict the relationship between PfPR2to10 and either clinical or severe incidence.
The plots are organized into panels separated by model (columns) and age groups (rows). The function saves the generated plots to a specified directory.  

### Parameters  

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes prevalence and incidence data, along with model and age group information.                   |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple panels on the plot. Default is `'modelname'`.                        |
| `channel`            | `str`              | Variable representing the y-axis data to be plotted (e.g., clinical incidence).                                      |

### Returns

  `None`: The function saves the plots to the specified directory.

### Usage Example  

```   
import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'prevalence_2to10': [0.1, 0.2, 0.3, 0.4, 0.5],
    'clinical_incidence': [0.05, 0.1, 0.15, 0.2, 0.25],
    'modelname': ['Model A', 'Model B', 'Model A', 'Model B', 'Model A'],
    'seasonality': ['Season 1', 'Season 1', 'Season 2', 'Season 2', 'Season 1'],
    'ageGroup': ['0-5', '0-5', '6-10', '6-10', '11-15'],
}

df = pd.DataFrame(data)

# Call the function
prevalence2to10_to_incidence_by_age_and_model('path/to/save/directory', df)

``` 

------------------ 


## `eir_to_outcome` 

### Overview  

The `eir_to_outcome` function generates line plots that illustrate the relationship between the entomological inoculation rate (EIR) and a specified outcome variable. The plots are organized by model names (as colors) and further divided into panels based on a specified variable (sweepvar).
The function saves the generated plots to a specified directory.  

### Parameters  

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes combined model results and relevant variables.                                               |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple panels on the plot. Default is `'cm_clinical'`.                     |
| `eir_val`            | `str`, optional    | The EIR value to be used for plotting. Default is `'simulatedEIR'`.                                                |
| `channel`            | `str`, optional    | The outcome variable to compare against EIR (e.g., prevalence or incidence).                                        |
| `agegrp`             | `str`, optional    | Limits the resulting graphs to the selected age group. Default is `'0-5'`.                                         |

### Returns  

  `None`: The function saves the plots to the specified directory.  

### Usage Example  

```  
import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'simulatedEIR': [0.1, 0.5, 1.0, 5.0, 10.0],
    'prevalence_2to10': [0.01, 0.05, 0.1, 0.2, 0.25],
    'cm_clinical': ['Model A', 'Model B', 'Model A', 'Model B', 'Model A'],
    'seasonality': ['Season 1', 'Season 1', 'Season 2', 'Season 2', 'Season 1'],
    'output_target': [1, 2, 3, 4, 5],
}

df = pd.DataFrame(data)

# Call the function
eir_to_outcome('path/to/save/directory', df)

``` 

------------------ 


## `input_to_simulated_eir` 

### Overview 

The `input_to_simulated_eir` function generates line plots comparing input EIR values to simulated annual EIR values. The plots are grouped by model names (sweepvar) and divided into panels based on a specified variable (facet_var). The function saves the generated plots to a specified directory.

### Parameters  

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes combined model results and relevant variables.                                               |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple lines on the plot. Default is `'cm_clinical'`.                       |
| `facet_var`          | `str`, optional    | Variable used to create subplots based on its unique values. Default is `'seasonality'`.                             |

### Returns  

  `None`: The function saves the plots to the specified directory.

### Usage Example  

``` 
import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'simulatedEIR': [0.1, 0.5, 1.0, 5.0, 10.0],
    'output_target': [1, 2, 3, 4, 5],
    'cm_clinical': ['Model A', 'Model B', 'Model A', 'Model B', 'Model A'],
    'seasonality': ['Season 1', 'Season 1', 'Season 2', 'Season 2', 'Season 1'],
}

df = pd.DataFrame(data)

# Call the function
input_to_simulated_eir('path/to/save/directory', df)

``` 


