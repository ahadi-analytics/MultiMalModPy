# analyzer.py

## `parse_args`

```python
def parse_args():
    """
    Parses command-line arguments for simulation specifications.
    """
```

Description
This function parses command-line arguments that specify the configuration for running simulations.

Arguments
-d, --directory (str, required):
The directory where the exp.obj file is located. This is a required argument.

-i, --exp_id (str, optional):
A unique ID for the simulation experiment. This argument is required for EMOD runs. The default value is None.

Returns
Namespace:
An object containing the parsed arguments.

Example
```python
args = parse_args()
print(args.directory)
print(args.exp_id)
```

## `InsetChartAnalyzer`

```python
class InsetChartAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    """
```

**Description**  
InsetChartAnalyzer is used to analyze the inset chart report output specific to the EMOD simulation framework.

**Parameters**  
`expt_name` (str):  
The name of the experiment.

`sweep_variables` (list, optional):  
List of variables that were swept in the experiment. Defaults to ["Run_Number"].  

`channels` (list, optional):  
List of channels to analyze in the inset chart. Defaults to common simulation outputs such as ['Statistical Population', 'Births', 'Disease Deaths', ...].

`daily` (bool, optional):  
Whether to analyze the data on a daily basis. Defaults to False.  

`working_dir` (str, optional):    
Directory where analysis results are saved. Defaults to "./".  

`start_year` (int, optional):  
The starting year of the simulation. Defaults to 2022.  

`burnin` (None or int, optional):
The number of years to exclude from the results (burn-in period). Defaults to None.




## `InputEIRAnalyzer`

```python
class InputEIRAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    """
```

**Description**  
InputEIRAnalyzer  ...

**Parameters**  
`expt_name` (str):  
The name of the experiment.

`sweep_variables` (list, optional):  
List of variables that were swept in the experiment. Defaults to ["Run_Number"].  

`channels` (list, optional):  
List of channels to analyze in the inset chart. Defaults to common simulation outputs such as ['Statistical Population', 'Births', 'Disease Deaths', ...].

`daily` (bool, optional):  
Whether to analyze the data on a daily basis. Defaults to False.  

`working_dir` (str, optional):    
Directory where analysis results are saved. Defaults to "./".  

`start_year` (int, optional):  
The starting year of the simulation. Defaults to 2022.  

`burnin` (None or int, optional):
The number of years to exclude from the results (burn-in period). Defaults to None.




## `BenchmarkAnalyzer`

```python
class BenchmarkAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    """
```

**Description**  
BenchmarkAnalyzer  ...

**Parameters**  
`expt_name` (str):  
The name of the experiment.

`sweep_variables` (list, optional):  
List of variables that were swept in the experiment. Defaults to ["Run_Number"].  

`channels` (list, optional):  
List of channels to analyze in the inset chart. Defaults to common simulation outputs such as ['Statistical Population', 'Births', 'Disease Deaths', ...].

`daily` (bool, optional):  
Whether to analyze the data on a daily basis. Defaults to False.  

`working_dir` (str, optional):    
Directory where analysis results are saved. Defaults to "./".  

`start_year` (int, optional):  
The starting year of the simulation. Defaults to 2022.  

`burnin` (None or int, optional):
The number of years to exclude from the results (burn-in period). Defaults to None.



## `DailyAgeBinAnalyzer`

```python
class DailyAgeBinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    """
```

**Description**  
DailyAgeBinAnalyzer  ...

**Parameters**  
`expt_name` (str):  
The name of the experiment.

`sweep_variables` (list, optional):  
List of variables that were swept in the experiment. Defaults to ["Run_Number"].  

`channels` (list, optional):  
List of channels to analyze in the inset chart. Defaults to common simulation outputs such as ['Statistical Population', 'Births', 'Disease Deaths', ...].

`daily` (bool, optional):  
Whether to analyze the data on a daily basis. Defaults to False.  

`working_dir` (str, optional):    
Directory where analysis results are saved. Defaults to "./".  

`start_year` (int, optional):  
The starting year of the simulation. Defaults to 2022.  

`burnin` (None or int, optional):
The number of years to exclude from the results (burn-in period). Defaults to None.



## `FiveDayAgeBinAnalyzer`

```python
class FiveDayAgeBinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    """
```

**Description**  
FiveDayAgeBinAnalyzer  ...

**Parameters**  
`expt_name` (str):  
The name of the experiment.

`sweep_variables` (list, optional):  
List of variables that were swept in the experiment. Defaults to ["Run_Number"].  

`channels` (list, optional):  
List of channels to analyze in the inset chart. Defaults to common simulation outputs such as ['Statistical Population', 'Births', 'Disease Deaths', ...].

`daily` (bool, optional):  
Whether to analyze the data on a daily basis. Defaults to False.  

`working_dir` (str, optional):    
Directory where analysis results are saved. Defaults to "./".  

`start_year` (int, optional):  
The starting year of the simulation. Defaults to 2022.  

`burnin` (None or int, optional):
The number of years to exclude from the results (burn-in period). Defaults to None.



## `MonthlyAgeBinAnalyzer`

```python
class MonthlyAgeBinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    """
```

**Description**  
MonthlyAgeBinAnalyzer  ...

**Parameters**  
`expt_name` (str):  
The name of the experiment.

`sweep_variables` (list, optional):  
List of variables that were swept in the experiment. Defaults to ["Run_Number"].  

`channels` (list, optional):  
List of channels to analyze in the inset chart. Defaults to common simulation outputs such as ['Statistical Population', 'Births', 'Disease Deaths', ...].

`daily` (bool, optional):  
Whether to analyze the data on a daily basis. Defaults to False.  

`working_dir` (str, optional):    
Directory where analysis results are saved. Defaults to "./".  

`start_year` (int, optional):  
The starting year of the simulation. Defaults to 2022.  

`burnin` (None or int, optional):
The number of years to exclude from the results (burn-in period). Defaults to None.



## `AnnualAgeBinAnalyzer`

```python
class AnnualAgeBinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    """
```

**Description**  
MonthlyAgeBinAnalyzer  ...

**Parameters**  
`expt_name` (str):  
The name of the experiment.

`sweep_variables` (list, optional):  
List of variables that were swept in the experiment. Defaults to ["Run_Number"].  

`channels` (list, optional):  
List of channels to analyze in the inset chart. Defaults to common simulation outputs such as ['Statistical Population', 'Births', 'Disease Deaths', ...].

`daily` (bool, optional):  
Whether to analyze the data on a daily basis. Defaults to False.  

`working_dir` (str, optional):    
Directory where analysis results are saved. Defaults to "./".  

`start_year` (int, optional):  
The starting year of the simulation. Defaults to 2022.  

`burnin` (None or int, optional):
The number of years to exclude from the results (burn-in period). Defaults to None.








