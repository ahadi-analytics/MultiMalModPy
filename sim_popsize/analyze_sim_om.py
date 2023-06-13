import pickle
import os
import sys
import math
import datetime
import numpy as np
import pandas as pd
import argparse

sys.path.append('../')
from OpenMalaria.measures import mm, mmi
from OpenMalaria.sample_plots import *
from benchmark_plots import *


def parse_args():
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        help="Job Directory where exp.obj is located",
    )
    return parser.parse_args()


def to_df(exp):
    data = []
    for i in range(1, exp.nexps):
        try:
            output = pd.read_csv(os.path.join(exp.job_directory, 'txt', f'{i}.txt'), sep="\t", header=None)
            output.columns = ['survey', 'ageGroup', 'measure', 'value']
            output['index'] = i
            data.append(output)
        except Exception as e:
            print(e)
    return pd.concat(data)


def format_df(df):
    df.reset_index(drop=True, inplace=True)
    df = df.astype(dtype={
        'survey': np.int32,
        'ageGroup': np.int32,
        'measure': np.int32,
        'value': np.float64,
        'index': np.int32
    })
    df.drop(df[df.survey == 1].index, inplace=True)
    df.reset_index(inplace=True)  # drop rows with NaN
    return df


def add_measure_names(df, mm):
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]
    adf = df.merge(mm_df, on='measure', how='inner')
    return adf


def survey_to_date(df, survey_step_days=30, start_year=0):
    if survey_step_days == 30:
        df['days'] = df['survey'] * survey_step_days
        df['month'] = df['survey'] % 12
        df.loc[df['month'] == 0, 'month'] = 12
        df['year'] = (df['days'] / 365).apply(np.floor)
    elif survey_step_days == 365:
        df['year'] = df['survey']
        df['month'] = 12
    else:
        raise ValueError("survey_step_days must be 30 or 365")

    df['year'] = df['year'] + start_year
    df['date'] = df.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)

    return df


def pivot_wider(df, index_cols=None, names_from=None, values_from=None):
    if index_cols is None: index_cols = ['index', 'survey', 'ageGroup']
    if names_from is None: names_from = ['measure_name']
    if values_from is None: values_from = ['value']
    wdf = (df.pivot_table(index=index_cols,
                          columns=names_from,
                          values=values_from,
                          aggfunc='first'))
    wdf.columns = [''.join(col).replace('value', '') for col in wdf.columns]
    wdf = wdf.reset_index()
    return wdf


def InputEIRAnalyzer(exp, mm, start_year,survey_step_days=30,  compr='infer'):
    print(f"Running InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))
    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup > 0].index, inplace=True)
    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)

    df['value'] = df['value'] * (survey_step_days/ 5)
    if survey_step_days==30:
        df_mth = add_measure_names(df, mm)
        df_mth = pivot_wider(df_mth, index_cols=['index', 'survey', 'year', 'month', 'ageGroup'])
        df_mth = df_mth.merge(scen_df, on='index', how='inner')
        df_mth = df_mth.rename({'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'}, axis=1)
        df_mth.to_csv((os.path.join(wdir, f'OM_EIR_mth.csv')), index=False, compression=compr)

    # Aggregate the surveys to years
    nmonths = len(df['month'].unique())
    df_yr = df.groupby(['index', 'measure', 'ageGroup','year'], as_index=False).value.sum()
    df_yr['value'] = df_yr['value'] / nmonths
    df_yr = add_measure_names(df_yr, mm)
    df_yr = pivot_wider(df_yr, index_cols=['index', 'ageGroup','year'])
    df_yr = df_yr.merge(scen_df, on='index', how='inner')
    df_yr = df_yr.rename({'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'}, axis=1)
    print(f'Saving OM_EIR_yr.csv to {wdir}')
    df_yr.to_csv((os.path.join(wdir, f'OM_EIR_yr.csv')), index=False, compression=compr)


    # Aggregate over time
    nyears = len(df['year'].unique())
    df_aggr = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()
    df_aggr['value'] = df_aggr['value'] / nyears
    df_aggr = add_measure_names(df_aggr, mm)
    df_aggr = pivot_wider(df_aggr, index_cols=['index', 'ageGroup'])
    df_aggr = df_aggr.merge(scen_df, on='index', how='inner')
    df_aggr = df_aggr.rename({'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'}, axis=1)
    print(f'Saving OM_EIR.csv to {wdir}')
    df_aggr.to_csv((os.path.join(wdir, f'OM_EIR.csv')), index=False, compression=compr)




