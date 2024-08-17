import os
import argparse
import pickle
import datetime
import pandas as pd
import numpy as np
from measures import mm, mmi
import sys


def parse_args():
    """
    Parses command-line arguments for simulation specifications.
    """
    # Set the description for the argument parser
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)

    # Add the required argument for the job directory
    parser.add_argument(
        "-d",
        "--directory",
        type=str,
        required=True,
        help="Job Directory where exp.obj is located",
    )
    return parser.parse_args()


def to_df(exp):
    """
    Combined single OpenMalaria experiment outputs across scenarios into a DataFrame.
    Args:
        exp: The experiment object including information about the job_directory where outputs are stored and number of scenarios to expect
    Returns:
        A DataFrame containing the standard experiment output for all OpenMalaria scenarios.
    """

    data = []
    if exp.nexps == 1:
        output = pd.read_csv(os.path.join(exp.job_directory, 'txt', '1.txt'), sep="\t", header=None)
        output.columns = ['survey', 'ageGroup', 'measure', 'value']
        output['index'] = 1
        data.append(output)
    else:
        for i in range(1, exp.nexps + 1):
            try:
                # Read the experiment output from the TXT file
                output = pd.read_csv(os.path.join(exp.job_directory, 'txt', f'{i}.txt'), sep="\t", header=None)
                output.columns = ['survey', 'ageGroup', 'measure', 'value']
                output['index'] = i
                data.append(output)
            # Allows exception and skip scenario if no TXT output exists
            except Exception as e:
                print(e)

    # Concatenate all the experiment outputs into a single DataFrame and return
    return pd.concat(data)


def format_df(df):
    """
    Format the DataFrame containing OpenMalaria experiment output.
    """
    # Reset the index of the DataFrame
    df.reset_index(drop=True, inplace=True)
    # Specify the data types for the columns
    df = df.astype(dtype={
        'survey': np.int32,
        'ageGroup': np.int32,
        'measure': np.int32,
        'value': np.float64,
        'index': np.int32
    })
    # Drop rows with survey number 1, that include cumulative results over past simulation time not monitored
    df.drop(df[df.survey == 1].index, inplace=True)
    df['survey'] = df['survey'] - 1
    # Reset the index of the DataFrame to drop rows with NaN values
    df.reset_index(inplace=True)
    return df


def add_measure_names(df, mm):
    """
    Adds measure names to a DataFrame based on a measure dictionary specific to OpenMalaria.
    Args:
        df (pandas.DataFrame): The input DataFrame to annotate with measure names.
        mm (dict): The measure dictionary mapping measure IDs to measure names.
    Returns:
        pandas.DataFrame: The annotated DataFrame with measure names.
    """
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]
    adf = df.merge(mm_df, on='measure', how='inner')
    return adf


def survey_to_date(df, survey_step_days=30, start_year=0):
    """
    Converts OpenMalaria survey timesteps to dates based on the survey step size and simulation start year.
    Note: In OpenMalaria survey results are always written into a single file of the same format, in contrast to EMOD where multiple files may be specified
    Args:
        df (pandas.DataFrame): The input DataFrame per timestep
        survey_step_days (int): The number of days between surveys. Default is 30.
        start_year (int): The starting year for the surveys. Default is 0.
    Returns:
        pandas.DataFrame: The DataFrame with added 'date' column representing the survey dates.
    Raises:
        ValueError: If survey_step_days is not 30 or 365.
    """
    # 5day timesteps
    if survey_step_days == 5:
        df['days'] = df['survey'] * survey_step_days
        df['month'] = np.floor(df['days'] / (365.0001 / 12)) + 1
        df['month'] = df['month'] % 12 
        df.loc[df['month'] == 0, 'month'] = 12
        df['year'] = (df['days'] / 365.00000001).apply(np.floor)
        df['year'] = df['year'] + start_year
        #df['date'] = df.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1) 
    # Monthly timesteps
    elif survey_step_days == 30:
        df['days'] = df['survey'] * survey_step_days
        df['month'] = df['survey'] % 12
        df.loc[df['month'] == 0, 'month'] = 12
        df['year'] = (df['days'] / 360.00000001).apply(np.floor)
        df['year'] = df['year'] + start_year
        #df['date'] = df.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)
    # Annual timesteps
    elif survey_step_days == 365:
        df['year'] = df['survey']
        df['month'] = 1
        df['year'] = df['year'] + start_year
        #df['date'] = df.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)
    else:
        raise ValueError("survey_step_days must be 30 or 365")
    return df


def pivot_wider(df, index_cols=None, names_from=None, values_from=None):
    """
    Pivot a DataFrame from long to wide format.
    Args:
        df: The DataFrame to be pivoted.
        index_cols: Columns to use as index (default: ['index', 'survey', 'ageGroup']).
        names_from: Columns to use as column names in the wide format (default: ['measure_name']).
        values_from: Columns to use as values in the wide format (default: ['value']).
    Returns:
        A pivoted DataFrame in wide format.
    """
    # Set defaults if not specified
    if index_cols is None:
        index_cols = ['index', 'survey', 'ageGroup']
    if names_from is None:
        names_from = ['measure_name']
    if values_from is None:
        values_from = ['value']

    # Transform dataframe long to wide
    wdf = (df.pivot_table(index=index_cols,
                          columns=names_from,
                          values=values_from,
                          aggfunc='first'))
    wdf.columns = [''.join(col).replace('value', '') for col in wdf.columns]
    wdf = wdf.reset_index()
    return wdf


