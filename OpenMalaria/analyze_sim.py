import pickle
import sys

## For plotting
sys.path.append('../')
from helper import parse_args
from benchmark_plots import *


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


# def aggregate_surveys():

def InputEIRAnalyzer(exp, mm, saveExtract=False):
    print(f"Running InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup > 0].index, inplace=True)
    if saveExtract:
        df.to_csv((os.path.join(wdir, f'OM_EIR_raw.csv')), index=False, compression='gzip')

    adf = add_measure_names(df, mm)
    df1 = pivot_wider(adf)

    df2 = df1.merge(scen_df, on='index', how='inner')
    df2.to_csv((os.path.join(wdir, f'OM_EIR_surveys.csv')), index=False, compression='gzip')

    # Aggregare the surveys
    df3 = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()
    df3 = add_measure_names(df3, mm)
    df3 = pivot_wider(df3, index_cols=['index', 'ageGroup'])
    df3 = df3.merge(scen_df, on='index', how='inner')
    print(f'Saving OM_EIR.csv to {wdir}')
    df3.to_csv((os.path.join(wdir, f'OM_EIR.csv')), index=False, compression='gzip')


def BaseAnalyzer(exp, mm, channels=None, saveExtract=False):
    print(f"Running BaseAnalyzer...", flush=True)

    df = to_df(exp)
    if saveExtract:
        df.to_csv((os.path.join(wdir, f'OM_surveyoutput_raw.csv')), index=False, compression='gzip')

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
    age_df = pd.DataFrame({'agebin_nr': df2['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    adf = adf.merge(age_df, on='agebin_nr', how='inner')
    print(f'Saving OM_surveyoutput_base.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_surveyoutput_base.csv')), index=False, compression='gzip')


def BenchmarkAnalyzer(exp, mmi, grp_channels=['eir', 'ageGroup', 'seed', 'seasonality']):
    print(f"Running BenchmarkAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    age_groups = exp.agebins  # must reflect the xml monitoring section
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels

    df = to_df(exp)
    df = format_df(df)
    # df = pd.read_csv(os.path.join(exp.job_directory, 'OM_survey_output_raw.csv'), compression='gzip')

    # Sum the surveys
    df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()

    # adjust nHost for age_groups 0 to 1
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1

    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    g = df.merge(scen_df, on='index', how='inner')

    age2to10 = (age_groups[g.ageGroup - 1] >= 2) & (age_groups[g.ageGroup - 1] <= 10)

    nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(grp_channels).value.sum()
    nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(grp_channels).value.sum()

    grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
    pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean() * 100).rename("prevalence_2to10")
    simulatedEIR = (g[(g.measure == mmi['SimulatedEIR'])].groupby(grp_channels).value.mean() * 6).rename("simulatedEIR")

    adf = pd.DataFrame()
    age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]
    for i in range(0, len(age_groups_on_plot)):
        ages = age_groups_on_plot[i]
        ageCond = (age_groups[g.ageGroup - 1] >= ages[0]) & (age_groups[g.ageGroup - 1] <= ages[1])
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'

        nClinicalCases = 0
        for m in ['nUncomp']:
            nClinicalCases += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

        nSevereCases = 0
        for m in ['nUncomp']:
            nSevereCases += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

        nDeaths = 0
        for m in ['expectedDirectDeaths', 'expectedIndirectDeaths']:
            nDeaths += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

        nHost = g[(g.measure == mmi['nHost']) & ageCond].groupby(grp_channels).value.sum()

        clinical_incidence = nClinicalCases / (nHost / 12)  # (events per person per year)
        severe_incidence = nSevereCases / (nHost / 12)  # (events per person per year)
        mortality = nDeaths / (nHost / 12)  # (events per person per year)

        # clinical_incidence = clinical_incidence.groupby('eir').mean()
        # severe_incidence = severe_incidence.groupby('eir').mean()
        # mortality = mortality.groupby('eir').mean()
        # 'eir': list(g['eir'].unique()) * nseeds,  ## same for all age groups and seeds
        # 'prevalence_2to10': list(prevalence2to10) * nseeds,  ## same for all age groups and seeds
        # 'simulatedEIR': list(simulatedEIR) * nseeds,  ## same for all age groups and seeds
        # # 'age_group': ageCond_labels,

        simdata = pd.DataFrame({'prevalence_2to10': pfpr2to10,
                                'simulatedEIR': simulatedEIR,
                                'clinical_incidence': clinical_incidence,
                                'severe_incidence': severe_incidence,
                                'mortality': mortality})
        simdata['age_group'] = ageCond_labels
        adf = pd.concat([adf, simdata])

    adf.reset_index(inplace=True)
    print(f'Saving OM_benchmark.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_benchmark.csv')), index=False)


