# Postprocessing explained

## OpenMalaria

**Timesteps**

```python   
    # Determine survey step size
if exp.openmalaria_survey_step == '5d':
    survey_steps = 5
if exp.openmalaria_survey_step == '30d':
    survey_steps = 30
if exp.openmalaria_survey_step == '1y':
    survey_steps = 365
```  

### Annual analyzer

[survey-measures](https://github.com/SwissTPH/openmalaria/wiki/MonitoringOptions#survey-measures)
nHost: 	Total number of humans
nPatent: The number of human hosts whose total (blood-stage) parasite density is above the detection threshold
nUncomp: 	number of episodes (uncomplicated) [...detailed description on the Wiki]

**Step 1**: Combine output from TXT files into a CSV file and add day-month-year columns

```python 
    df = to_df(exp)
df = format_df(df)
df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)
```

| level_0 | survey | ageGroup | measure | value | index | days | month | year |
|---------|--------|----------|---------|-------|-------|------|-------|------|
| 191     | 1      | 1        | 0       | 31    | 1     | 5    | 1     | 2000 |
| 192     | 1      | 2        | 0       | 18    | 1     | 5    | 1     | 2000 |
| 193     | 1      | 3        | 0       | 28    | 1     | 5    | 1     | 2000 |
| 194     | 1      | 4        | 0       | 80    | 1     | 5    | 1     | 2000 |
| 195     | 1      | 5        | 0       | 124   | 1     | 5    | 1     | 2000 |
| 196     | 1      | 6        | 0       | 123   | 1     | 5    | 1     | 2000 |
| 197     | 1      | 7        | 0       | 99    | 1     | 5    | 1     | 2000 |
| 198     | 1      | 8        | 0       | 497   | 1     | 5    | 1     | 2000 |
| 382     | 2      | 1        | 0       | 31    | 1     | 10   | 1     | 2000 |
| 383     | 2      | 2        | 0       | 18    | 1     | 10   | 1     | 2000 |
| 384     | 2      | 3        | 0       | 29    | 1     | 10   | 1     | 2000 |
| 385     | 2      | 4        | 0       | 80    | 1     | 10   | 1     | 2000 |
| 386     | 2      | 5        | 0       | 124   | 1     | 10   | 1     | 2000 |
| 387     | 2      | 6        | 0       | 122   | 1     | 10   | 1     | 2000 |
| 388     | 2      | 7        | 0       | 99    | 1     | 10   | 1     | 2000 |
| 389     | 2      | 8        | 0       | 497   | 1     | 10   | 1     | 2000 |

**Step 2**: Values per survey are summed per ageGroup, measure and index and for nHost (measure='0') and nPatent (
measure='3') the value is divided by the annual number of surveysteps.
If running with 5 day surveysteps, that is 73

```python 
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year
df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year
```

**nHost**
In this example, the total population the simulation was run with, was 1000 individuals.

| index | year | measure | ageGroup | value | value /73 |
|-------|------|---------|----------|-------|-----------|
| 1     | 2000 | 0       | 1        | 2154  | 30        |
| 1     | 2000 | 0       | 2        | 1259  | 17        |
| 1     | 2000 | 0       | 3        | 2413  | 33        |
| 1     | 2000 | 0       | 4        | 5814  | 80        |
| 1     | 2000 | 0       | 5        | 9178  | 126       |
| 1     | 2000 | 0       | 6        | 8695  | 119       |
| 1     | 2000 | 0       | 7        | 7536  | 103       |
| 1     | 2000 | 0       | 8        | 35951 | 492       |

**nPatent**

| index | year | measure | ageGroup | value | value /73 |
|-------|------|---------|----------|-------|-----------|
| 1     | 2000 | 3       | 1        | 176   | 2.4       |
| 1     | 2000 | 3       | 2        | 321   | 4.4       |
| 1     | 2000 | 3       | 3        | 584   | 8.0       |
| 1     | 2000 | 3       | 4        | 1604  | 22.0      |
| 1     | 2000 | 3       | 5        | 2933  | 40.2      |
| 1     | 2000 | 3       | 6        | 3411  | 46.7      |
| 1     | 2000 | 3       | 7        | 3085  | 42.3      |
| 1     | 2000 | 3       | 8        | 15907 | 217.9     |

**Step 3**: For each year the 1) 2to10 age group measures are obtained and 2) other age groups aggregated

```python 
age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5], [0, 100]]
age_bins = [0.5, 1, 2, 5, 10, 15, 20, 100]
grp_channels = ['ageGroup', 'index']
```

**Step 3.1:**

```python 
    age2to10 = g['ageGroup'].apply(lambda x: age_bins[x - 1] > 2 and age_bins[x - 1] <= 10)
    nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['index']).value.sum()
    nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['index']).value.sum()
    grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
    pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")
```

**Step 3.2:**

```python 

for i in range(0, len(age_groups_aggregates)):
    ages = age_groups_aggregates[i]
    ageCond = g['ageGroup'].apply(lambda x: age_bins[x - 1] > ages[0] and age_bins[x - 1] <= ages[1])
    ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
```

_Example_

```text 
ages = [1, 2]
ageCond_labels='1-2'
```

```python 

# Compute various measures for the current age group
nPatentInfections = 0
for m in ['nPatent']:
    nPatentInfections += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

nClinicalCases = 0
for m in ['nUncomp']:
    nClinicalCases += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

nHost = g[(g.measure == mmi['nHost']) & ageCond].groupby(grp_channels).value.sum()
```  

_Example nHost,nPatent and nUncomp_

| index | year | ageGroup | nHost    | nPatentInfections | nClinicalCases |
|-------|------|----------|----------|-------------------|----------------|
| 1     | 2000 | 3        | 33.05479 | 8                 | 60             |
| 2     | 2000 | 3        | 31.82192 | 4.575342          | 38             |
| 3     | 2000 | 3        | 31.31507 | 5.808219          | 53             |
| 4     | 2000 | 3        | 30.9589  | 3.013699          | 32             |
| 5     | 2000 | 3        | 27.63014 | 5.342466          | 43             |
| 6     | 2000 | 3        | 28.76712 | 4.726027          | 39             |
| 7     | 2000 | 3        | 28.27397 | 12.65753          | 91             |
| 8     | 2000 | 3        | 32.13699 | 16.76712          | 106            |
| 9     | 2000 | 3        | 34.21918 | 12.52055          | 90             |
| 10    | 2000 | 3        | 30.12329 | 13.26027          | 96             |
| 11    | 2000 | 3        | 31.24658 | 12.24658          | 122            |
| 12    | 2000 | 3        | 29.52055 | 10.61644          | 95             |

Since a single age_bin falls under the selected age_group_aggregate , the same values appear as shown in the `value`
column above

```
 prevalence = nPatentInfections / nHost
 clinical_incidence = nClinicalCases / nHost
```


