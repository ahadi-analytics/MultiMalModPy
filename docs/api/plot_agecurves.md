# plot_agecurves.py

Function Documentation

## `age_curves` 

### Overview

The `age_curves` function generates plots over age based on the provided dataset. It takes into account the combined model results and allows for visualization of different channels across age groups. The function saves the generated plots to a specified directory.

### Requirements

This function requires the `PfPR_ClinicalIncidence_yr.csv` data file to be present in the specified directory.

### Parameters

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes combined model results.                                                                     |
| `channel`            | `str`              | Variable representing the y-axis data to be plotted.                                                                |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple lines on the plot. Default is `'modelname'`.                         |
| `facet_var`          | `str`, optional    | Variable used to create subplots based on its unique values. Default is `'output_target'`.                           |
| `age_groups_aggregates` | `list`, optional  | List of age groups for aggregating data. Default is `['0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100']`. |

### Returns  

`None`: The function saves the plots to the specified directory.  

### Usage Example  
 

```   

import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'ageGroup': ['0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100'],
    'prevalence': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    'modelname': ['Model A', 'Model B', 'Model A', 'Model B', 'Model A', 'Model B', 'Model A', 'Model B'],
    'output_target': ['Target 1', 'Target 2', 'Target 1', 'Target 2', 'Target 1', 'Target 2', 'Target 1', 'Target 2'],
}

df = pd.DataFrame(data)

# Call the function
age_curves('path/to/save/directory', df, 'prevalence')

```


