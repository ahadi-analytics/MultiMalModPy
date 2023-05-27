import pickle
import os
import sys
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
    nyears = len(df['year'].unique())
    df_yr = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()
    df_yr['value'] = df_yr['value'] / nyears
    df_yr = add_measure_names(df_yr, mm)
    df_yr = pivot_wider(df_yr, index_cols=['index', 'ageGroup'])
    df_yr = df_yr.merge(scen_df, on='index', how='inner')
    df_yr = df_yr.rename({'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'}, axis=1)
    print(f'Saving OM_EIR.csv to {wdir}')
    df_yr.to_csv((os.path.join(wdir, f'OM_EIR.csv')), index=False, compression=compr)


def BaseAnalyzer(exp, mm, saveExtract=False, compr='gzip'):
    print(f"Running BaseAnalyzer...", flush=True)

    df = to_df(exp)
    if saveExtract:
        df.to_csv((os.path.join(wdir, f'OM_surveyoutput_raw.csv')), index=False, compression=compr)

    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)

    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    adf = df.merge(mm_df, on='measure', how='inner')
    adf = adf.rename({'ageGroup': 'agebin_nr'}, axis=1)

    age_groups = exp.agebins
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels
    age_df = pd.DataFrame({'agebin_nr': adf['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    adf = adf.merge(age_df, on='agebin_nr', how='inner')
    print(f'Saving OM_surveyoutput_base.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_surveyoutput_base.csv')), index=False, compression=compr)


def SurveyAllAgeAnalyzer(exp, mm, start_year=2020, survey_step_days=30, compr='infer'):
    print(f"Running SurveyAllAgeAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    df = to_df(exp)
    df = format_df(df)

    df0 = df.loc[df.ageGroup == 0]
    df0.drop(['ageGroup'], axis=1)
    df0['value'] = df0['value']  * (survey_step_days/ 5)
    
    df.drop(df[df.ageGroup == 0].index, inplace=True)
    
    # Sum the age groups
    df = df.groupby(['index', 'survey', 'measure'], as_index=False).value.sum()

    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    df0 = df0.merge(mm_df, on='measure', how='inner')
    df0 = pivot_wider(df0, index_cols=['index', 'survey'])

    adf = df.merge(mm_df, on='measure', how='inner')
    adf = pivot_wider(adf, index_cols=['index', 'survey'])

    adf = adf.merge(df0, on=['index', 'survey'], how='inner')
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.rename({'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'}, axis=1)
    adf['nTreatments'] = adf['nTreatments1'] + adf['nTreatments2'] + adf['nTreatments3']
    adf = survey_to_date(adf, survey_step_days=survey_step_days, start_year=start_year)

    print(f'Saving All_Age_InsetChart.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'All_Age_InsetChart.csv')), index=False, compression=compr)


def BenchmarkAnalyzer(exp, mmi, grp_channels=['ageGroup', 'index']):
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
    df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()

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

        clinical_incidence = nClinicalCases / (nHost / 12)  # (events per person per year)
        severe_incidence = nSevereCases / (nHost / 12)  # (events per person per year)
        mortality = nDeaths / (nHost / 12)  # (events per person per year)

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


def MonthlyBenchmarkAnalyzer(exp, mmi, start_year, grp_channels=['ageGroup', 'index']):
    print(f"Running MonthlyBenchmarkAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))
    eir_df = pd.read_csv(os.path.join(wdir, 'OM_EIR_mth.csv'))
    eir_df = eir_df.groupby(['index', 'month'], as_index=False)['inputEIR', 'simulatedEIR'].mean()

    age_groups = exp.agebins  # np.array([0.5,1,2,5,10,15,20,100])
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels

    df = to_df(exp)
    df = format_df(df)
    df = survey_to_date(df, survey_step_days=30, start_year=start_year)

    # Sum the surveys
    df = df.groupby(['index', 'month', 'measure', 'ageGroup'], as_index=False).value.sum()

    # adjust nHost for age_groups 0 to 1
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1

    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    sdf = df

    adf = pd.DataFrame()
    for mth in range(1, 13):
        g = sdf.loc[sdf['month'] == mth]

        age2to10 = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= 2 and age_groups[x - 1] <= 10)

        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(grp_channels).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(grp_channels).value.sum()

        grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
        pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

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

            clinical_incidence = nClinicalCases / (nHost / 12)  # (events per person per year) - for each month
            severe_incidence = nSevereCases / (nHost / 12)  # (events per person per year) - for each month
            mortality = nDeaths / (nHost / 12)  # (events per person per year)- for each month

            simdata = pd.DataFrame({'prevalence_2to10': pfpr2to10,
                                    'clinical_incidence': clinical_incidence,
                                    'severe_incidence': severe_incidence,
                                    'mortality': mortality})
            simdata['age_group'] = ageCond_labels
            simdata['month'] = mth
            adf = pd.concat([adf, simdata])

    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on=['index', 'month'], how='inner')

    print(f'Saving OM_benchmark_mth.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_benchmark_mth.csv')), index=False)


def MonthlyAgebinAnalyzer(exp, mm, start_year, compr='infer'):
    print(f"Running MonthlyAgebinAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)

    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    adf = df.merge(mm_df, on='measure', how='inner')
    df1 = (adf.pivot_table(index=['index', 'survey', 'ageGroup'],
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
    df3 = survey_to_date(df3, survey_step_days=30, start_year=start_year)

    print(f'Saving OM_surveyoutput_mth.csv to {wdir}')
    df3.to_csv((os.path.join(wdir, f'OM_surveyoutput_mth.csv')), index=False, compression=compr)


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
    
    # BaseAnalyzer(exp, mm)
    SurveyAllAgeAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)
    InputEIRAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)
    if survey_steps == 30:
        MonthlyAgebinAnalyzer(exp, mm, start_year=start_year)
        MonthlyBenchmarkAnalyzer(exp, mmi, start_year=start_year)
        BenchmarkAnalyzer(exp, mmi)
    AnnualAgebinAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)
    
    exp_tags = ['seed', 'eir', 'access', 'seasonality']  # FIXME dont hardcode
    channels_inset_chart = ['nHost', 'nInfect', 'nPatent', 'totalInfs', 'totalPatentInf', 'nTreatments', 'nUncomp',
                            'nSevere', 'nSeq', 'nIndDeaths',
                            'nDirDeaths', 'inputEIR', 'simulatedEIR', 'expectedDirectDeaths',
                            'expectedSevere']  # 'expectedIndirectDeaths',

    if create_sampleplots:
        all_age_sample_plot(wdir, exp_tags, channels_inset_chart, survey_steps=survey_steps)
        sample_plot_yr(wdir, exp_tags)
        if survey_steps ==30:
            sample_plot_mth(wdir, exp_tags)
        # eir_to_prevalence2to10(wdir= exp.sim_out_dir, emodom=['OpenMalaria'], sweepvar ='access')
