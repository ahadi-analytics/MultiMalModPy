import argparse
import pickle
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

from plotter.plot_helper import *


# Calculates ANOVA scores for each output variable, requires Benchmark.csv
def anovas(fdir, df):
    """
    Calculates ANOVA scores for each output variable, seperated by age group and all ages.
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
    Returns:
        None (ANOVA values are saved to disk).
    """
    from scipy.stats import f_oneway
    comparisons = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'simulatedEIR']
    emod = df[df['modelname'] == 'EMOD']
    malsim = df[df['modelname'] == 'malariasimulation']
    openmalaria = df[df['modelname'] == 'OpenMalaria']

    anova_df = pd.DataFrame(columns=['Age Group', 'Objective', 'F_value', 'p_value', 'null_hyp'])

    # As a whole
    for com in comparisons:
        performance_emod = emod[com]
        performance_malariasimulation = malsim[com]
        performance_openmalaria = openmalaria[com]
        f_value, p_value = f_oneway(performance_emod, performance_malariasimulation, performance_openmalaria)
        if p_value <= 0.05:
            null_hyp = True
        else:
            null_hyp = False
        new_row = {'Age Group': 'Across All Ages', 'Objective': com, 'F_value': f_value, 'p_value': p_value,
                   'null_hyp': null_hyp}
        anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)

    # By Age Group
    for age in df['ageGroup'].unique():
        em = emod[emod['ageGroup'] == age]
        ms = malsim[malsim['ageGroup'] == age]
        om = openmalaria[openmalaria['ageGroup'] == age]
        for com in comparisons:
            performance_emod = em[com]
            performance_malariasimulation = ms[com]
            performance_openmalaria = om[com]
            f_value, p_value = f_oneway(performance_emod, performance_malariasimulation, performance_openmalaria)
            if p_value <= 0.05:
                null_hyp = True
            else:
                null_hyp = False
            new_row = {'Age Group': age, 'Objective': com, 'F_value': f_value, 'p_value': p_value, 'null_hyp': null_hyp}
            anova_df = pd.concat([anova_df, pd.DataFrame([new_row])], ignore_index=True)

    anova_df.to_csv(os.path.join(fdir, 'anovas.csv'), index=False)


# Calculates RMSE values for each output variable
def rmse(fdir, df):
    """
    Calculates RMSE scores for each output variable (comparing against each model individually), seperated by age group and all ages.
    Parameters:
        fdir (str): Directory where the plot will be saved.
        df (pandas dataframe): Dataframe that includes combined model results.
    Returns:
        None (RMSE scores are saved to disk).
    """
    from sklearn.metrics import mean_squared_error
    from math import sqrt

    rmse_vars = ['prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'simulatedEIR']

    rmse_df = pd.DataFrame(
        columns=['Age Group', 'Variable', 'EMOD_TO_OPENMALARIA', 'OPENMALARIA_TO_MALARIASIMULATION',
                 'EMOD_TO_MALARIASIMULATION'])

    for rmse_var in rmse_vars:
        group_data = df.groupby(['modelname'])[rmse_var].agg(['mean']).reset_index()
        emod_data = group_data[group_data['modelname'] == 'EMOD']
        malsim_data = group_data[group_data['modelname'] == 'malariasimulation']
        om_data = group_data[group_data['modelname'] == 'OpenMalaria']
        # RMSE Between EMOD and OM
        rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
        # RMSE Between OM AND malariasimulation
        rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
        # RMSE Between EMOD and malariasimulation
        rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
        # RMSE Concat
        new_row = {'Age Group': 'Across All Ages', 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo,
                   'OPENMALARIA_TO_MALARIASIMULATION': rmse_om, 'EMOD_TO_MALARIASIMULATION': rmse_em}
        rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index=True)

    for age in df['ageGroup'].unique():
        adf = df[df['ageGroup'] == age]
        for rmse_var in rmse_vars:
            group_data = adf.groupby(['modelname'])[rmse_var].agg(['mean']).reset_index()
            emod_data = group_data[group_data['modelname'] == 'EMOD']
            malsim_data = group_data[group_data['modelname'] == 'malariasimulation']
            om_data = group_data[group_data['modelname'] == 'OpenMalaria']
            # RMSE Between EMOD and OM
            rmse_eo = sqrt(mean_squared_error(emod_data['mean'], om_data['mean']))
            # RMSE Between OM AND malariasimulation
            rmse_om = sqrt(mean_squared_error(malsim_data['mean'], om_data['mean']))
            # RMSE Between EMOD and malariasimulation
            rmse_em = sqrt(mean_squared_error(emod_data['mean'], malsim_data['mean']))
            # RMSE DF
            new_row = {'Age Group': age, 'Variable': rmse_var, 'EMOD_TO_OPENMALARIA': rmse_eo,
                       'OPENMALARIA_TO_MALARIASIMULATION': rmse_om, 'EMOD_TO_MALARIASIMULATION': rmse_em}
            rmse_df = pd.concat([rmse_df, pd.DataFrame([new_row])], ignore_index=True)
    rmse_df.to_csv(os.path.join(fdir, 'rmse.csv'), index=False)


if __name__ == "__main__":
    args = parse_args()
    wdir = args.directory
    modelname = args.modelname
    if isinstance(modelname, str):
        modelname = [modelname]
    file = open(os.path.join(wdir, "exp.obj"), "rb")
    exp = pickle.load(file)

    df, out_dir = get_output_df(wdir, modelname)
    out_dir = os.path.join(out_dir, 'plots')
    os.makedirs(out_dir, exist_ok=True)

    if len(modelname) == 3:
        print('#----- Calculating RMSE Values and ANOVAs -----#')
        rmse(out_dir, modelname)
        anovas(out_dir, modelname)
