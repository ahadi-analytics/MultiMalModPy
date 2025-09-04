import os
import sys
import argparse
import pickle
import datetime
import pandas as pd
import numpy as np
import math

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
from utility.experiment import LoadExperiment


def parse_args():
    """
    Parse command-line arguments for simulation specifications.
    This function sets up the argument parser to handle command-line inputs,
    specifically for specifying the job directory and an optional experiment ID.
    The job directory is required to locate the `exp.obj` file.

    Args:
        None

    Returns:
        Namespace: A namespace object containing the parsed command-line arguments.
        The attributes include:
            - job_dir (str): The job directory where `exp.obj` is located.
    """

    # Set the description for the argument parser
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)

    # Add the required argument for the job directory
    parser.add_argument(
        "-dir",
        "--directory",
        type=str,
        required=True,
        help="Job Directory of exp.obj")
    parser.add_argument('--mpv',
                        action='store_true',
                        help='Analyze malariasimulation runs with parameter variation (default: False).')
    return parser.parse_args()


def convert_to_long(output, age_groups):
    """
    Convert the dataframe to long form for the desired columns.

    Args:
        output (pandas.DataFrame): Input dataframe.
        age_min (list): Minimum age values.

        age_max (list): Maximum age values.

    Returns:
        pandas.DataFrame: Long-form output.
    """
    result = []
    for pair in age_groups:
        agemin = pair[0]
        agemax = pair[1]
        data = {
            'index': output['index'],  # unique identifier across seeds & parameter sweep combinations
            'timestep': output['timestep'],
            'month': output['month'],
            'year': output['year'],
            'ageGroup': f"{int(np.floor(agemin / 365))}-{int(np.floor(agemax / 365))}",
            'age_lower': agemin,
            'age_upper': agemax,
            'nPopulation': output['S_count'] + output['A_count'] + output['U_count'] + output['Tr_count'] + output[
                'D_count'],
            'n_age': output[f"n_age_{agemin}_{agemax}"],
            'prev': output[f"prev_{agemin}_{agemax}"],
            'n_inc': output[f"n_inc_{agemin}_{agemax}"],
            'n_inc_clinical': output[f"n_inc_clinical_{agemin}_{agemax}"],
            'n_inc_severe': output[f"n_inc_severe_{agemin}_{agemax}"],
            'prevalence_2to10': output['prevalence_2to10'],
            'n_infectious_mos': output['Im_gamb_count'],
            'n_total_mos_pop': output['Sm_gamb_count'] + output['Pm_gamb_count'] + output['Im_gamb_count'],
            'EIR_gamb': output['EIR_gamb']
        }
        result.append(pd.DataFrame(data))
    output = pd.concat(result, ignore_index=True)
    return output


