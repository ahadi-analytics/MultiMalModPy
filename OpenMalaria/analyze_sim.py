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
    Combined single OpenMalaria experiment outputs across scenarios into a  DataFrame.
    Args:
        exp: The experiment object including information about the job_directory where outputs are stored and number of scenarios to expect
    Returns:
        A DataFrame containing the standard experiment output for all OpenMalaria scenarios.
    """
    data = []
    for i in range(1, exp.nexps):
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
    df['survey'] = df['survey'] -1
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
        df['month'] = np.floor(df['days'] / (365/12))+1
        df['month'] = df['survey'] % 12
        df.loc[df['month'] == 0, 'month'] = 12
        df['year'] = (df['days'] / 365).apply(np.floor)
    # Monthly timesteps
    elif survey_step_days == 30:
        df['days'] = df['survey'] * survey_step_days
        df['month'] = df['survey'] % 12
        df.loc[df['month'] == 0, 'month'] = 12
        df['year'] = (df['days'] / 365).apply(np.floor)
    # Annual timesteps
    elif survey_step_days == 365:
        df['year'] = df['survey']
        df['month'] = 1
    else:
        raise ValueError("survey_step_days must be 30 or 365")

    df['year'] = df['year'] + start_year
    df['date'] = df.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)

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
    if index_cols is None: index_cols = ['index', 'survey', 'ageGroup']
    if names_from is None: names_from = ['measure_name']
    if values_from is None: values_from = ['value']

    # Transform dataframe long to wide
    wdf = (df.pivot_table(index=index_cols,
                          columns=names_from,
                          values=values_from,
                          aggfunc='first'))
    wdf.columns = [''.join(col).replace('value', '') for col in wdf.columns]
    wdf = wdf.reset_index()
    return wdf


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
    print(f"Running InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    # Prepare and format the data
    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup > 0].index, inplace=True)
    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)

    # Adjust the values based on the survey step interval
    df['value'] = df['value'] * (survey_step_days / 5)

    if survey_step_days == 30:
        # Monthly aggregation
        df_mth = add_measure_names(df, mm)
        df_mth = pivot_wider(df_mth, index_cols=['index', 'survey', 'year', 'month', 'ageGroup'])
        df_mth = df_mth.merge(scen_df, on='index', how='inner')
        df_mth = df_mth.rename({'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'}, axis=1)
        df_mth.to_csv((os.path.join(wdir, f'OM_EIR_mth.csv')), index=False, compression=compr)

    # Yearly aggregation
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
    """
    Run the BaseAnalyzer for OpenMalaria experiments.
    Args:
        exp: The experiment object.
        mm: The measure map object.
        saveExtract: Whether to save the raw survey output DataFrame (default: False).
        compr: The compression method for saving the output CSV files (default: 'gzip').
    """
    print(f"Running BaseAnalyzer...", flush=True)

    # Read the experiment data into a DataFrame
    df = to_df(exp)
    if saveExtract:
        # Save the raw survey output if saveExtract is True
        df.to_csv((os.path.join(wdir, f'OM_surveyoutput_raw.csv')), index=False, compression=compr)

    # Format and filter the DataFrame
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)

    # Convert the measure map to a DataFrame
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    # Merge the data with the measure map based on the 'measure' column
    adf = df.merge(mm_df, on='measure', how='inner')
    adf = adf.rename({'ageGroup': 'agebin_nr'}, axis=1)

    # Extract age groups from the experiment's agebins
    age_groups = exp.agebins
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels
    age_df = pd.DataFrame({'agebin_nr': adf['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    # Merge the data with the age information based on the 'agebin_nr' column
    adf = adf.merge(age_df, on='agebin_nr', how='inner')

    # Save the processed DataFrame to a CSV file named 'OM_surveyoutput_base.csv'
    print(f'Saving OM_surveyoutput_base.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_surveyoutput_base.csv')), index=False, compression=compr)


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
    print(f"Running SurveyAllAgeAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)

    # Separate the age group 0 data ('all age') and adjust the values
    df0 = df.loc[df.ageGroup == 0]
    df0.drop(['ageGroup'], axis=1)
    df0.loc[:, 'value'] = df0['value'] * (survey_step_days / 5)

    # Drop age group 0 from the main DataFrame
    df.drop(df[df.ageGroup == 0].index, inplace=True)

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
    adf = adf.rename({'SimulatedEIR': 'simulatedEIR', 'InputEIR': 'inputEIR'}, axis=1)
    adf['nTreatments'] = adf['nTreatments1'] + adf['nTreatments2'] + adf['nTreatments3']

    # Convert survey dates to actual dates based on the survey step size and start year
    adf = survey_to_date(adf, survey_step_days=survey_step_days, start_year=start_year)

    # Save the processed DataFrame to a CSV file named 'All_Age_InsetChart.csv'
    print(f'Saving All_Age_InsetChart.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'All_Age_InsetChart.csv')), index=False, compression=compr)


def BenchmarkAnalyzer(exp, mmi, survey_step_days=30, grp_channels=['ageGroup', 'index']):
    """
    Run the BenchmarkAnalyzer equivalent of EMOD for OpenMalaria experiments.
    Args:
        exp: The experiment object.
        mmi: The measure map object.
        survey_step_days: The survey step size in days (default: 30).
        grp_channels: The group channels for grouping the data (default: ['ageGroup', 'index']).
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup and grp_channels
           all surveys aggregated
    Returns:
        None
    """
    print(f"Running BenchmarkAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'OM_EIR.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Define age groups and labels
    age_groups = exp.agebins
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)

    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / survey_step_days))
    num_years = np.floor(len(df['survey'].unique()) / n_surveys_per_year)

    # Sum the surveys for each measure and age group
    df = df.groupby(['index', 'measure', 'ageGroup'], as_index=False).value.sum()

    # for sum of annual Host population.
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year
    df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year

    # Adjust nHost for age_groups 0 to 1 based on yearsAtRisk
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    g = df

    # Filter and aggregate data for age groups 2 to 10
    age2to10 = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= 2 and age_groups[x - 1] <= 10)
    nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(grp_channels).value.sum()
    nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(grp_channels).value.sum()

    # Calculate PfPR for age groups 2 to 10
    grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
    pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

    # Prepare an empty DataFrame for storing the analysis results
    adf = pd.DataFrame()

    # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframe to write out
    # [[0, 5]] + [[(age_groups[i - 1]), (age_groups[i])] for i in range(1, len(age_groups))]
    age_groups_aggregates = [[0, 5], [5, 10], [10, 15], [15, 20]]

    # Analyze data for each age group on the plot
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        # note, keep as overlapping age groups
        ageCond = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= ages[0] and age_groups[x - 1] <= ages[1])
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
        simdata['age_group'] = ageCond_labels
        adf = pd.concat([adf, simdata])

    # Merge the analysis results with the scenario and EIR data
    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on='index', how='inner')

    # Save the processed DataFrame to a CSV file named 'OM_benchmark.csv'
    print(f'Saving OM_benchmark.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_benchmark.csv')), index=False)


def MonthlyBenchmarkAnalyzer(exp, mmi, start_year, grp_channels=['ageGroup', 'index']):
    """
    Run the MonthlyBenchmarkAnalyzer for OpenMalaria experiments to create Benchmark type output keeping the months separate
    Args:
        exp: The experiment object.
        mmi: The measure map object.
        start_year: The starting year for the analysis.
        grp_channels: The group channels for grouping the data (default: ['ageGroup', 'index']).
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup, month and grp_channels
           surveys aggregated across years per month
    Returns:
        None
    """

    print(f"Running MonthlyBenchmarkAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    # Read the monthly EIR data from the CSV file and compute the mean for each index and month
    eir_df = pd.read_csv(os.path.join(wdir, 'OM_EIR_mth.csv'))
    eir_df = eir_df.groupby(['index', 'month'], as_index=False)[['inputEIR', 'simulatedEIR']].mean()

    # Define age groups and labels
    age_groups = exp.agebins  # np.array([0.5,1,2,5,10,15,20,100])
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)
    df = survey_to_date(df, survey_step_days=30, start_year=start_year)

    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / 30))
    num_years = np.floor(len(df['survey'].unique()) / n_surveys_per_year)

    # Sum the surveys for each measure, month, and age group
    df = df.groupby(['index', 'month', 'measure', 'ageGroup'], as_index=False).value.sum()

    # for sum of annual pop not sum of years+months.
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year  
    df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year 

    # Adjust nHost for age groups 0 to 1 based on yearsAtRisk
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]
    sdf = df

    # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframeto write out
    # [[0, 5]] + [[(age_groups[i - 1]), (age_groups[i])] for i in range(1, len(age_groups))]
    age_groups_aggregates =  [[0, 5], [5, 10], [10, 15], [15, 20]]

    adf = pd.DataFrame()
    # Iterate over each month
    for mth in range(1, 13):
        g = sdf.loc[sdf['month'] == mth]

        # Filter and aggregate data for age groups 2 to 10
        age2to10 = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= 2 and age_groups[x - 1] <= 10)
        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(grp_channels).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(grp_channels).value.sum()

        grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
        pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

        # Analyze data for each age group on the plot
        for i in range(0, len(age_groups_aggregates)):
            ages = age_groups_aggregates[i]
            ageCond = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= ages[0] and age_groups[x - 1] <= ages[1])

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
            simdata = pd.DataFrame({'nHost': nHost / num_years,
                                    'prevalence_2to10': pfpr2to10,
                                    'prevalence': prevalence,
                                    'clinical_incidence': clinical_incidence,
                                    'severe_incidence': severe_incidence,
                                    'mortality': mortality})
            simdata['age_group'] = ageCond_labels
            simdata['month'] = mth
            adf = pd.concat([adf, simdata])

    # Merge the analysis results with the scenario and EIR data
    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on=['index', 'month'], how='inner')

    # Save the processed DataFrame to a CSV file named 'OM_benchmark_mth.csv'
    print(f'Saving OM_benchmark_mth.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_benchmark_mth.csv')), index=False)


def MonthlyAgebinAnalyzer(exp, mm, start_year, compr='infer'):
    """
    Run the MonthlyAgebinAnalyzer equivalent for OpenMalaria experiments.
    Args:
        exp: The experiment object.
        mm: The measure map object.
        start_year: The starting year for the analysis.
        compr: The compression type for saving the output CSV file (default: 'infer').
    Saves: CSV dataframe of simulation outcome metrics per agebin, month and grp_channels
           surveys aggregated per surveytimestep (year and month)
    Returns:
        None
    """
    print(f"Running MonthlyAgebinAnalyzer...", flush=True)
    channels = ['index', 'survey', 'ageGroup', 'nHost', 'nPatent', 'nInfect', 'nUncomp', 'nSevere']

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)

    # Remove rows with ageGroup 0 ('all age')
    df.drop(df[df.ageGroup == 0].index, inplace=True)

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
    df2 = df2.rename({'ageGroup': 'agebin_nr'}, axis=1)

    # Define age groups and labels
    age_groups = exp.agebins  # must reflect the xml monitoring section
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels
    age_df = pd.DataFrame({'agebin_nr': df2['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    # Merge the age group data with the previous DataFrame
    df3 = df2.merge(age_df, on='agebin_nr', how='inner')

    # Convert survey data to dates and set the start year
    df3 = survey_to_date(df3, survey_step_days=30, start_year=start_year)

    # Save the processed DataFrame to a CSV file named 'OM_surveyoutput_mth.csv'
    print(f'Saving OM_surveyoutput_mth.csv to {wdir}')
    df3.to_csv((os.path.join(wdir, f'OM_surveyoutput_mth.csv')), index=False, compression=compr)


def AnnualAgebinAnalyzer(exp, mm, start_year, survey_step_days=365, compr='infer'):
    """
    Run the MonthlyAgebinAnalyzer equivalent for OpenMalaria experiments.
    Args:
        exp: The experiment object.
        mm: The measure map object.
        start_year: The starting year for the analysis.
        survey_step_days: The survey step size in days (default: 365).
        compr: The compression type for saving the output CSV file (default: 'infer').
    Saves: CSV dataframe of simulation outcome metrics per agebin, year and grp_channels
           surveys aggregated per surveytimestep (year)
    Returns:
        None
    """
    print(f"Running AnnualAgebinAnalyzer...", flush=True)
    channels = ['index', 'year', 'ageGroup', 'nHost', 'nPatent', 'nInfect', 'nUncomp', 'nSevere']
    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    # Convert experiment data to DataFrame
    df = to_df(exp)
    df = format_df(df)
    df.drop(df[df.ageGroup == 0].index, inplace=True)

    # Convert survey data to dates
    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)
    if survey_step_days == 30:
        df = df.groupby(['index', 'ageGroup', 'year', 'measure'], as_index=False).value.sum()
        df = df.loc[df['year'] < np.max(df.year)]
    elif survey_step_days == 365:
        df = df.groupby(['index', 'ageGroup', 'year', 'measure'], as_index=False).value.mean()
    else:
        raise ValueError('survey_step_days must be 30 or 365')

    # Add measure names to the DataFrame
    mm_df = pd.DataFrame.from_dict(mm, orient='index')
    mm_df['measure'] = mm_df.index
    mm_df['measure_name'] = mm_df[0]
    mm_df = mm_df[['measure', 'measure_name']]

    # Pivot the DataFrame to the desired format
    adf = df.merge(mm_df, on='measure', how='inner')
    df1 = (adf.pivot_table(index=['index', 'year', 'ageGroup'],
                           columns=['measure_name'],
                           values=['value'],
                           aggfunc='first'))
    df1.columns = [''.join(col).replace('value', '') for col in df1.columns]
    df1 = df1.reset_index()

    # only keep selected outcome columns
    df1 = df1[channels]

    # Merge with scenario data
    df2 = df1.merge(scen_df, on='index', how='inner')
    df2 = df2.rename({'ageGroup': 'agebin_nr'}, axis=1)

    # Create age group labels
    age_groups = exp.agebins  # must reflect the xml monitoring section
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels
    age_df = pd.DataFrame({'agebin_nr': df2['agebin_nr'].unique(), 'agebin': age_groups, 'ageGroup': age_group_labels})

    # Merge with age group data
    df3 = df2.merge(age_df, on='agebin_nr', how='inner')

    # Save the processed DataFrame to a CSV file named 'OM_surveyoutput_yr.csv'
    print(f'Saving OM_surveyoutput_yr to {wdir}')
    df3.to_csv((os.path.join(wdir, f'OM_surveyoutput_yr.csv')), index=False, compression=compr)


def AnnualBenchmarkAnalyzer(exp, mmi, start_year, survey_step_days=30, grp_channels=['ageGroup', 'index']):
    """
    Run the AnnualBenchmarkAnalyzer for OpenMalaria experiments to create Benchmark type output keeping the years separate
    Args:
        exp: The experiment object.
        mmi: The measure map object.
        start_year: The starting year for the analysis.
        grp_channels: The group channels for grouping the data (default: ['ageGroup', 'index']).
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup, year and grp_channels
           surveys aggregated across years per month
    Returns:
        None
    """
    print(f"Running AnnualBenchmarkAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(exp.job_directory, 'scenarios.csv'))

    # Read the monthly EIR data from the CSV file and compute the mean for each index and month
    eir_df = pd.read_csv(os.path.join(wdir, 'OM_EIR.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Define age groups and labels
    age_groups = exp.agebins
    age_group_labels = [str(age_groups[i - 1]) + "-" + str(age_groups[i]) for i in range(1, len(age_groups))]
    age_group_labels = [str(0) + "-" + str(age_groups[0])] + age_group_labels

    # Convert the experiment data to a DataFrame and format it
    df = to_df(exp)
    df = format_df(df)
    df = survey_to_date(df, survey_step_days=survey_step_days, start_year=start_year)

    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / survey_step_days))
    num_years = np.floor(len(df['survey'].unique()) / n_surveys_per_year)

    # Sum the surveys for each measure, year, and age group
    df = df.groupby(['index', 'year', 'measure', 'ageGroup'], as_index=False).value.sum()

    # for sum of annual Host population.
    df.loc[(df.measure == mmi['nHost']), 'value'] = df[(df.measure == mmi['nHost'])].value / n_surveys_per_year
    df.loc[(df.measure == mmi['nPatent']), 'value'] = df[(df.measure == mmi['nPatent'])].value / n_surveys_per_year
    
    # Adjust nHost for age groups 0 to 1 based on yearsAtRisk
    yearsAtRisk = np.array(age_groups)
    yearsAtRisk[yearsAtRisk > 1] = 1
    df.loc[(df.measure == mmi['nHost']), 'value'] *= yearsAtRisk[df[(df.measure == mmi['nHost'])].ageGroup - 1]

    # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframeto write out
    # [[0, 5]] + [[(age_groups[i - 1]), (age_groups[i])] for i in range(1, len(age_groups))]
    age_groups_aggregates = [[0, 5], [5, 10], [10, 15], [15, 20]]

    adf = pd.DataFrame()
    # Iterate over each year
    for yr in df['year'].unique():
        g = df.loc[df['year'] == yr]

        # Filter and aggregate data for age groups 2 to 10
        age2to10 = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= 2 and age_groups[x - 1] <= 10)
        nHost2to10 = g[(g.measure == mmi['nHost']) & age2to10].groupby(grp_channels).value.sum()
        nPatent2to10 = g[(g.measure == mmi['nPatent']) & age2to10].groupby(grp_channels).value.sum()

        grp_channels = [ch for ch in grp_channels if ch != 'ageGroup']
        pfpr2to10 = ((nPatent2to10 / nHost2to10).groupby(grp_channels).mean()).rename("prevalence_2to10")

        adf = pd.DataFrame()
        # Analyze data for each age group on the plot
        for i in range(0, len(age_groups_aggregates)):
            ages = age_groups_aggregates[i]
            ageCond = g['ageGroup'].apply(lambda x: age_groups[x - 1] >= ages[0] and age_groups[x - 1] <= ages[1])
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

            prevalence = nPatentInfections /  nHost  # prevalence
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
            simdata['age_group'] = ageCond_labels
            adf = pd.concat([adf, simdata])

    # Merge the analysis results with the scenario and EIR data
    adf.reset_index(inplace=True)
    adf = adf.merge(scen_df, on='index', how='inner')
    adf = adf.merge(eir_df, on='index', how='inner')

    # Save the processed DataFrame to a CSV file named 'OM_benchmark_yr.csv'
    print(f'Saving OM_benchmark_yr.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'OM_benchmark_yr.csv')), index=False)


if __name__ == "__main__":
    # Parse command line arguments
    args = parse_args()
    job_directory = args.directory

    # Load experiment object
    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    start_year = exp.sim_start_year_om
    wdir = os.path.join(exp.sim_out_dir, 'om')
    create_sampleplots = True

    # Determine survey step size
    if exp.om_survey_step == '5d':
        survey_steps = 5
    if exp.om_survey_step == '30d':
        survey_steps = 30
    if exp.om_survey_step == '1y':
        survey_steps = 365

    # Run analyzers
    BaseAnalyzer(exp, mm, saveExtract=False, compr='gzip')
    SurveyAllAgeAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)
    InputEIRAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)

    if survey_steps == 30:
        MonthlyAgebinAnalyzer(exp, mm, start_year=start_year)
        MonthlyBenchmarkAnalyzer(exp, mmi, start_year=start_year)

    BenchmarkAnalyzer(exp, mmi, survey_step_days=survey_steps)
    AnnualBenchmarkAnalyzer(exp, mmi, start_year=start_year, survey_step_days=survey_steps)
    AnnualAgebinAnalyzer(exp, mm, start_year=start_year, survey_step_days=survey_steps)

    # Define tags and channels for sample plots
    exp_tags = [x for x in exp.sweep_list if x != 'seed']
    channels_inset_chart = ['nHost', 'nInfect', 'nPatent', 'totalInfs', 'totalPatentInf', 'nTreatments', 'nUncomp',
                            'nSevere', 'nSeq', 'nIndDeaths',
                            'nDirDeaths', 'inputEIR', 'simulatedEIR', 'expectedDirectDeaths',
                            'expectedSevere']  # 'expectedIndirectDeaths',

    # Create sample plots if specified
    if create_sampleplots:
        all_age_sample_plot(wdir, exp_tags, channels_inset_chart)
        sample_plot_yr(wdir, exp_tags)
        emodom = ['OpenMalaria']
        if survey_steps == 30:
            sample_plot_mth(wdir, exp_tags)

            sweepvar = 'annual_input_EIR'
            monthly_trends(wdir= exp.sim_out_dir,  emodom=emodom, channel='clinical_incidence', sweepvar=sweepvar)
            monthly_trends(wdir= exp.sim_out_dir, emodom=emodom, channel='severe_incidence', sweepvar=sweepvar)
            monthly_trends(wdir= exp.sim_out_dir, emodom=emodom, channel='prevalence', sweepvar=sweepvar)
            monthly_trends(wdir= exp.sim_out_dir, emodom=emodom,  channel='prevalence_2to10', sweepvar=sweepvar)
            monthly_trends(wdir= exp.sim_out_dir,  emodom=emodom, channel='simulatedEIR', sweepvar=sweepvar)
        
        sweepvar ='cm_clinical'
        prevalence2to10_to_incidence(wdir= exp.sim_out_dir, emodom=emodom, channel='prevalence', y_lim=1)
        prevalence2to10_to_incidence(wdir= exp.sim_out_dir, emodom=emodom, channel='clinical_incidence', y_lim=6)
        prevalence2to10_to_incidence(wdir= exp.sim_out_dir, emodom=emodom, channel='severe_incidence', y_lim=0.1)
        eir_to_prevalence2to10(wdir= exp.sim_out_dir, emodom=emodom, sweepvar=sweepvar, eir_val='simulatedEIR')
        eir_to_prevalence2to10(wdir= exp.sim_out_dir,  emodom=emodom,  sweepvar=sweepvar, eir_val='inputEIR')
        input_to_simulated_eir(wdir= exp.sim_out_dir,  emodom=emodom, sweepvar=sweepvar)
    