def BenchmarkAnalyzer(exp, mmi, grp_channels=['ageGroup', 'index'],survey_step_days=30):
    print(f"Running BenchmarkAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))
    eir_df = pd.read_csv(os.path.join(wdir, 'OM_EIR.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    age_groups = exp.agebins  # np.array([0.5,1,2,5,10,15,20,100])
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels

    df = to_df(exp)
    df = format_df(df)

    # Sum the surveys
    nsurveys = len(df['survey'].unique())
    df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()
    df.to_csv((os.path.join(wdir, f'OM_benchmark_test.csv')), index=False)
    # adjust nHost for age_groups 0 to 1
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    g = df

    age2to10 = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= 2 and age_groups[x - 1] <= 10)

    nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(grp_channels).value.sum()
    nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(grp_channels).value.sum()

    grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
    pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

    adf = pd.DataFrame()
    age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]
    for i in range(0, len(age_groups_on_plot)):
        ages = age_groups_on_plot[i]
        ageCond = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= ages[0] and age_groups[x - 1] <= ages[1])

        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'

        nClinicalCases = 0
        for m in ['nUncomp']:
            nClinicalCases += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

        nSevereCases = 0
        for m in ['nSevere']:
            nSevereCases += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

        nDeaths = 0
        for m in ['expectedDirectDeaths', 'expectedIndirectDeaths']:
            nDeaths += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

        nHost = g[(g.measure == mmi['nHost']) & ageCond].groupby(grp_channels).value.sum()
        
        d = math.floor(365/survey_step_days)
        clinical_incidence = nClinicalCases / (nHost / d)  # (events per person per year)
        severe_incidence = nSevereCases / (nHost / d)  # (events per person per year)
        mortality = nDeaths / (nHost / d)  # (events per person per year)

        simdata = pd.DataFrame({'prevalence_2to10': pfpr2to10,
                                'clinical_incidence': clinical_incidence,
                                'severe_incidence': severe_incidence,
                                'mortality': mortality})
        simdata['age_group'] = ageCond_labels
        adf = pd.concat([adf, simdata])

    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on='index', how='inner')

    print(f'Saving OM_benchmark.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_benchmark.csv')), index=False)