def get_age_group_labels(age_bins):
    age_group_labels = [str(age_bins[i - 1]) + "-" + str(age_bins[i]) for i in range(1, len(age_bins))]
    age_group_labels = [str(0) + "-" + str(age_bins[0])] + age_group_labels
    return age_group_labels


def InputEIRAnalyzer(exp, mm, start_year, survey_step_days=30, compr='infer'):
    """
    Run the InputEIRAnalyzer for OpenMalaria experiments.

    Args:
        exp: The experiment object.
        mm: The measure map object.
        start_year: The start year of the analysis.
        survey_step_days: The survey step interval in days (default: 30).
        compr: The compression method for saving the output CSV files (default: 'infer').

    """
    print("Running InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))

    # Prepare and format the data
    df = to_df(exp)
    df = format_df(df)

    df_vector = df[df['measure'].isin([32, 34])]
    df_all = df[df['measure'].isin([7, 35, 36])]
    df_all.drop(columns='ageGroup', inplace=True)

    df_vector = df_vector.groupby(['index', 'survey', 'measure'])[['value']].agg(np.sum).reset_index()
    df = pd.concat([df_vector, df_all], ignore_index=True)

    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)

    # Adjust the values based on the survey step interval
    df['value'] = df['value'] * (survey_step_days / 5)

    scen_var = ['scen_id', 'num_seeds', 'seasonality', 'entomology_mode']
    outcome_var = ['InputEIR', 'SimulatedEIR', 'nTransmit', 'Vector_Nv', 'Vector_Sv']
    cc_step_var = ['cc_factor_om', 'cc_timestep_om','cc_title']
    columns_to_keep = ['index', 'seed', 'survey', 'days', 'year'] + scen_var + outcome_var

    if survey_step_days == 5:
        df_day = add_measure_names(df, mm)
        df_day = pivot_wider(df_day, index_cols=['index', 'survey', 'days', 'year'])
        df_day = df_day.merge(scen_df, on='index', how='inner')
        # If we created different eirs for each simulation, we need to parse it out here, so all the models can eventually be aligned
        # The only difference between these two dfs is if eir_om (om specific eir) or eir (general to all models) is used.
        if 'cc_change' in df_day:
            df_day = df_day[columns_to_keep + cc_step_var]
            df_day = df_day.rename(columns={'SimulatedEIR': 'simulatedEIR',
                                            'InputEIR': 'inputEIR',
                                            'Vector_Nv': 'n_total_mos_pop',
                                            'Vector_Sv': 'n_infectious_mos',
                                            'days': 'timestep'})
        else:
            df_day = df_day[columns_to_keep]
            df_day = df_day.rename(columns={'SimulatedEIR': 'simulatedEIR',
                                            'InputEIR': 'inputEIR',
                                            'Vector_Nv': 'n_total_mos_pop',
                                            'Vector_Sv': 'n_infectious_mos',
                                            'days': 'timestep'})
        print(f'Saving EIR_daily.csv to {wdir}')
        df_day['day'] = (df_day['timestep']-1)%365 + 1
        df_day.to_csv((os.path.join(wdir, 'EIR_daily.csv')), index=False, compression=compr)

        # Monthly aggregation for survey_step_days = 5
        df_mth = df.groupby(['index', 'year', 'month', 'measure'], as_index=False).value.sum()
        df_mth = add_measure_names(df_mth, mm)
        df_mth = pivot_wider(df_mth, index_cols=['index', 'month', 'year'])
        df_mth = df_mth.merge(scen_df, on=['index'],  how='inner')
        df_mth = df_mth.rename(columns={'SimulatedEIR': 'simulatedEIR',
                                        'InputEIR': 'inputEIR',
                                        'Vector_Nv': 'n_total_mos_pop',
                                        'Vector_Sv': 'n_infectious_mos'})

        print(f'Saving EIR_mth.csv to {wdir}')
        df_mth.to_csv((os.path.join(wdir, 'EIR_mth.csv')), index=False, compression=compr)

    if survey_step_days == 30:
        # Monthly aggregation
        df_mth = add_measure_names(df, mm)
        df_mth = pivot_wider(df_mth, index_cols=['index', 'survey', 'year', 'month'])
        df_mth = df_mth.merge(scen_df, on='index', how='inner')
        df_mth = df_mth.rename(columns={'SimulatedEIR': 'simulatedEIR',
                                        'InputEIR': 'inputEIR',
                                        'Vector_Nv': 'n_total_mos_pop',
                                        'Vector_Sv': 'n_infectious_mos'})

        print(f'Saving EIR_mth.csv to {wdir}')
        df_mth.to_csv((os.path.join(wdir, 'EIR_mth.csv')), index=False, compression=compr)

    # Yearly aggregation - keep years
    df_yr = df.groupby(['index', 'year', 'measure'], as_index=False).value.sum()
    df_yr = add_measure_names(df_yr, mm)
    df_yr = pivot_wider(df_yr, index_cols=['index', 'year'])
    df_yr = df_yr.merge(scen_df, on='index', how='inner')
    df_yr = df_yr.rename(columns={'SimulatedEIR': 'simulatedEIR',
                                  'InputEIR': 'inputEIR',
                                  'Vector_Nv': 'n_total_mos_pop',
                                  'Vector_Sv': 'n_infectious_mos'})

    print(f'Saving EIR_yr.csv to {wdir}')
    df_yr.to_csv((os.path.join(wdir, 'EIR_yr.csv')), index=False, compression=compr)

    # Yearly aggregation - mean
    nyears = len(df['year'].unique())
    df_yr = df.groupby(['index', 'measure'], as_index=False).value.sum()
    df_yr['value'] = df_yr['value'] / nyears
    df_yr = add_measure_names(df_yr, mm)
    df_yr = pivot_wider(df_yr, index_cols=['index'])
    df_yr = df_yr.merge(scen_df, on='index', how='inner')
    df_yr = df_yr.rename(columns={'SimulatedEIR': 'simulatedEIR',
                                  'InputEIR': 'inputEIR',
                                  'Vector_Nv': 'n_total_mos_pop',
                                  'Vector_Sv': 'n_infectious_mos'})

    print(f'Saving EIR.csv to {wdir}')
    df_yr.to_csv((os.path.join(wdir, 'EIR.csv')), index=False,
                 compression=compr)  ## annual average - do we need to keep this?