def post_processing(exp, job_directory, pv_suffix=''):
    """
    Perform post-processing of malariasimulation simulation output data.
    This was previously done in R, but was brought to python to match the two other models.

    Args:
        exp: Experiment object.
        job_directory: Directory containing raw simulation output files.

    Saves:
        {i}_daily.csv: for each simulation {i} in an experiment, saves the processed daily output.
        daily.csv: combines all the processed daily outputs for each simulation in the experiment.

    Returns:
        None
    """

    agebins_days = [a * 365 for a in exp.agebins]

    columns_to_keep = ['timestep', 'Sm_gamb_count', 'Pm_gamb_count', 'Im_gamb_count', 'EIR_gamb', 'S_count',
                       'A_count', 'U_count', 'Tr_count', 'D_count', 'index']

    columns_with_ages = ['n_age', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_detect_lm']

    needed_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age', 'nPopulation', 'prevalence_2to10', 'prev',
                       'index', 'timestep', 'month', 'year', 'ageGroup', 'age_upper', 'EIR_gamb',
                       'n_infectious_mos', 'n_total_mos_pop']

    age_groups = [[0, int(agebins_days[0] // 1)]]  # Start with the first age group [0, 182]
    age_groups.extend(
        [int(agebins_days[i] // 1) + 1, int(agebins_days[i + 1] // 1)] for i in range(len(agebins_days) - 1))

    for z in columns_with_ages:
        for i in age_groups:
            columns_to_keep.append(f'{z}_{i[0]}_{i[1]}')

    daily = pd.DataFrame()
    for i in range(1, exp.nexps + 1):
        df = pd.read_csv(os.path.join(job_directory, 'malariasimulation_jobs', f'{i}_out{pv_suffix}.csv'))
        df = df.loc[:, df.columns.isin(columns_to_keep + ['n_detect_lm_730_3650', 'n_age_730_3650'])]
        days_in_months = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        days_in_months = np.repeat(days_in_months, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        days_in_months = np.tile(days_in_months, int(max(df['timestep']) / 365))
        df['month'] = days_in_months
        df['year'] = np.floor(df['timestep'] / 365.000001).astype(int)
        for pair in age_groups:
            df[f'prev_{pair[0]}_{pair[1]}'] = df[f'n_detect_lm_{pair[0]}_{pair[1]}'] / df[f'n_age_{pair[0]}_{pair[1]}']

        df['prevalence_2to10'] = df['n_detect_lm_730_3650'] / df['n_age_730_3650']
        output = convert_to_long(df, age_groups)
        output['year'] = output['year'] + exp.sim_start_year_malariasimulation
        output = output[needed_channels]
        output = output[output['timestep'] > (exp.malariasimulation_burnin * 365)]
        output['timestep'] = output['timestep'] - (exp.malariasimulation_burnin * 365)
        # output.to_csv(os.path.join(job_directory, f'malariasimulation_jobs/{i}_daily{pv_suffix}.csv'), index=False) # not need to be written out per default, since daily.csv is used
        daily = pd.concat([daily, output], axis=0)
    daily.to_csv((os.path.join(wdir, f'daily{pv_suffix}.csv')), index=False)


def InputEIRAnalyzer(jdir, wdir, daily=False, pv_suffix=''):
    """
    Run the InputEIRAnalyzer for malariasimulation experiments.
    This function generates daily or aggregated EIR (Entomological Inoculation Rate) reports.
    It filters and processes relevant columns, and saves the results as CSV files.

    Args:
        jdir (str): Path to the directory containing the scenario data file `scenarios_wseeds_mpv.csv`.
        wdir (str): Path to the directory containing the simulation data file `daily.csv`, and where
            output CSV files will be saved.
        daily (bool, optional): If `True`, only the daily EIR data (`EIR_daily.csv`) will be processed and saved.
            If `False`, monthly, yearly, and multi-year mean EIR files will also be generated and saved.
            Defaults to `False`.

    Raises:
        FileNotFoundError: If the required `scenarios_wseeds_mpv.csv` or `daily.csv` files are not found in `jdir` or `wdir`.
        ValueError: If data columns necessary for processing (e.g., 'EIR_gamb') are missing in the input files.

    Saves:
        One or more CSV files based on the `daily` flag:
            - `EIR_daily.csv`: Contains daily EIR data, if `daily=True`.
            - `EIR_mth.csv`: Contains monthly aggregated EIR data, if `daily=False`.
            - `EIR_yr.csv`: Contains yearly aggregated EIR data, if `daily=False`.
            - `EIR.csv`: Contains mean EIR over the monitoring period, if `daily=False`.
    Returns:
        None
    """
    print("\nRunning InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds_mpv.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns

    columns_to_keep = ['index', 'timestep', 'month', 'year', 'nPopulation', 'EIR_gamb', 'n_infectious_mos',
                       'n_total_mos_pop']

    df = pd.read_csv(os.path.join(wdir, f'daily{pv_suffix}.csv'))
    df = df[df['ageGroup'] == '0-0']
    df = df[columns_to_keep]
    df['EIR_gamb'] = df['EIR_gamb'] / df['nPopulation']
    if daily:
        df_daily = df.merge(scen_df, on='index', how='inner')
        columns_to_keep = ['index', 'seed', 'timestep', 'month', 'year', 'nPopulation', 'EIR_gamb',
                           'cm_clinical', 'seasonality', 'scen_id', 'num_seeds', 'cm_start', 'cm_severe',
                           'n_infectious_mos', 'n_total_mos_pop', 'target_output_values']
        columns_to_keep = [col for col in columns_to_keep if col in df_daily.columns]
        df_daily = df_daily[columns_to_keep]
        df_daily = df_daily.rename({'EIR_gamb': 'eir'}, axis=1)
        print(f'Saving EIR_daily{pv_suffix}.csv to {wdir}')
        df_daily.to_csv((os.path.join(wdir, f'EIR_daily{pv_suffix}.csv')), index=False)

    else:
        # Monthly aggregation - keep months and years
        mean_channels = ['n_infectious_mos', 'n_total_mos_pop']
        df_mth = df.groupby(['index', 'month', 'year'], as_index=False)['EIR_gamb'].sum()
        vdf_mth = df.groupby(['index', 'month', 'year'], as_index=False)[mean_channels].mean()
        df_mth = df_mth.merge(vdf_mth, on=['index', 'month', 'year'], how='inner')
        df_mth = df_mth.merge(scen_df, on='index', how='inner')
        df_mth = df_mth.rename({'EIR_gamb': 'eir'}, axis=1)
        print(f'Saving EIR_mth{pv_suffix}.csv to {wdir}')
        df_mth.to_csv((os.path.join(wdir, f'EIR_mth{pv_suffix}.csv')), index=False)

        # Yearly aggregation - keep years
        df_yr = df.groupby(['index', 'year'], as_index=False)['EIR_gamb'].sum()
        vdf_yr = df.groupby(['index', 'year'], as_index=False)[mean_channels].mean()
        df_yr = df_yr.merge(vdf_yr, on=['index', 'year'], how='inner')
        df_yr = df_yr.merge(scen_df, on='index', how='inner')
        df_yr = df_yr.rename({'EIR_gamb': 'eir'}, axis=1)
        print(f'Saving EIR_yr{pv_suffix}.csv to {wdir}')
        df_yr.to_csv((os.path.join(wdir, f'EIR_yr{pv_suffix}.csv')), index=False)

        # Mean over monitoring period
        nyears = len(df['year'].unique())
        df_yr = df.groupby(['index'], as_index=False)['EIR_gamb'].sum()
        vdf_yr = df.groupby(['index'], as_index=False)[mean_channels].mean()
        df_yr = df_yr.merge(vdf_yr, on=['index'], how='inner')
        df_yr['EIR_gamb'] = df_yr['EIR_gamb'] / nyears
        df_yr['n_infectious_mos'] = df_yr['n_infectious_mos'] / nyears
        df_yr['n_total_mos_pop'] = df_yr['n_total_mos_pop'] / nyears
        df_yr = df_yr.merge(scen_df, on='index', how='inner')
        df_yr = df_yr.rename({'EIR_gamb': 'eir'}, axis=1)
        print(f'Saving EIR{pv_suffix}.csv to {wdir}')
        df_yr.to_csv((os.path.join(wdir, f'EIR{pv_suffix}.csv')), index=False)


def SurveyAllAgeAnalyzer(jdir, wdir, sweep_variables, pv_suffix=''):
    """
    Run the SurveyAllAgeAnalyzer for malariasimulation outputs.
    This function postprocesses outputs by age-groups across dates and variables defined by `sweep_variables`.
    The function reads, filters, and aggregates relevant columns, and then saves the processed data to a CSV file.

    Args:
        jdir (str): Path to the directory containing the scenario data file `scenarios_wseeds_mpv.csv`.
        wdir (str): Path to the directory containing the experiment data file `daily.csv`, and where
            the output CSV file will be saved.
        sweep_variables (list of str): List of column names used as grouping variables in the aggregation.

    Raises:
        FileNotFoundError: If the required `scenarios_wseeds_mpv.csv` or `daily.csv` files are not found in `jdir` or `wdir`.
        ValueError: If data columns necessary for processing (e.g., 'n_inc') are missing in the input files.

    Saves:
        `All_Age_Outputs.csv`

    Returns:
        None
    """

    print("\nRunning SurveyAllAgeAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds_mpv.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'target_output_values'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns

    # Read experiment data daily
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev', 'n_infectious_mos', 'n_total_mos_pop', 'EIR_gamb']
    columns_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup',
                       'age_upper'] + sum_channels + mean_channels
    df = pd.read_csv(os.path.join(wdir, f'daily{pv_suffix}.csv'))
    df = df[columns_to_keep]

    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['day'] = df['timestep'] % 365
    df['date'] = df.apply(lambda x: datetime.date(int(x['year']), 1, 1) + datetime.timedelta(int(x['day']) - 1), axis=1)

    # Sum the values of the age groups
    # Aggregate data per date and sweep_variables using sum and mean specific to outcome channel

    sdf = df.groupby(['date'] + sweep_variables)[sum_channels].agg('sum').reset_index()
    mdf = df.groupby(['date'] + sweep_variables)[mean_channels].agg('mean').reset_index()
    adf = pd.merge(left=sdf, right=mdf, on=(sweep_variables + ['date']))

    # Merge with the scenario data
    adf = adf.merge(scen_df, on='index', how='inner')

    # Save the processed DataFrame to a CSV file named 'All_Age_Outputs.csv'
    print(f'Saving All_Age_Outputs.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, f'All_Age_Outputs{pv_suffix}.csv')), index=False)


def TimeavrgAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None, pv_suffix=''):
    """
    Run the TimeavrgAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups aggregated over the monitoring period.

    Args:
        jdir (str): Path to the directory containing simulation job data.
        wdir (str): Path to the working directory.
        sweep_variables (list): List of sweep variables.
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.

    Saves:
        mmmpy_timeavrg.csv
        interpolation_data.csv (if exp.run_mode == 'calibration')

    Returns:
        None
    """
    print("\nRunning TimeavrgAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, f'EIR{pv_suffix}.csv'))
    eir_df = eir_df[['index', 'target_output_values', 'eir', 'n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age']
    mean_channels = ['prevalence_2to10']
    columns_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup', 'prev', 'nPopulation',
                       'age_upper'] + sum_channels + mean_channels

    df = pd.read_csv(os.path.join(wdir, f'daily{pv_suffix}.csv'), usecols=columns_to_keep)
    df = df[columns_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n_age']

    df_pfpr2to10 = df.groupby(sweep_variables)[mean_channels].agg('mean').reset_index()

    ## Aggregate years
    n_surveys_per_year = 365
    n_surveys = round(len(df['timestep'].unique()), 0)
    n_years = round(n_surveys / 365, 0)
    sum_channels += ['n_prev']
    df = df.groupby(sweep_variables + ['agebin'])[sum_channels].agg('sum').reset_index()
    df['n_age'] = df['n_age'] / n_surveys_per_year
    df['n_prev'] = df['n_prev'] / n_surveys_per_year

    cdf = pd.DataFrame()

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            adf = adf.groupby(sweep_variables)[['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age']].agg(
                'sum').reset_index()
            adf['prevalence'] = adf['n_prev'] / (adf['n_age'])

            # (events per person per annum)
            adf['clinical_incidence'] = adf['n_inc_clinical'] / adf['n_age']
            adf['severe_incidence'] = adf['n_inc_severe'] / adf['n_age']
            adf['ageGroup'] = ageCond_labels
            adf['n_age'] = adf['n_age'] / n_years
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables)
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds_mpv.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'target_output_values'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on='index', how='inner')

    # Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence'] * ((1 - 0.42) * cdf['cm_clinical'] + (1 - cdf['cm_clinical'])) * ( 1 / 0.8)
    # cdf['severe_incidence'] = cdf['severe_incidence'] * (0.5 * cdf['cm_severe'] + (1 - cdf['cm_severe']))

    # Rename columns for standardization across models
    cdf['mortality'] = ''

    cdf = cdf.rename({'n_age': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])

    print(f'Saving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file named 'mmmpy_timeavrg.csv'
    cdf.to_csv((os.path.join(wdir, f'mmmpy_timeavrg{pv_suffix}.csv')), index=False)

    if exp.run_mode == 'calibration' and pv_suffix == None:
        u5 = cdf[cdf['ageGroup'] == '0-5'].groupby('scen_id')['clinical_incidence'].agg('mean').reset_index()
        u5 = u5.rename(columns={'clinical_incidence': 'clinical_incidence_U5'})
        all_ages = cdf[cdf['ageGroup'] == '0-100'].groupby('scen_id')['clinical_incidence'].agg('mean').reset_index()
        cdf = cdf[cdf['ageGroup'] == '0-100']
        cdf = cdf.groupby(['scen_id', 'transmission_intensity_malariasimulation', 'seasonality', 'cm_clinical', 'cm_severe'])[
            ['eir', 'prevalence_2to10', 'prevalence', 'severe_incidence', 'n_total_mos_pop']].agg(
            'mean').reset_index()
        cdf = cdf.merge(all_ages, on='scen_id')
        cdf = cdf.merge(u5, on='scen_id')
        cdf = cdf.drop(['scen_id'], axis=1)
        cdf['models'] = 'malariasimulation'
        cdf['pop_size'] = exp.malariasimulation_pop_size
        cdf['importaion'] = False
        cdf = cdf.rename(columns={'transmission_intensity_malariasimulation': 'input_target'})
        cdf.to_csv((os.path.join(wdir, 'interpolation_data.csv')), index=False)
        cdf.to_csv((os.path.join(exp.interp_path, 'malariasimulation', f'{exp.exp_name}_interpolation_data.csv')),
                   index=False)


def AnnualAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None, pv_suffix=''):
    """
    Process annual data for malariasimulation experiments, generating a dataframe of malaria metrics over time
    by age group. Aggregates daily data into yearly sums, calculates prevalence and incidence rates,
    and merges experimental metadata for analysis.

    Args:
        jdir (str): Path to the directory containing scenario job data, including metadata.
        wdir (str): Path to the working directory containing input data CSV files and where the output will be saved.
        sweep_variables (list): List of columns that identify experimental sweeps (e.g., parameter values).
        age_groups_aggregates (list, optional): List of age ranges for aggregating results. Each entry is a [min_age, max_age] list.
            Defaults to None, in which case it uses predefined age bins.

    Saves:
        mmmpy_yr.csv

    Returns:
        None
    """
    print("\nRun AnnualAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, f'EIR_yr{pv_suffix}.csv'))
    eir_df = eir_df[['index', 'year', 'target_output_values', 'eir', 'n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age']
    mean_channels = ['prevalence_2to10']
    columns_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup',
                       'age_upper', 'prev', 'nPopulation'] + sum_channels + mean_channels

    # df = load_combined_daily_output(jdir, columns_to_keep)
    df = pd.read_csv(os.path.join(wdir, f'daily{pv_suffix}.csv'), usecols=columns_to_keep)
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n_age']
    sum_channels += ['n_prev']

    df_pfpr2to10 = df.groupby(sweep_variables + ['year'])[mean_channels].agg('mean').reset_index()

    ## Aggregate to years
    n_surveys_per_year = int(round(len(df['timestep'].unique()) / len(df['year'].unique()), 0))
    df = df.groupby(sweep_variables + ['agebin', 'year'])[sum_channels].agg('sum').reset_index()
    df['n_age'] = df['n_age'] / n_surveys_per_year
    df['n_prev'] = df['n_prev'] / n_surveys_per_year

    cdf = pd.DataFrame()

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            adf = adf.groupby(sweep_variables + ['year'])[sum_channels].agg('sum').reset_index()
            adf['prevalence'] = adf['n_prev'] / (adf['n_age'])
            # (events per person per annum)
            # adf['incidence'] = adf['n_inc'] / (adf['n_age'])
            adf['clinical_incidence'] = adf['n_inc_clinical'] / (adf['n_age'])
            adf['severe_incidence'] = adf['n_inc_severe'] / (adf['n_age'])
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['year'])
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds_mpv.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'target_output_values'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on=['index', 'year'], how='inner')

    # Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence'] * ((1 - 0.42) * cdf['cm_clinical'] + (1 - cdf['cm_clinical'])) * (
                1 / 0.8)
    # cdf['severe_incidence'] = cdf['severe_incidence'] * (0.5 * cdf['cm_severe'] + (1 - cdf['cm_severe']))

    # Rename columns for alignment with OpenMalaria results
    cdf = cdf.rename({'n_age': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])

    # Save the processed DataFrame to a CSV file
    print(f'Saving outputs to: {wdir}')
    cdf.to_csv((os.path.join(wdir, f'mmmpy_yr{pv_suffix}.csv')), index=False)


def MonthlyAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None, pv_suffix=''):
    """
    Process monthly data for malariasimulation experiments, generating a dataframe of malaria metrics over time
    by age group. Aggregates daily data into monthly averages or sums, calculates prevalence and incidence rates,
    and merges experimental metadata for analysis.

    Args:
        jdir (str): Path to the directory containing scenario job data, including metadata.
        wdir (str): Path to the working directory containing input data CSV files and where the output will be saved.
        sweep_variables (list): List of columns that identify experimental sweeps (e.g., parameter values).
        age_groups_aggregates (list, optional): List of age ranges for aggregating results. Each entry is a [min_age, max_age] list.
            Defaults to None, in which case it uses predefined age bins.

    Saves:
        mmmpy_mth.csv

    Returns:
        None
    """
    print("\nRunning MonthlyAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, f'EIR_mth{pv_suffix}.csv'))
    eir_df = eir_df.groupby(sweep_variables + ['month', 'year'])[
        ['eir', 'target_output_values', 'n_total_mos_pop']].agg(
        'mean').reset_index()  # mean across runs per month and year
    eir_df = eir_df[['index', 'month', 'year', 'target_output_values', 'eir', 'n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    mean_channels = ['prevalence_2to10']
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age']
    columns_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup', 'age_upper', 'nPopulation',
                       'prev'] + mean_channels + sum_channels

    df = pd.read_csv(os.path.join(wdir, f'daily{pv_suffix}.csv'))
    df = df[columns_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n_age']
    sum_channels += ['n_prev']

    df_pfpr2to10 = df.groupby(sweep_variables + ['month', 'year'])[mean_channels].agg('mean').reset_index()

    ## Aggregate days to month and years
    df = df.groupby(sweep_variables + ['agebin', 'month', 'year'])[sum_channels].agg('sum').reset_index()
    df['n_age'] = df['n_age'] / (365 / 12)
    df['n_prev'] = df['n_prev'] / (365 / 12)

    cdf = pd.DataFrame()

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            ## Aggregate by age group
            adf = adf.groupby(sweep_variables + ['month', 'year'])[sum_channels].agg('sum').reset_index()

            adf['prevalence'] = adf['n_prev'] / (adf['n_age'])
            # events per person per annum (annualized)
            # adf['incidence'] = (adf['n_inc'] / adf['n_age']/ 12)
            adf['clinical_incidence'] = (adf['n_inc_clinical'] / (adf['n_age'] / 12))
            adf['severe_incidence'] = (adf['n_inc_severe'] / (adf['n_age'] / 12))
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['month', 'year'])
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds_mpv.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'target_output_values'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on=['index', 'month', 'year'], how='inner')

    # Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence'] * ((1 - 0.42) * cdf['cm_clinical'] + (1 - cdf['cm_clinical'])) * (
                1 / 0.8)
    # cdf['severe_incidence'] = cdf['severe_incidence'] * (0.5 * cdf['cm_severe'] + (1 - cdf['cm_severe']))

    # Rename columns for alignment with OpenMalaria results
    cdf = cdf.rename({'n_age': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])
    cdf['date'] = cdf.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)

    print(f'Saving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file
    cdf.to_csv((os.path.join(wdir, f'mmmpy_mth{pv_suffix}.csv')), index=False)


def FiveDayAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None, intervention_analyzer_columns=None,
                          pv_suffix=''):
    """
    Run the FiveDayAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups over time (5-day intervals and years).
    This function processes simulation outputs, aggregating malaria-related metrics every five days
    and across specified age bins and sweep variables. It outputs metrics like prevalence, clinical
    incidence, and severe incidence per age group. The processed data is saved to a CSV file.

    Args:
        jdir (str): Path to the directory containing the scenario data file `scenarios_wseeds_mpv.csv`.
        wdir (str): Path to the working directory, where the experiment data (`daily.csv`) is stored and output is saved.
        sweep_variables (list of str): List of column names used for grouping in the aggregation.
        age_groups_aggregates (list of lists, optional): List of age ranges to aggregate in the form of
            [[min_age, max_age], ...]. Defaults to standard age bins if not provided.
        intervention_analyzer_columns (list, optional): List of intervention specific columns that need to be included
            in the final mmmpy_5day.csv file.

    Raises:
        FileNotFoundError: If required files (`daily.csv`, `EIR_daily.csv`, or `scenarios_wseeds_mpv.csv`) are missing.
        ValueError: If expected data columns are not found in the input files.

    Saves:
        mmmpy_5day.csv

    Returns:
        None
    """
    print("\nRunning FiveDayAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, f'EIR_daily{pv_suffix}.csv'))
    eir_df = eir_df.groupby(sweep_variables + ['year', 'timestep'])[
        ['eir', 'target_output_values', 'n_infectious_mos', 'n_total_mos_pop']].agg('mean').reset_index()
    eir_df = eir_df[['index', 'timestep', 'year', 'eir', 'n_infectious_mos', 'n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    mean_channels = ['prevalence_2to10']
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age']
    columns_to_keep = ['index', 'timestep', 'year', 'ageGroup', 'age_upper', 'nPopulation',
                       'prev'] + sum_channels + mean_channels

    df = pd.read_csv(os.path.join(wdir, f'daily{pv_suffix}.csv'), usecols=columns_to_keep)
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n_age']
    sum_channels += ['n_prev']

    df['day'] = (df['timestep'] - 1) % 365 + 1
    df['5day'] = df['day'].apply(lambda x: 5 * math.ceil(x / 5))
    df = df.groupby(sweep_variables + ['agebin', '5day', 'year']).agg({'n_prev': ['sum'],
                                                                       'n_inc': ['sum'],
                                                                       'n_inc_clinical': ['sum'],
                                                                       'n_inc_severe': ['sum'],
                                                                       'n_age': ['sum'],
                                                                       'nPopulation': ['mean'],
                                                                       'prevalence_2to10': ['mean'],
                                                                       'prev': ['mean']}).reset_index()
    df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={'5day': 'day'})

    ## EIR
    eir_df['day'] = (eir_df['timestep'] - 1) % 365 + 1
    eir_df['5day'] = eir_df['day'].apply(lambda x: 5 * math.ceil(x / 5))
    eir_df = eir_df.groupby(sweep_variables + ['5day', 'year']).agg(
        {'eir': ['sum'], 'n_infectious_mos': ['mean'],
         'n_total_mos_pop': ['mean'], 'timestep': ['max']}).reset_index()
    eir_df.columns = eir_df.columns.get_level_values(0)
    eir_df = eir_df.rename(columns={'5day': 'day'})
    df_pfpr2to10 = df.groupby(sweep_variables + ['day', 'year'])[['prevalence_2to10']].agg('mean').reset_index()
    df = df[sweep_variables + ['agebin', 'day', 'year'] + sum_channels]

    df['n_age'] = df['n_age'] / (365 / 73)
    df['n_prev'] = df['n_prev'] / (365 / 73)

    cdf = pd.DataFrame()

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            ## Aggregate by age group
            adf = adf.groupby(sweep_variables + ['day', 'year'])[sum_channels].agg('sum').reset_index()

            adf['prevalence'] = adf['n_prev'] / (adf['n_age'])
            # events per person per annum (annualized)
            # adf['incidence'] = (adf['n_inc'] / adf['n_age']/ 12)
            adf['clinical_incidence'] = (adf['n_inc_clinical'] / (adf['n_age'] / 73))  ## 5-Daily to annualized incidence
            adf['severe_incidence'] = (adf['n_inc_severe'] / (adf['n_age'] / 73))
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['day', 'year'])
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds_mpv.csv'))
    scen_df = scen_df.drop(['entomology_mode'], axis=1, errors='ignore')
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')

    cdf = cdf.merge(eir_df, on=['index', 'day', 'year'], how='inner')

    # Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence'] * ((1 - 0.42) * cdf['cm_clinical'] + (1 - cdf['cm_clinical'])) * (
                1 / 0.8)
    # cdf['severe_incidence'] = cdf['severe_incidence'] * (0.5 * cdf['cm_severe'] + (1 - cdf['cm_severe']))

    # Rename columns for alignment with OpenMalaria results
    cdf = cdf.rename({'n_age': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])

    # Save the processed DataFrame to a CSV file
    columns_to_keep = ['scen_id', 'seed', 'timestep', 'day', 'year', 'cm_clinical', 'seasonality',
                       'target_output_values',
                       'ageGroup', 'eir', 'prevalence_2to10', 'prevalence',
                       'clinical_incidence', 'severe_incidence', 'n_total_mos_pop', 'n_infectious_mos']
    columns_to_keep += [column for column in intervention_analyzer_columns if column in cdf.columns]
    cdf = cdf[columns_to_keep]
    print(f'Saving outputs to: {wdir}')
    cdf.to_csv((os.path.join(wdir, f'mmmpy_5day{pv_suffix}.csv')), index=False)


def DailyAgeBinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None, pv_suffix=''):
    """
    Run the DailyAgeBinAnalyzer equivalent for malariasimulation experiments.
    This function processes daily simulation outputs, aggregating malaria-related metrics across specified
    age bins and sweep variables. The function reads, filters, and aggregates relevant columns,
    including age group aggregates if provided, and saves the processed data to a CSV file.

    Args:
        jdir (str): Path to the directory containing the scenario data file `scenarios_wseeds_mpv.csv`.
        wdir (str): Path to the directory containing the experiment data file `daily.csv`, and where
            the output CSV file will be saved.
        sweep_variables (list of str): List of column names used as grouping variables in the aggregation.
        age_groups_aggregates (list of lists, optional): List of age ranges to aggregate in the form of
            [[min_age, max_age], ...]. If None, default age bins will be used.

    Raises:
        FileNotFoundError: If the required `scenarios_wseeds_mpv.csv` or `daily.csv` files are not found in `jdir` or `wdir`.
        ValueError: If data columns necessary for processing (e.g., 'n_inc') are missing in the input files.

    Saves:
        `mmmpy_daily.csv`

    Returns:
        None
    """
    print("\nRunning DailyAgeBinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n_age']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev', 'n_infectious_mos', 'n_total_mos_pop']
    columns_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup',
                       'age_upper'] + sum_channels + mean_channels
    # df = load_combined_daily_output(jdir, columns_to_keep)
    df = pd.read_csv(os.path.join(wdir, 'daily.csv'), usecols=columns_to_keep)
    df['n_prev'] = df['prev'] * df['n_age']
    df['incidence'] = (df['n_inc'] / df['n_age'])
    df['clinical_incidence'] = (df['n_inc_clinical'] / (df['n_age'] / 365))  ## Daily to annualized incidence
    df['severe_incidence'] = (df['n_inc_severe'] / (df['n_age'] / 365))
    df['agebin'] = round(df['age_upper'] / 365, 1)

    # Align to common output terminology used
    df = df.rename({'n_age': 'nHost', 'n_inc': 'nInfect', 'n_inc_clinical': 'nUncomp', 'n_inc_severe': 'nSevere',
                    'prev': 'prevalence'}, axis=1)

    ### Add age group aggregates
    cdf = pd.DataFrame()
    # Age group labels
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df['agebin'] > ages[0]) & (df['agebin'] <= ages[1])]
        if adf.empty:
            pass
        else:
            adf = adf.groupby(sweep_variables + ['timestep', 'month', 'year']).agg(
                nHost=('nHost', 'sum'),
                prevalence=('prevalence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                clinical_incidence=('clinical_incidence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                severe_incidence=('severe_incidence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                prevalence_2to10=('prevalence_2to10', 'mean')
            ).reset_index()
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    ## Add scenarios variables
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds_mpv.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'target_output_values'], axis=1,
                           errors='ignore')  ## remove EMOD specific columns

    df = cdf.merge(scen_df, on=sweep_variables, how='inner')
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_daily.csv'))
    eir_df = eir_df[['index', 'timestep', 'month', 'year', 'eir', 'target_output_values']]
    df = df.merge(eir_df, on=['index', 'timestep', 'month', 'year'], how='inner')

    # Severe Incidence Recalculation
    df['severe_incidence'] = df['severe_incidence'] * ((1 - 0.42) * df['cm_clinical'] + (1 - df['cm_clinical'])) * (
                1 / 0.8)
    # df['severe_incidence'] = df['severe_incidence'] * (0.5 * df['cm_severe'] + (1 - df['cm_severe']))

    # Let's limit the output of daily, so its a little more reasonable for us to process.
    columns_to_keep = ['index', 'scen_id', 'seed', 'ageGroup', 'timestep', 'eir', 'n_infectious_mos',
                       'n_total_mos_pop', 'nHost', 'clinical_incidence', 'severe_incidence', 'prevalence',
                       'prevalence_2to10']

    # Iterate over columns to drop and check if they exist
    columns_to_keep = [col for col in columns_to_keep if col in df.columns]
    df = df[columns_to_keep]

    # Save the processed DataFrame to a CSV file
    print(f'Saving outputs to: {wdir}')
    df.to_csv((os.path.join(wdir, f'mmmpy_daily{pv_suffix}.csv')), index=False)


if __name__ == "__main__":
    args = parse_args()
    job_directory = args.directory
    mpv = args.mpv
    if mpv:
        suffix ='_pv'
    else:
        suffix = ''

    # Load experiment object
    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)

    wdir = os.path.join(exp.output_directory, 'malariasimulation')
    sweep_variables = ['index']
    all_age_sp = False  # False
    seeds = exp.num_seeds
    age_groups_aggregates = exp.age_groups_aggregates

    # Python Post-Processing
    post_processing(exp, job_directory, pv_suffix=suffix)

    # Run analyzers
    InputEIRAnalyzer(job_directory, wdir, pv_suffix = suffix)
    if 'daily' in exp.analyzer_list or '5day' in exp.analyzer_list:
        InputEIRAnalyzer(job_directory, wdir, daily=True, pv_suffix=suffix)

    # Age groups aggregated to all and time intervals are kept unaggregated (1day)
    if 'surveyallage' in exp.analyzer_list:
        SurveyAllAgeAnalyzer(job_directory, wdir, sweep_variables, pv_suffix=suffix)
    ## Aggregated timeseries per age groups
    if 'timeavrg' in exp.analyzer_list:
        TimeavrgAgebinAnalyzer(job_directory, wdir, sweep_variables, age_groups_aggregates, pv_suffix=suffix)
    ## Annual timeseries per age groups
    if 'annual' in exp.analyzer_list:
        AnnualAgebinAnalyzer(job_directory, wdir, sweep_variables, age_groups_aggregates, pv_suffix=suffix)
    ## Monthly timeseries per age groups
    if 'monthly' in exp.analyzer_list:
        MonthlyAgebinAnalyzer(job_directory, wdir, sweep_variables, age_groups_aggregates, pv_suffix=suffix)
    ## 5 day timeseries per age groups
    if '5day' in exp.analyzer_list:
        FiveDayAgebinAnalyzer(job_directory, wdir, sweep_variables, age_groups_aggregates,
                              intervention_analyzer_columns=exp.intervention_analyzer_columns, pv_suffix=suffix)
    ## Daily timeseries per age groups
    if 'daily' in exp.analyzer_list:
        DailyAgeBinAnalyzer(job_directory, wdir, sweep_variables, pv_suffix=suffix)
