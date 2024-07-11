import numpy as np
import pandas as pd

def gather_interpolate_data(input_type = None, seasonality = None):
    if input_type == 'pfpr':
        if 'seasonal' in seasonality:
            #only works on CM 45
            data = pd.read_csv('/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240628/sims_dynamic_seasonal__14_52_12/om/PfPR_ClinicalIncidence_yr.csv')
        if 'perennial' in seasonality:
            print("need to input pfpr perennial data")
    elif input_type == 'eir':
        if 'seasonal' in seasonality:
            print("need to input eir seasonal data")
        if 'perennial' in seasonality:
            print("need to input eir perennial data")
    return data

def input_target_to_eir(idata = None, row=None, input_type = None):       
    if input_type == 'pfpr':
        idata = idata[((idata['cm_clinical'] == row['cm_clinical']) & (idata['seasonality'] == row['seasonality']))]
        idata = idata.groupby(['eir'])['prevalence_2to10'].agg(np.mean).reset_index()
        xt = idata['prevalence_2to10']
        yp = idata['eir']
        xnew = row['input_target']
        eir = np.interp(xnew, xt, yp)
    elif input_type == 'eir':
        idata = idata[((idata['cm_clinical'] == row['cm_clinical']) & (idata['seasonality'] == row['seasonality']))]
        idata = idata.groupby(['eir'])['simulatedEIR'].agg(np.mean).reset_index()
        xt = idata['simulatedEIR']
        yp = idata['eir']
        xnew = row['input_target']
        eir = np.interp(xnew, xt, yp)       
    return eir