def BaseAnalyzer(exp, mm, saveExtract=False, compr='infer'):
    """
    Run the BaseAnalyzer for OpenMalaria experiments.
    Args:
        exp: The experiment object.
        mm: The measure map object.
        saveExtract: Whether to save the raw survey output DataFrame (default: False).
        compr: The compression method for saving the output CSV files (default: 'gzip').
    """
    print("Running BaseAnalyzer...", flush=True)

    # Read the experiment data into a DataFrame
    df = to_df(exp)
    if saveExtract:
        # Save the raw survey output if saveExtract is True
        df.to_csv((os.path.join(wdir, 'Surveyoutput_raw.csv')), index=False, compression=compr)

    # Format and filter the DataFrame
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)  ## ageGroup 0 = vector related or all age related outcomes (i.e. EIR)
    df.drop(df[df.ageGroup > 1000].index, inplace=True) ## In OpenMalaria 'third dimension' may indicate other dimensions than age group

    # Convert the measure map to a DataFrame
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    # Merge the data with the measure map based on the 'measure' column
    adf = df.merge(mm_df, on='measure', how='inner')
    adf = adf.rename(columns={'ageGroup': 'agebin_nr'})

    # Extract age groups from the experiment's agebins
    age_group_labels = get_age_group_labels(exp.agebins)
    age_df = pd.DataFrame({'agebin_nr': adf['agebin_nr'].unique(), 'agebin': exp.agebins, 'ageGroup': age_group_labels})

    # Merge the data with the age information based on the 'agebin_nr' column
    adf = adf.merge(age_df, on='agebin_nr', how='inner')

    # Save the processed DataFrame to a CSV file named 'Surveyoutput_base.csv'
    print(f'Saving Surveyoutput_base.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, 'Surveyoutput_base.csv')), index=False, compression=compr)


def SurveyAllAgeAnalyzer(exp, mm, start_year=2020, survey_step_days=30, compr='infer'):
    """
    Run the SurveyAllAgeAnalyzer for OpenMalaria experiments.
    Args:
        exp: The experiment object.
        mm: The measure map object.
        start_year: The start year for the survey (default: 2020).
        survey_step_days: The survey step size in days (default: 30).
        compr: The compression method for saving the output CSV files (default: 'infer').
    """
    print("Running SurveyAllAgeAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)

    # Separate the age group 0 data ('all age') and adjust the values
    df0 = df.loc[df.ageGroup == 0]
    df0.drop(['ageGroup'], axis=1)
    df0.loc[:, 'value'] = df0['value'] * (survey_step_days / 5)

    # Drop age group 0 from the main DataFrame
    df.drop(df[df.ageGroup == 0].index, inplace=True)
    df.drop(df[df.ageGroup > 1000].index, inplace=True)  ## In OpenMalaria 'third dimension' may indicate other dimensions than age group

    # Sum the values of the age groups
    df = df.groupby(['index', 'survey', 'measure'], as_index=False).value.sum()

    # Convert the measure map to a DataFrame
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    # Merge the age group 0 data with the measure map
    df0 = df0.merge(mm_df, on='measure', how='inner')
    df0 = pivot_wider(df0, index_cols=['index', 'survey'])

    # Merge the summed age group data with the measure map
    adf = df.merge(mm_df, on='measure', how='inner')
    adf = pivot_wider(adf, index_cols=['index', 'survey'])

    # Merge the age group 0 data and the summed age group data
    adf = adf.merge(df0, on=['index', 'survey'], how='inner')

    # Merge with the scenario data
    adf = adf.merge(scen_df, on='index', how='inner')

    # Rename columns and compute the total number of treatments
    adf = adf.rename(columns={'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'})
    adf['nTreatments'] = adf['nTreatments1'] + adf['nTreatments2'] + adf['nTreatments3']

    # Convert survey dates to actual dates based on the survey step size and start year
    adf = survey_to_date(adf, survey_step_days=survey_step_days, start_year=start_year)

    # Save the processed DataFrame to a CSV file
    print(f'Saving All_Age_Outputs.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, 'All_Age_Outputs.csv')), index=False, compression=compr)


def BenchmarkAnalyzer(exp, mmi, survey_step_days=30, grp_channels=['ageGroup', 'index'], age_groups_aggregates=None):
    """
    Run the BenchmarkAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups aggregated over the monitoring period.

    Args:
        exp (object): The experiment object.
        mmi (object): The measure map object.
        start_year (int):  The starting year for the surveys (i.e. start year of monitoring period).
        grp_channels (list, optional): The group channels for grouping the data (default: ['ageGroup', 'index']).
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.
        survey_step_days (int, optional): Number of days between survey steps. Defaults to 30.

    Saves:
        Benchmark.csv

    Returns:
        None
    """
    print("Running BenchmarkAnalyzer...", flush=True)

    # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframeto write out
    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR', 'n_total_mos_pop', 'n_infectious_mos']]

    # Define age groups and labels
    age_bins = exp.agebins

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)
    df.drop(df[df.ageGroup > 1000].index, inplace=True)  ## In OpenMalaria 'third dimension' may indicate other dimensions than age group

    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / survey_step_days))
    num_years = np.floor(len(df['survey'].unique()) / n_surveys_per_year)

    # Sum the surveys for each measure and age group
    df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()

    # for sum of annual Host population.
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year
    df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year

    # Adjust nHost for age_groups 0 to 1 based on yearsAtRisk
    yearsAtRisk = np.array(age_bins)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    g = df

    # Filter and aggregate data for age groups 2 to 10
    age2to10 = g['ageGroup'].apply(lambda x: age_bins[x - 1] > 2 and age_bins[x - 1] <= 10)
    nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['index']).value.sum()
    nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['index']).value.sum()

    # Calculate PfPR for age groups 2 to 10
    grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
    pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

    # Prepare an empty DataFrame for storing the analysis results
    adf = pd.DataFrame()

    # Analyze data for each age group on the plot
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        # note, keep as overlapping age groups
        ageCond = g['ageGroup'].apply(lambda x: age_bins[x - 1] > ages[0] and age_bins[x - 1] <= ages[1])
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'

        # Compute various measures for the current age group
        nPatentInfections = 0
        for m in ['nPatent']:
            nPatentInfections += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

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

        prevalence = nPatentInfections / nHost  # prevalence
        clinical_incidence = nClinicalCases / nHost  # (events per person per year)
        severe_incidence = nSevereCases / nHost  # (events per person per year)
        mortality = nDeaths / nHost  # (events per person per year)

        # Create a DataFrame with the analysis results for the current age group
        simdata = pd.DataFrame({'nHost': nHost / num_years,
                                'prevalence_2to10': pfpr2to10,
                                'prevalence': prevalence,
                                'clinical_incidence': clinical_incidence,
                                'severe_incidence': severe_incidence,
                                'mortality': mortality})
        simdata['ageGroup'] = ageCond_labels
        adf = pd.concat([adf, simdata])

    # Merge the analysis results with the scenario and EIR data
    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on='index', how='inner')

    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    print(f'Saving Benchmark.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, 'Benchmark.csv')), index=False)

    if exp.run_mode == 'calibrun':
        u5 = adf[adf['ageGroup']=='0-5'].groupby('scen_id')['clinical_incidence'].agg('mean').reset_index()
        u5 = u5.rename(columns={'clinical_incidence':'clinical_incidence_U5'})
        all_ages = adf[adf['ageGroup']=='0-100'].groupby('scen_id')['clinical_incidence'].agg('mean').reset_index()
        adf = adf[adf['ageGroup']=='0-100']
        adf = adf.groupby(['scen_id','model_input_om','seasonality','cm_clinical'])[['simulatedEIR','prevalence_2to10','prevalence','severe_incidence','n_total_mos_pop']].agg('mean').reset_index()
        adf = adf.merge(all_ages, on = 'scen_id')
        adf = adf.merge(u5, on = 'scen_id')
        adf = adf.drop(['scen_id'],axis=1)
        adf['modelname'] = 'OpenMalaria'
        adf = adf.rename(columns={'model_input_om':'input_target'})
        adf.to_csv((os.path.join(wdir, 'interpolation_data.csv')), index=False)
        adf.to_csv((os.path.join(exp.interp_path, 'OpenMalaria', f'{exp.exp_name}_interpolation_data.csv')))

def AnnualAgebinAnalyzer(exp, mmi, start_year, survey_step_days=30, grp_channels=['ageGroup', 'index'],
                         age_groups_aggregates=None):
    """
    Run the AnnualAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups over time (years).

    Args:
        exp (object): The experiment object.
        mmi (object): The measure map object.
        start_year (int):  The starting year for the surveys (i.e. start year of monitoring period).
        grp_channels (list, optional): The group channels for grouping the data (default: ['ageGroup', 'index']).
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.
        survey_step_days (int, optional): Number of days between survey steps. Defaults to 30.

    Saves:
        PfPR_ClinicalIncidence_yr.csv

    Returns:
        None
    """
    print("Running AnnualBenchmarkAnalyzer...", flush=True)

    # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframeto write out
    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))

    # Read the monthly EIR data from the CSV file and compute the mean for each index and month
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_yr.csv'))
    eir_df = eir_df[['index', 'year', 'inputEIR', 'simulatedEIR', 'n_total_mos_pop', 'n_infectious_mos']]

    # Define age groups and labels
    age_bins = exp.agebins

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)
    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)
    df.drop(df[df.ageGroup == 0].index, inplace=True)
    df.drop(df[df.ageGroup > 1000].index, inplace=True)  ## 'third dimension' may indicate other  than age group


    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / survey_step_days))

    # Sum the surveys for each measure, year, and age group
    df = df.groupby(['index', 'year', 'measure', 'ageGroup'], as_index=False).value.sum()

    # for sum of annual Host population.
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year
    df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year

    # Adjust nHost for age groups 0 to 1 based on yearsAtRisk
    yearsAtRisk = np.array(age_bins)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]

    adf = pd.DataFrame()
    # Iterate over each year
    for yr in df['year'].unique():
        g = df.loc[df['year'] == yr]

        # Filter and aggregate data for age groups 2 to 10
        age2to10 = g['ageGroup'].apply(lambda x: age_bins[x - 1] > 2 and age_bins[x - 1] <= 10)
        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['index']).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['index']).value.sum()

        grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
        pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

        # Analyze data for each age group on the plot
        for i in range(0, len(age_groups_aggregates)):
            ages = age_groups_aggregates[i]
            ageCond = g['ageGroup'].apply(
                lambda x: age_bins[x - 1] > ages[0] and age_bins[x - 1] <= ages[1])  # non overlapping
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'

            # Compute various measures for the current age group
            nPatentInfections = 0
            for m in ['nPatent']:
                nPatentInfections += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

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

            prevalence = nPatentInfections / nHost  # prevalence
            clinical_incidence = nClinicalCases / nHost  # (events per person per year)
            severe_incidence = nSevereCases / nHost  # (events per person per year)
            mortality = nDeaths / nHost  # (events per person per year)

            # Create a DataFrame with the analysis results for the current age group
            simdata = pd.DataFrame({'nHost': nHost,
                                    'prevalence_2to10': pfpr2to10,
                                    'prevalence': prevalence,
                                    'clinical_incidence': clinical_incidence,
                                    'severe_incidence': severe_incidence,
                                    'mortality': mortality})
            simdata['ageGroup'] = ageCond_labels
            simdata['year'] = yr
            adf = pd.concat([adf, simdata])

    # Merge the analysis results with the scenario and EIR data
    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on=['index', 'year'], how='inner')

    # Save the processed DataFrame to a CSV file named 'PfPR_ClinicalIncidence_yr.csv'
    print(f'Saving PfPR_ClinicalIncidence_yr.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, 'PfPR_ClinicalIncidence_yr.csv')), index=False)


def MonthlyAgebinAnalyzer(exp, mmi, start_year, grp_channels=['ageGroup', 'index'], age_groups_aggregates=None,
                          survey_step_days=30):
    """
    Run the MonthlyAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups over time (month and years).

    Args:
        exp (object): The experiment object.
        mmi (object): The measure map object.
        start_year (int):  The starting year for the surveys (i.e. start year of monitoring period).
        grp_channels (list, optional): The group channels for grouping the data (default: ['ageGroup', 'index']).
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.
        survey_step_days (int, optional): Number of days between survey steps. Defaults to 30.

    Saves:
        PfPR_ClinicalIncidence_mth.csv

    Returns:
        None
    """

    print("Running MonthlyBenchmarkAnalyzer...", flush=True)

    # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframeto write out
    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))

    # Read the monthly EIR data from the CSV file and compute the mean for each index and month
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_mth.csv'))
    eir_df = eir_df.groupby(['index', 'month'], as_index=False)[['inputEIR', 'simulatedEIR', 'n_total_mos_pop', 'n_infectious_mos']].mean()

    # Define age groups and labels
    age_bins = exp.agebins

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)
    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)
    df.drop(df[df.ageGroup == 0].index, inplace=True)
    df.drop(df[df.ageGroup > 1000].index, inplace=True)  ## In OpenMalaria 'third dimension' may indicate other dimensions than age group

    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / 30))
    #num_years = np.floor(len(df['survey'].unique()) / n_surveys_per_year)

    # Sum the surveys for each measure, month, and age group - note the same if survey_step_days = 30, but should also run if survey_step_days = 5
    df = df.groupby(['index',  'year', 'month', 'measure', 'ageGroup'], as_index=False).value.sum()

    # for sum of annual pop not sum of years+months.
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year
    df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year

    # Adjust nHost for age groups 0 to 1 based on yearsAtRisk
    yearsAtRisk = np.array(age_bins)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    sdf = df

    adf = pd.DataFrame()
    # Iterate over month and year
    for (year, month), group in sdf.groupby(['year', 'month']):
        g = sdf.loc[(sdf['year'] == year) & (sdf['month'] == month)]

        # Filter and aggregate data for age groups 2 to 10
        age2to10 = g['ageGroup'].apply(lambda x: age_bins[x - 1] > 2 and age_bins[x - 1] <= 10)
        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['index']).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['index']).value.sum()

        grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
        pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

        # Analyze data for each age group on the plot
        for i in range(0, len(age_groups_aggregates)):
            ages = age_groups_aggregates[i]
            ageCond = g['ageGroup'].apply(lambda x: age_bins[x - 1] > ages[0] and age_bins[x - 1] <= ages[1])

            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'

            # Compute various measures for the current age group
            nPatentInfections = 0
            for m in ['nPatent']:
                nPatentInfections += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

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

            prevalence = nPatentInfections / nHost  # (prevalence)
            clinical_incidence = nClinicalCases / nHost  # (events per person per year) - for each month
            severe_incidence = nSevereCases / nHost  # (events per person per year) - for each month
            mortality = nDeaths / nHost  # (events per person per year)- for each month

            # Create a DataFrame with the analysis results for the current age group
            simdata = pd.DataFrame({'nHost': nHost * n_surveys_per_year,
                                    'prevalence_2to10': pfpr2to10,
                                    'prevalence': prevalence,
                                    'clinical_incidence': clinical_incidence,
                                    'severe_incidence': severe_incidence,
                                    'mortality': mortality})
            simdata['ageGroup'] = ageCond_labels
            simdata['month'] = month
            simdata['year'] = year
            adf = pd.concat([adf, simdata])

    # Merge the analysis results with the scenario and EIR data
    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on=['index', 'month'], how='inner')
    adf['date'] = adf.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)
    # Save the processed DataFrame to a CSV file named 'PfPR_ClinicalIncidence_mth.csv'
    print(f'Saving PfPR_ClinicalIncidence_mth.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, 'PfPR_ClinicalIncidence_mth.csv')), index=False)


def FiveDayAgebinAnalyzer(exp, mmi, start_year, grp_channels=['ageGroup', 'index'], age_groups_aggregates=None,
                          survey_step_days=5):
    """
    Run the FiveDayAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups over time (5day and years).

    Args:
        exp (object): The experiment object.
        mmi (object): The measure map object.
        start_year (int):  The starting year for the surveys (i.e. start year of monitoring period).
        grp_channels (list, optional): The group channels for grouping the data (default: ['ageGroup', 'index']).
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.
        survey_step_days (int, optional): Number of days between survey steps. Defaults to 30.

    Saves:
        PfPR_ClinicalIncidence_5day.csv

    Returns:
        None
    """

    print("Running FiveDayAgebinAnalyzer...", flush=True)

    # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframeto write out
    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))

    # Read the monthly EIR data from the CSV file and compute the mean for each index and timestep
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_daily.csv'))
    eir_df = eir_df.groupby(['index', 'survey'], as_index=False)[
        ['inputEIR', 'simulatedEIR', 'n_total_mos_pop', 'n_infectious_mos']].mean()

    # Define age groups and labels
    age_bins = exp.agebins

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)
    df.drop(df[df.ageGroup > 1000].index, inplace=True)

    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / 5))

    # Sum the surveys for each measure, timestep,and age group
    df = df.groupby(['index', 'survey', 'measure', 'ageGroup'], as_index=False).value.sum()

    # for sum of annual pop not sum of years+months.
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year
    df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year

    # Adjust nHost for age groups 0 to 1 based on yearsAtRisk
    yearsAtRisk = np.array(age_bins)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    sdf = df

    adf = pd.DataFrame()
    # Iterate over day, month, and year
    for ii, group in enumerate(sdf.groupby(['survey'])):
        t, grouped = group
        g = sdf.loc[(sdf['survey'] == t)]

        # Filter and aggregate data for age groups 2 to 10
        age2to10 = g['ageGroup'].apply(lambda x: age_bins[x - 1] > 2 and age_bins[x - 1] <= 10)
        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(['index']).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(['index']).value.sum()

        grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
        pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

        # Analyze data for each age group on the plot
        for i in range(0, len(age_groups_aggregates)):
            ages = age_groups_aggregates[i]
            ageCond = g['ageGroup'].apply(lambda x: age_bins[x - 1] > ages[0] and age_bins[x - 1] <= ages[1])

            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'

            # Compute various measures for the current age group
            nPatentInfections = 0
            for m in ['nPatent']:
                nPatentInfections += g[(g.measure == mmi[m]) & ageCond].groupby(grp_channels).value.sum()

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

            prevalence = nPatentInfections / nHost  # (prevalence)
            clinical_incidence = nClinicalCases / nHost  # (events per person per year) - for each 5day
            severe_incidence = nSevereCases / nHost  # (events per person per year) - for each 5day
            mortality = nDeaths / nHost  # (events per person per year)- for each 5day

            # Create a DataFrame with the analysis results for the current age group
            simdata = pd.DataFrame({'nHost': nHost * n_surveys_per_year,
                                    'prevalence_2to10': pfpr2to10,
                                    'prevalence': prevalence,
                                    'clinical_incidence': clinical_incidence,
                                    'severe_incidence': severe_incidence,
                                    'mortality': mortality})
            simdata['ageGroup'] = ageCond_labels
            simdata['survey'] = t
            adf = pd.concat([adf, simdata])

    # Merge the analysis results with the scenario and EIR data
    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')

    adf = adf.merge(eir_df, on=['index', 'survey'], how='inner')

    # adf['date'] = adf.apply(lambda x: datetime.date(int(x['year']), 1, 1) + datetime.timedelta(days=int(x['day']) - 1), axis=1)
    adf = survey_to_date(adf, survey_step_days=survey_step_days, start_year=start_year)
    adf['day'] = (adf['days']-1)%365 + 1
    adf = adf.drop(columns = ['days','month']) #This can be removed once we have consistent months across all three models
    #Months in five day periods is currently wrong.
    # Save the processed DataFrame to a CSV file named 'PfPR_ClinicalIncidence_5day.csv'
    print(f'Saving PfPR_ClinicalIncidence_5day.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, 'PfPR_ClinicalIncidence_5day.csv')), index=False)


def CCStepAnalyzer(exp, mm, start_year, compr='infer'):
    """
    Run the DailyAgebinAnalyzer equivalent for OpenMalaria experiments.
    Args:
        exp: The experiment object.
        mm: The measure map object.
        start_year: The starting year for the surveys.
        compr: The compression type for saving the output CSV file (default: 'infer').
    Saves: CSV dataframe of simulation outcome metrics per agebin, month and grp_channels
           surveys aggregated per surveytimestep (year and month)
    Returns:
        None
    """
    print("Running CCStepAnalyzer...", flush=True)
    channels = ['index', 'survey', 'ageGroup', 'nHost', 'nPatent', 'nInfect', 'nUncomp', 'nSevere', 'Vector_Nv',
                'Vector_Sv']

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios_wseeds.csv'))

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)

    # Remove rows with ageGroup 0 ('all age')
    df.drop(df[df.ageGroup == 0].index, inplace=True)
    df.drop(df[df.ageGroup > 1000].index, inplace=True)  ## In OpenMalaria 'third dimension' may indicate other dimensions than age group

    # Convert the measure map to a DataFrame
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    # Merge the experiment data with the measure map on the measure column
    adf = df.merge(mm_df, on='measure', how='inner')

    # Pivot the table to have measures as columns and values as cells
    df1 = (adf.pivot_table(index=['index', 'survey', 'ageGroup'],
                           columns=['measure_name'],
                           values=['value'],
                           aggfunc='first'))
    df1.columns = [''.join(col).replace('value', '') for col in df1.columns]
    df1 = df1.reset_index()

    # only keep selected outcome columns
    df1 = df1[channels]
    # Merge the pivoted table with the scenario data
    df2 = df1.merge(scen_df, on='index', how='inner')

    df2 = df2.rename(columns={'ageGroup': 'agebin_nr'})

    # Define age groups and labels
    age_group_labels = get_age_group_labels(exp.agebins)
    age_df = pd.DataFrame({'agebin_nr': df2['agebin_nr'].unique(), 'agebin': exp.agebins, 'ageGroup': age_group_labels})

    # Merge the age group data with the previous DataFrame
    df3 = df2.merge(age_df, on='agebin_nr', how='inner')

    # Convert survey data to dates and set the start year
    df3 = survey_to_date(df3, survey_step_days=5, start_year=start_year)

    n_surveys_per_year = np.floor((365 / 5))
    df3['nHost'] = (df3['nHost'] / n_surveys_per_year)
    df3['nPatent'] = (df3['nPatent'] / n_surveys_per_year)
    df3['nUncomp'] = (df3['nUncomp'] / n_surveys_per_year)
    df3['nSevere'] = (df3['nSevere'] / n_surveys_per_year)
    df3['prevalence'] = df3['nPatent'] / df3['nHost']
    df3['clinical_incidence'] = df3['nUncomp'] / (df3['nHost'])  # per person per annum
    df3['severe_incidence'] = df3['nSevere'] / (df3['nHost'])  # per person per annum


    first_columns = ['seed', 'year', 'month', 'agebin', 'ageGroup', 'nHost', 'prevalence', 'clinical_incidence',
                     'severe_incidence']
    df3 = df3[first_columns + df3.drop(columns=first_columns).columns.tolist()]
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_daily.csv'))
    eir_df = eir_df[['index', 'survey', 'year', 'simulatedEIR', 'inputEIR']]
    eir_df['simulatedEIR'] = eir_df['simulatedEIR'] / 5 # we divide by 5 for cc plotting, so it more closely reflects daily output
    df3 = df3.merge(eir_df, on=['index', 'survey', 'year'], how='inner')
    df3 = df3[['scen_id', 'index', 'seed', 'cm_start', 'cm_severe', 'cm_clinical', 'seasonality', 'survey', 'days',
                   'month', 'year', 'agebin', 'ageGroup', 'Vector_Nv', 'Vector_Sv',
                   'nHost', 'output_target', 'inputEIR', 'simulatedEIR', 'prevalence', 'clinical_incidence', 'severe_incidence',
                   'nPatent', 'nInfect', 'nUncomp','nSevere', 'cc_factor_om', 'cc_change','cc_title']]
    df3 = df3.rename(
            columns={'days': 'timestep','Vector_Nv': 'n_total_mos_pop', 
                     'Vector_Sv': 'n_infectious_mos'})

    grp_channels = ['index', 'timestep']
    age_groups_2to10 = [5,10]
    g = df3[df3['agebin'].isin(age_groups_2to10)]
    nHost2to10 = g.groupby(grp_channels)['nHost'].agg(np.sum).reset_index()
    nPatent2to10 = g.groupby(grp_channels)['nPatent'].agg(np.sum).reset_index()
    pfpr2to10 = nPatent2to10.merge(nHost2to10, on=grp_channels, how='inner')
    pfpr2to10['prevalence_2to10'] = pfpr2to10['nPatent'] / pfpr2to10['nHost']
    pfpr2to10 = pfpr2to10[['prevalence_2to10', 'timestep', 'index']]
    df3 = df3.merge(pfpr2to10, on=['timestep', 'index'], how='inner')
    vector_channels = ['n_total_mos_pop', 'n_infectious_mos']
    v = df3.groupby(grp_channels)[vector_channels].agg(np.sum).reset_index()
    df3 = df3.drop(columns=vector_channels)
    df3 = df3.merge(v, on=grp_channels, how='inner')
    # Save the processed DataFrame to a CSV file
    print(f'\nSaving outputs to: {wdir}')
    cols_to_keep = ['scen_id', 'seed', 'cm_clinical','seasonality', 'output_target', 'cc_change', 'cc_title', 'ageGroup', 'timestep', 'simulatedEIR', 'prevalence_2to10', 'prevalence',
                    'clinical_incidence', 'severe_incidence', 'n_total_mos_pop', 'n_infectious_mos']
    df3 = df3[cols_to_keep]
    df3.to_csv((os.path.join(wdir, 'CCstep_daily.csv')), index=False, compression=compr)


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    jdir = args.directory
    # Load experiment object
    file = open(os.path.join(jdir, "exp.obj"), "rb")
    exp = pickle.load(file)
    start_year = exp.start_year
    wdir = os.path.join(exp.sim_out_dir, 'om')
    age_groups_aggregates = exp.age_groups_aggregates

    # Determine survey step size
    if exp.om_survey_step == '5d':
        survey_steps = 5
    if exp.om_survey_step == '30d':
        survey_steps = 30
    if exp.om_survey_step == '1y':
        survey_steps = 365

    # Run analyzers
    InputEIRAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)

    if survey_steps == 30:
        BaseAnalyzer(exp, mm, saveExtract=False, compr='gzip')
        SurveyAllAgeAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)

    ## Aggregated timeseries per age groups
    if 'benchmark' in exp.analyzer_list:
        BenchmarkAnalyzer(exp, mmi, survey_step_days=survey_steps, age_groups_aggregates=age_groups_aggregates)

    ## 5 day timeseries per age groups
    if '5day' in exp.analyzer_list:
        FiveDayAgebinAnalyzer(exp, mmi, start_year=start_year, survey_step_days=survey_steps,
                              age_groups_aggregates=age_groups_aggregates)

    ## Monthly timeseries per age groups
    if 'monthly' in exp.analyzer_list:
        MonthlyAgebinAnalyzer(exp, mmi, start_year=start_year, survey_step_days=survey_steps,
                              age_groups_aggregates=age_groups_aggregates)

    ## Annual timeseries per age groups
    if 'annual' in exp.analyzer_list:
        AnnualAgebinAnalyzer(exp, mmi, start_year=start_year, survey_step_days=survey_steps,
                             age_groups_aggregates=age_groups_aggregates)

    ## Custom analyzers
    if survey_steps == 5 and 'cc_step' in exp.analyzer_list:
        CCStepAnalyzer(exp, mm, start_year, compr='infer')