def AnnualBenchmarkAnalyzer(exp, mmi, start_year, grp_channels=['ageGroup', 'index'], survey_step_days =30):
    print(f"Running AnnualBenchmarkAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))
    eir_df = pd.read_csv(os.path.join(wdir, 'OM_EIR.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    age_groups = exp.agebins  # np.array([0.5,1,2,5,10,15,20,100])
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels

    df = to_df(exp)
    df = format_df(df)
    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)

    # Sum the surveys
    df = df.groupby(['index','year', 'measure', 'ageGroup'], as_index=False).value.sum()

    # adjust nHost for age_groups 0 to 1
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1

    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]

    adf = pd.DataFrame()
    for yr in df['year'].unique():
        g = df.loc[df['year'] == yr]

        age2to10 = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= 2 and age_groups[x - 1] <= 10)
    
        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(grp_channels).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(grp_channels).value.sum()
    
        grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
        pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")
    
        adf = pd.DataFrame()
        age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]
        for i in range(0, len(age_groups_on_plot)):
            ages = age_groups_on_plot[i]
            ageCond = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= ages[0] and age_groups[x - 1] <= ages[1])
    
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
    
            nClinicalCases = 0
            for m in ['nUncomp']:
                nClinicalCases += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()
    
            nSevereCases = 0
            for m in ['nSevere']:
                nSevereCases += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()
    
            nDeaths = 0
            for m in ['expectedDirectDeaths', 'expectedIndirectDeaths']:
                nDeaths += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()
    
            nHost = g[(g.measure == mmi['nHost']) & ageCond].groupby(grp_channels).value.sum()
    
            d = math.floor(365/survey_step_days)
            clinical_incidence = nClinicalCases / (nHost / d)  # (events per person per year)
            severe_incidence = nSevereCases / (nHost / d)  # (events per person per year)
            mortality = nDeaths / (nHost / d)  # (events per person per year)
    
            simdata = pd.DataFrame({'prevalence_2to10': pfpr2to10,
                                    'clinical_incidence': clinical_incidence,
                                    'severe_incidence': severe_incidence,
                                    'mortality': mortality})
            simdata['age_group'] = ageCond_labels
            adf = pd.concat([adf, simdata])

    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on='index', how='inner')

    print(f'Saving OM_benchmark_yr.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_benchmark_yr.csv')), index=False)

def AnnualAgebinAnalyzer(exp, mm, start_year, survey_step_days=365, compr='infer'):
    print(f"Running AnnualAgebinAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)

    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)
    if survey_step_days ==30:
        df = df.groupby(['index','ageGroup', 'year', 'measure'], as_index=False).value.sum()
        df = df.loc[df['year']< np.max(df.year) ]
    elif survey_step_days ==365:
        df = df.groupby(['index','ageGroup', 'year', 'measure'], as_index=False).value.mean()
    else: 
        raise ValueError('survey_step_days must be 30 or 365')  
        
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    adf = df.merge(mm_df, on='measure', how='inner')
    df1 = (adf.pivot_table(index=['index', 'year', 'ageGroup'],
                           columns=['measure_name'],
                           values=['value'],
                           aggfunc='first'))
    df1.columns = [''.join(col).replace('value', '') for col in df1.columns]
    df1 = df1.reset_index()

    df2 = df1.merge(scen_df, on='index', how='inner')
    df2 = df2.rename({'ageGroup': 'agebin_nr'}, axis=1)

    age_groups = exp.agebins  # must reflect the xml monitoring section
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels
    age_df = pd.DataFrame({'agebin_nr': df2['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    df3 = df2.merge(age_df, on='agebin_nr', how='inner')

    print(f'Saving OM_surveyoutput_yr to {wdir}')
    df3.to_csv((os.path.join(wdir, f'OM_surveyoutput_yr.csv')), index=False, compression=compr)


if __name__ == "__main__":
    args = parse_args()
    job_directory = args.directory

    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    start_year = exp.sim_start_year
    wdir = os.path.join(exp.sim_out_dir, 'om')
    create_sampleplots = True
    if exp.om_survey_step == '30d':
        survey_steps =30
    if exp.om_survey_step == '1y':
        survey_steps =365
    

    #InputEIRAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)
    BenchmarkAnalyzer(exp, mmi, survey_step_days=survey_steps)
    AnnualBenchmarkAnalyzer(exp, mmi, start_year=start_year, survey_step_days=survey_steps)
    AnnualAgebinAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)
    
    exp_tags = ['seed', 'eir', 'access', 'seasonality']  # FIXME dont hardcode
    channels_inset_chart = ['nHost', 'nInfect', 'nPatent', 'totalInfs', 'totalPatentInf', 'nTreatments', 'nUncomp',
                            'nSevere', 'nSeq', 'nIndDeaths',
                            'nDirDeaths', 'inputEIR', 'simulatedEIR', 'expectedDirectDeaths',
                            'expectedSevere']  # 'expectedIndirectDeaths',

    if create_sampleplots:
        sample_plot_yr(wdir, exp_tags)

