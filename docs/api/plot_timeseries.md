# plot_timeseries.py


The annual_timeseries, monthly_timeseries, and monthly_trends functions generate visualizations of 
temporal data, allowing for comparative analysis of model results across different time scales.
Each function is designed to plot specified outcome variables while accommodating grouping by model
type or age group, facilitating insights into trends over time. These functions enhance the
interpretability of complex data by providing clear, customizable plots that aggregate results 
annually or monthly.

Function Documentations for:  
 [monthly_trends](#`monthly_trends`)  
 [monthly_timeseries](#`monthly_timeseries`)  
 [annual_timeseries](#`annual_timeseries`)  


------------------ 


## `monthly_trends`   

### Overview

The `monthly_trends` function generates line plots to visualize monthly trends for a specified outcome variable, allowing for comparisons across different models or output targets. The data is aggregated across years, assuming a single occurrence per month.

### Parameters

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes combined model results and relevant variables, including a column for months.               |
| `channel`            | `str`              | Variable representing the y-axis data to be plotted.                                                                |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple lines on the plot. Default is `'output_target'`.                    |
| `agegrp`             | `str`, optional    | Age group filter for the data. Default is `'0-100'`.                                                                  |

### Returns

- `None`: The function saves the plots to the specified directory.

### Raises

- `ValueError`: If no seasonal transmission pattern is specified in the data.

### Usage Example

```  
import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'month': list(range(1, 13)) * 2,  # Months from January to December for two years
    'clinical_incidence': [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.35, 0.5, 0.45, 0.6, 0.55, 0.7] * 2,
    'output_target': ['Target A'] * 12 + ['Target B'] * 12,
    'modelname': ['Model A'] * 12 + ['Model B'] * 12,
}

df = pd.DataFrame(data)

# Call the function
monthly_trends('path/to/save/directory', df, 'clinical_incidence')
```   


------------------ 


## `monthly_timeseries` 

### Overview  

The `monthly_timeseries` function generates monthly time series plots for a specified outcome variable, allowing for comparisons across different models and subgroups defined by a facet variable. The plots are saved to a specified directory.

### Parameters  

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes combined model results and relevant variables, including a date column.                     |
| `channel`            | `str`              | Variable representing the y-axis data to be plotted.                                                                |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple lines on the plot. Default is `'modelname'`.                        |
| `facet_var`          | `str`, optional    | Variable used to create subplots based on its unique values. Default is `'ageGroup'`. (Consider updating the default)|
| `agegrp`             | `str`, optional    | Age group filter for the data. Default is `'0-100'`.                                                                  |

### Returns  

  `None`: The function saves the plots to the specified directory.  

### Usage Example  

``` 
import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'date': pd.date_range(start='2020-01-01', periods=12, freq='M'),
    'clinical_incidence': [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.35, 0.5, 0.45, 0.6, 0.55, 0.7],
    'modelname': ['Model A'] * 6 + ['Model B'] * 6,
    'ageGroup': ['0-5'] * 12
}

df = pd.DataFrame(data)

# Call the function
monthly_timeseries('path/to/save/directory', df, 'clinical_incidence')

```  


------------------ 

## `annual_timeseries`  

### Overview

The `annual_timeseries` function generates annual time series plots for a specified outcome variable, allowing for comparisons across different models and subgroups defined by a facet variable. 
The plots are saved to a specified directory.

### Parameters

| Parameter            | Type               | Description                                                                                                           |
|----------------------|--------------------|-----------------------------------------------------------------------------------------------------------------------|
| `fdir`               | `str`              | Directory where the plot will be saved.                                                                             |
| `df`                 | `pandas DataFrame` | Dataframe that includes combined model results and relevant variables.                                               |
| `channel`            | `str`              | Variable representing the y-axis data to be plotted.                                                                |
| `sweepvar`           | `str`, optional    | Variable to group the data and create multiple lines on the plot. Default is `'modelname'`.                        |
| `facet_var`          | `str`, optional    | Variable used to create subplots based on its unique values. Default is `'seasonality'`. (Update the default if needed)|
| `agegrp`             | `str`, optional    | Age group filter for the data. Default is `'0-100'`.                                                                  |

### Returns  

  `None`: The function saves the plots to the specified directory.  

### Usage Example  

``` 
import pandas as pd

# Sample DataFrame (make sure to load your actual data)
data = {
    'year': [2000, 2001, 2002, 2003, 2004],
    'clinical_incidence': [0.1, 0.2, 0.3, 0.4, 0.5],
    'modelname': ['Model A', 'Model A', 'Model B', 'Model B', 'Model A'],
    'seasonality': ['Season 1', 'Season 1', 'Season 2', 'Season 2', 'Season 1'],
    'ageGroup': ['0-5', '0-5', '5-10', '5-10', '0-5']
}

df = pd.DataFrame(data)

# Call the function
annual_timeseries('path/to/save/directory', df, 'clinical_incidence')

``` 

