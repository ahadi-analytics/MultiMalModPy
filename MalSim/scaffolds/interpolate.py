import numpy as np
import pandas as pd

def input_target_to_eir(df=None, input_type = None, seasonality = None):   
    output=[]
    if input_type == 'pfpr':
        if 'seasonal' in seasonality:
            #only works on CM 45
            data = pd.read_csv('/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240628/sims_dynamic_seasonal__14_52_12/MalSim/PfPR_ClinicalIncidence_yr.csv')
        if 'perennial' in seasonality:
            print("need to input pfpr perennial data")
        for i, row in df.iterrows():
            idata = data[((data['cm_clinical'] == row['cm_clinical']) & (data['seasonality'] == row['seasonality']))]
            idata = idata.groupby(['eir'])['prevalence_2to10'].agg(np.mean).reset_index()
            xt = idata['prevalence_2to10']
            yp = idata['eir']
            xnew = row['input_target']
            eir = np.interp(xnew, xt, yp)
            output.append(eir)
    elif input_type == 'eir':
        if 'seasonal' in seasonality:
            #only works on CM 45
            data = pd.read_csv('/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240628/sims_dynamic_seasonal__14_52_12/MalSim/PfPR_ClinicalIncidence_yr.csv')
        if 'perennial' in seasonality:
            print("need to input pfpr perennial data")
        for i, row in df.iterrows():
            idata = data[((data['cm_clinical'] == row['cm_clinical']) & (data['seasonality'] == row['seasonality']))]
            idata = idata.groupby(['eir'])['prevalence_2to10'].agg(np.mean).reset_index()
            xt = idata['prevalence_2to10']
            yp = idata['eir']
            xnew = row['input_target']
            eir = np.interp(xnew, xt, yp)
            output.append(eir)
    return output