import json
import pandas as pd
import numpy as np

f = open('EMOD/inputs/production_run/SSAfrica_demographics.json')
data = json.load(f)
f.close()

DistributionValues = data['Defaults']['IndividualAttributes']['AgeDistribution']['DistributionValues'][0]
ResultValues = data['Defaults']['IndividualAttributes']['AgeDistribution']['ResultValues'][0]

data = pd.DataFrame({'age_d': ResultValues, 'perc_cum': DistributionValues})
data['age_y'] = data['age_d'] / 365
data = data.sort_values(by='age_d')
data['perc'] = data['perc_cum'] - data['perc_cum'].shift(1)
data['age_y_round'] = round(data['age_y'], 0)


## Alignment to EMOD for production run
ages_EMOD = [round(y,0) for y in data['age_y']]
ages_openmalaria =             [0, 2,  5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100, 110, 120]
ages_malariasimulation = [0.083333, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120]
ages_aggregates = [0, 5, 10, 15, 20, 120]
data['age_group_openmalaria'] = pd.cut(data['age_y_round'], bins=ages_openmalaria)
data['age_group_malariasimulation'] = pd.cut(data['age_y_round'], bins=ages_malariasimulation)
data['age_group_emod'] = pd.cut(data['age_y_round'], bins=ages_malariasimulation)
data['age_group_aggregates'] = pd.cut(data['age_y_round'], bins=ages_aggregates)

data.to_csv('scenario_inputs/age_demographics.csv')

data2 = data.groupby('age_group_malariasimulation')['perc'].agg(np.sum).reset_index()
data3 = data.groupby('age_group_openmalaria')['perc'].agg(np.sum).reset_index()

data2['age_malariasimulation_upper'] = data2['age_group_malariasimulation'].astype(str).str.split(',').str[1].str.strip(')').str.strip(']')
data3['age_openmalaria_upper'] = data3['age_group_openmalaria'].astype(str).str.split(',').str[1].str.strip(')').str.strip(']').astype(
    int)

om_U1_perc = 3.474714994 / 100
data3.loc[data3['age_openmalaria_upper'] == 1, 'perc'] = om_U1_perc
data3.loc[data3['age_openmalaria_upper'] == 5, 'perc'] -= om_U1_perc

## Write snippet for Openmalaria
for index, row in data3.iterrows():
    xml_string = f'<group poppercent="{round(row["perc"] * 100, 9)}" upperbound="{row["age_openmalaria_upper"]}"/>'
    print(xml_string)

### Write age mortality for malariasimulation
### TODO: this requires simulation in R for malariasimulations