def MonthlyAgebinAnalyzer(exp, mm, saveExtract=False):
    print(f"Running MonthlyAgebinAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    df = to_df(exp)
    if saveExtract:
        df.to_csv((os.path.join(wdir, f'OM_survey_output_raw.csv')), index=False, compression='gzip')

    # df = pd.read_csv(os.path.join(wdir, "OM_survey_output.csv"), compression='gzip')
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)

    # Sum the surveys
    # df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum() ### do time aggregation later

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

    age_groups = exp.agebins  # np.array([0.5,1,2,5,10,15,20,100]) # must reflect the xml monitoring section
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels
    age_df = pd.DataFrame({'agebin_nr': df2['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    df3 = df2.merge(age_df, on='agebin_nr', how='inner')

    # adjust nHost for age_groups 0 to 1
    # yearsAtRisk = np.array(age_groups)
    # yearsAtRisk[yearsAtRisk > 1] = 1
    # df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup-1]
    # age2to10 = (age_groups[g.ageGroup-1] >= 2) & (age_groups[g.ageGroup-1] <= 10)
    # nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['eir', 'ageGroup', 'seed']).value.sum()
    # nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['eir', 'ageGroup', 'seed']).value.sum()
    # prevalence2to10 = (nPatent2to10 / nHost2to10).groupby('eir').mean() * 100
    print(f'Saving OM_surveyoutput_mth.csv to {wdir}')
    df3.to_csv((os.path.join(wdir, f'OM_surveyoutput_mth.csv')), index=False, compression='gzip')


def AnnualAgebinAnalyzer(exp, mm, saveExtract=False):
    print(f"Running AnnualAgebinAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    df = to_df(exp)
    if saveExtract:
        df.to_csv((os.path.join(wdir, f'OM_survey_output_raw.csv')), index=False, compression='gzip')

    # df = pd.read_csv(os.path.join(wdir, "OM_survey_output.csv"), compression='gzip')
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)

    # Sum the surveys
    # df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum() ### do time aggregation later

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

    age_groups = exp.agebins  # np.array([0.5,1,2,5,10,15,20,100]) # must reflect the xml monitoring section
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels
    age_df = pd.DataFrame({'agebin_nr': df2['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    df3 = df2.merge(age_df, on='agebin_nr', how='inner')

    # adjust nHost for age_groups 0 to 1
    # yearsAtRisk = np.array(age_groups)
    # yearsAtRisk[yearsAtRisk > 1] = 1
    # df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup-1]
    # age2to10 = (age_groups[g.ageGroup-1] >= 2) & (age_groups[g.ageGroup-1] <= 10)
    # nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['eir', 'ageGroup', 'seed']).value.sum()
    # nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['eir', 'ageGroup', 'seed']).value.sum()
    # prevalence2to10 = (nPatent2to10 / nHost2to10).groupby('eir').mean() * 100

    print(f'Saving OM_surveyoutput_yr to {wdir}')
    df3.to_csv((os.path.join(wdir, f'OM_surveyoutput_yr.csv')), index=False, compression='gzip')


if __name__ == "__main__":
    args = parse_args()
    job_directory = args.directory

    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    wdir = os.path.join(exp.sim_out_dir, 'om')

    # exp_sweeps = exp.sweeps
    # start_year = exp.start_year
    # end_year = exp.end_year

    InputEIRAnalyzer(exp, mm)
    MonthlyAgebinAnalyzer(exp, mm)
    BenchmarkAnalyzer(exp, mmi)

    prevalence2to10_to_incidence(exp, channel='clinical_incidence', y_lim=6)
    eir_to_prevalence2to10(exp)

    # if testmode:
    #  prevalence2to10_to_incidence(wdir,  channel='clinical_incidence', y_lim=6)
    #  sample_plot_mth(wdir, exp_tags)
    #  plot_eir_pfpr(wdir, exp_tags, eirchannel = "eir")
