import os
import argparse
import pickle
import datetime
import pandas as pd
import numpy as np
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
        "-o",
        "--job_dir",
        type=str,
        required=True,
        help="Job Directory of exp.obj")
    return parser.parse_args()


def load_combined_daily_output(job_directory, num_seeds):
    daily = pd.DataFrame()
    temp_daily = pd.DataFrame()
    needed_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n', 'nPopulation', 'prevalence_2to10', 'prev',
                       'index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup', 'age_upper', 'EIR_gamb',
                       'n_infectious_mos', 'n_total_mos_pop']
    for i in range(1, exp.nexps + 1):
        i_df = pd.read_csv(os.path.join(job_directory, f'malsim_jobs/daily_{i}.csv'))
        i_df = i_df.filter(items=needed_channels)
        temp_daily = pd.concat([temp_daily, i_df], axis=0)
        if i % num_seeds == 0:
            daily = pd.concat([daily, temp_daily], axis=0)
            temp_daily = pd.DataFrame()
    daily.to_csv((os.path.join(job_directory, 'malsim_jobs', 'daily.csv')), index=False)


def InputEIRAnalyzer(jdir, wdir, daily=False):
    """
    Run the InputEIRAnalyzer for Malariasimulation experiments.
    If daily is True, generate the EIR_daily.csv ONLY.
    """
    print("Running InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1)  ## EMOD specific, entomology_mode  not applicable

    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'nPopulation', 'EIR_gamb', 'n_infectious_mos',
                        'n_total_mos_pop']
    # df = load_combined_daily_output(jdir, channels_to_keep + ['ageGroup'])
    df = pd.read_csv(os.path.join(jdir, 'malsim_jobs', 'daily.csv'))
    df = df[channels_to_keep + ['ageGroup']]
    df = df[df['ageGroup'] == '0-0']

    df = df[channels_to_keep]
    df['EIR_gamb'] = df['EIR_gamb'] / df['nPopulation']
    if daily:
        df_daily = df.merge(scen_df, on='index', how='inner')
        columns_to_keep = ['index', 'seed', 'timestep', 'month', 'year', 'nPopulation', 'EIR_gamb',
                           'cm_clinical', 'seasonality', 'scen_id', 'num_seeds', 'cm_start', 'cm_severe',
                           'eir_malsim', 'eir_scalar_timestep_daily', 'eir_scalar_malsim', 'n_infectious_mos',
                           'n_total_mos_pop']

        columns_to_keep = [col for col in columns_to_keep if col in df_daily.columns]
        df_daily = df_daily[columns_to_keep]
        df_daily = df_daily.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)

        if 'eir_malsim' in df_daily:  # if the user sets different values between Malsim and EMOD, this should catch if the
            df_daily['inputEIR'] = df_daily['eir_malsim']
            df_daily = df_daily.rename(
                {'eir_scalar_timestep_daily': 'eir_scalar_timestep', 'eir_scalar_malsim': 'eir_scalar'}, axis=1)

        print(f'Saving EIR_daily.csv to {wdir}')
        df_daily.to_csv((os.path.join(wdir, 'EIR_daily.csv')), index=False)
    else:
        # Monthly aggregation - keep months and years
        mean_channels = ['n_infectious_mos', 'n_total_mos_pop']
        df_mth = df.groupby(['index', 'month', 'year'], as_index=False)['EIR_gamb'].sum()
        vdf_mth = df.groupby(['index', 'month', 'year'], as_index=False)[mean_channels].mean()
        df_mth = df_mth.merge(vdf_mth, on=['index', 'month', 'year'], how='inner')
        df_mth = df_mth.merge(scen_df, on='index', how='inner')
        df_mth = df_mth.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)
        df_mth['inputEIR'] = df_mth['eir']  # if inputEIR not available from simulations, use 'eir'
        print(f'Saving EIR_mth.csv to {wdir}')
        df_mth.to_csv((os.path.join(wdir, 'EIR_mth.csv')), index=False)

        # Yearly aggregation - keep years
        df_yr = df.groupby(['index', 'year'], as_index=False)['EIR_gamb'].sum()
        vdf_yr = df.groupby(['index', 'year'], as_index=False)[mean_channels].mean()
        df_yr = df_yr.merge(vdf_yr, on=['index', 'year'], how='inner')
        df_yr = df_yr.merge(scen_df, on='index', how='inner')
        df_yr = df_yr.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)
        df_yr['inputEIR'] = df_yr['eir']  # if inputEIR not available from simulations, use 'eir'
        print(f'Saving EIR_yr.csv to {wdir}')
        df_yr.to_csv((os.path.join(wdir, 'EIR_yr.csv')), index=False)

        # Mean over monitoring period
        nyears = len(df['year'].unique())
        df_yr = df.groupby(['index'], as_index=False)['EIR_gamb'].sum()
        vdf_yr = df.groupby(['index'], as_index=False)[mean_channels].mean()
        df_yr = df_yr.merge(vdf_yr, on=['index'], how='inner')
        df_yr['EIR_gamb'] = df_yr['EIR_gamb'] / nyears
        df_yr['n_infectious_mos'] = df_yr['n_infectious_mos'] / nyears
        df_yr['n_total_mos_pop'] = df_yr['n_total_mos_pop'] / nyears
        df_yr = df_yr.merge(scen_df, on='index', how='inner')
        df_yr = df_yr.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)
        df_yr['inputEIR'] = df_yr['eir']  # if inputEIR not available from simulations, use 'eir'
        print(f'Saving EIR.csv to {wdir}')
        df_yr.to_csv((os.path.join(wdir, 'EIR.csv')), index=False)


def SurveyAllAgeAnalyzer(jdir, wdir, sweep_variables):
    """
    Run the SurveyAllAgeAnalyzer for malariasimulation experiments.
    """
    print("Running SurveyAllAgeAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1)  ## EMOD specific, entomology_mode  not applicable

    # Read experiment data daily
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    # df = load_combined_daily_output(jdir, channels_to_keep)
    df = pd.read_csv(os.path.join(jdir, 'malsim_jobs', 'daily.csv'))
    df = df[channels_to_keep]

    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['day'] = df['timestep'] % 365
    df['date'] = df.apply(lambda x: datetime.date(int(x['year']), 1, 1) + datetime.timedelta(int(x['day']) - 1), axis=1)

    # Sum the values of the age groups
    # Aggregate data per date and sweep_variables using sum and mean specific to outcome channel

    sdf = df.groupby(['date'] + sweep_variables)[sum_channels].agg(np.sum).reset_index()
    mdf = df.groupby(['date'] + sweep_variables)[mean_channels].agg(np.mean).reset_index()
    adf = pd.merge(left=sdf, right=mdf, on=(sweep_variables + ['date']))

    # Merge with the scenario data
    adf = adf.merge(scen_df, on='index', how='inner')

    # Save the processed DataFrame to a CSV file named 'All_Age_Outputs.csv'
    print(f'Saving All_Age_Outputs.csv to {wdir}')
    adf.to_csv((os.path.join(wdir, 'All_Age_Outputs.csv')), index=False)


def BenchmarkAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None):
    """
    Run the BenchmarkAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups aggregated over the monitoring period.

    Args:
        jdir (str): Path to the directory containing simulation job data.
        wdir (str): Path to the working directory.
        sweep_variables (list): List of sweep variables.
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.

    Saves:
        Benchmark.csv

    Returns:
        None
    """
    print("Running BenchmarkAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    # df = load_combined_daily_output(jdir, channels_to_keep)
    df = pd.read_csv(os.path.join(jdir, 'malsim_jobs', 'daily.csv'))
    df = df[channels_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n']

    df_pfpr2to10 = df.groupby(sweep_variables)[['prevalence_2to10']].agg(np.mean).reset_index()

    ## Aggregate years
    n_surveys = round(len(df['timestep'].unique()), 0)
    n_years = round(n_surveys / 365, 0)
    df = df.groupby(sweep_variables + ['agebin', 'year'])[
        ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()
    df['n'] = df['n'] / n_surveys
    df['n_prev'] = df['n_prev'] / n_surveys

    cdf = pd.DataFrame()

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_aggregates)):
        ages = age_groups_aggregates[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin >= ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            adf = adf.groupby(sweep_variables)[['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(
                np.sum).reset_index()
            adf['prevalence'] = adf['n_prev'] / (adf['n'])

            # (events per person per annum)
            # adf['incidence'] = adf['n_inc'] / ( (adf['n'] * n_years))
            adf['clinical_incidence'] = adf['n_inc_clinical'] / ((adf['n'] * n_years))
            adf['severe_incidence'] = adf['n_inc_severe'] / ((adf['n'] * n_years))
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables)
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1)  ## EMOD specific, entomology_mode  not applicable
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on='index', how='inner')

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    cdf = cdf.rename({'n': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])

    print(f'\nSaving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir, 'Benchmark.csv')), index=False)


def MonthlyAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None):
    """
    Run the MonthlyAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups over time (month and years).

    Args:
        jdir (str): Path to the directory containing simulation job data.
        wdir (str): Path to the working directory.
        sweep_variables (list): List of sweep variables.
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.

    Saves:
        PfPR_ClinicalIncidence_mth.csv

    Returns:
        None
    """
    print("Running MonthlyAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_mth.csv'))
    eir_df = eir_df.groupby(sweep_variables + ['month', 'year'])[['simulatedEIR', 'inputEIR']].agg(
        np.mean).reset_index()  # mean across runs per month and year
    eir_df = eir_df[['index', 'month', 'year', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup', 'age_upper',
                        'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n', 'nPopulation', 'prevalence_2to10', 'prev']

    # df = load_combined_daily_output(jdir, channels_to_keep)
    df = pd.read_csv(os.path.join(jdir, 'malsim_jobs', 'daily.csv'))
    df = df[channels_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n']

    df_pfpr2to10 = df.groupby(sweep_variables + ['month', 'year'])[['prevalence_2to10']].agg(np.mean).reset_index()

    ## Aggregate days to month and years
    n_surveys_per_year = int(round(len(df['timestep'].unique()) / len(df['year'].unique()), 0))

    df = df.groupby(sweep_variables + ['agebin', 'month', 'year'])[
        ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()

    df['n'] = df['n'] /(365/12)
    df['n_prev'] = df['n_prev'] /(365/12)

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
            adf = adf.groupby(sweep_variables + ['month', 'year'])[
                ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()

            adf['prevalence'] = adf['n_prev'] / (adf['n'])
            # events per person per annum (annualized)
            # adf['incidence'] = (adf['n_inc'] / adf['n']/ 12)
            adf['clinical_incidence'] = (adf['n_inc_clinical'] / (adf['n']/ 12))
            adf['severe_incidence'] = (adf['n_inc_severe'] / (adf['n'] / 12))
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + [ 'month', 'year'])
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1)  ## EMOD specific, entomology_mode  not applicable
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on=['index', 'month', 'year'], how='inner')

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    cdf = cdf.rename({'n': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])
    cdf['date'] = cdf.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)
    
    print(f'\nSaving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir, 'PfPR_ClinicalIncidence_mth.csv')), index=False)


def AnnualAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None):
    """
    Run the AnnualAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups over time (years).

    Args:
        jdir (str): Path to the directory containing simulation job data.
        wdir (str): Path to the working directory.
        sweep_variables (list): List of sweep variables.
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.

    Saves:
        PfPR_ClinicalIncidence_yr.csv

    Returns:
        None
    """
    print("Run AnnualAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_yr.csv'))
    eir_df = eir_df[['index', 'year', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper', 'prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n', 'nPopulation',
                        'prevalence_2to10']
    # df = load_combined_daily_output(jdir, channels_to_keep)
    df = pd.read_csv(os.path.join(jdir, 'malsim_jobs', 'daily.csv'))
    df = df[channels_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n']

    df_pfpr2to10 = df.groupby(sweep_variables + ['year'])[['prevalence_2to10']].agg(np.mean).reset_index()

    ## Aggregate to years
    n_surveys_per_year = int(round(len(df['timestep'].unique()) / len(df['year'].unique()), 0))
    df = df.groupby(sweep_variables + ['agebin', 'year'])[
        ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()
    df['n'] = df['n'] / n_surveys_per_year
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
            adf = adf.groupby(sweep_variables + ['year'])[
                ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()

            adf['prevalence'] = adf['n_prev'] / (adf['n'])
            # (events per person per annum)
            # adf['incidence'] = adf['n_inc'] / (adf['n'])
            adf['clinical_incidence'] = adf['n_inc_clinical'] / (adf['n'])
            adf['severe_incidence'] = adf['n_inc_severe'] / (adf['n'])
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['year'])
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1)  ## EMOD specific, entomology_mode  not applicable
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on=['index', 'year'], how='inner')

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    cdf = cdf.rename({'n': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])

    print(f'\nSaving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir, 'PfPR_ClinicalIncidence_yr.csv')), index=False)


def CCStepAnalyzer(jdir, wdir, sweep_variables):
    """
    Run the CCStepAnalyzer equivalent for malariasimulation experiments.
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
    print("Running CCStepAnalyzer...", flush=True)

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev', 'n_infectious_mos', 'n_total_mos_pop']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    # df = load_combined_daily_output(jdir, channels_to_keep)
    df = pd.read_csv(os.path.join(jdir, 'malsim_jobs', 'daily.csv'))
    df = df[channels_to_keep]
    df['n_prev'] = df['prev'] * df['n']
    df['incidence'] = (df['n_inc'] / df['n'])
    df['clinical_incidence'] = (df['n_inc_clinical'] / df['n'])
    df['severe_incidence'] = (df['n_inc_severe'] / df['n'])
    age_grps = list(df['ageGroup'].unique())
    df['ageGroup'] = df['ageGroup'].astype('category')
    df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)
    df['ageGroup'] = df['ageGroup'].replace('0-0', '0-0.5')
    df['ageGroup'] = df['ageGroup'].replace('0-1', '0.5-1')

    # Align to common output terminology used
    df = df.rename({'n': 'nHost', 'n_inc': 'nInfect', 'n_inc_clinical': 'nUncomp', 'n_inc_severe': 'nSevere',
                    'prev': 'prevalence'}, axis=1)

    df[['agebin_low', 'agebin']] = df['ageGroup'].str.split('-', expand=True)

    ## Add scenarios variables
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1)  ## EMOD specific, entomology_mode  not applicable
    df = df.merge(scen_df, on=sweep_variables, how='inner')
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_daily.csv'))
    eir_df = eir_df[['index', 'timestep', 'month', 'year', 'simulatedEIR', 'inputEIR']]
    df = df.merge(eir_df, on=['index', 'timestep', 'month', 'year'], how='inner')

    # Let's limit the output of daily, so its a little more reasonable for us to process.
    columns_to_keep = ['index', 'seed', 'ageGroup', 'timestep', 'eir_malsim', 'simulatedEIR', 'n_infectious_mos',
                       'n_total_mos_pop', 'clinical_incidence', 'severe_incidence', 'prevalence', 'prevalence_2to10',
                       'carrying_capacity_step', 'eir_scalar_timestep_daily', 'eir_scalar_malsim']

    # Iterate over columns to drop and check if they exist
    columns_to_keep = [col for col in columns_to_keep if col in df.columns]
    df = df[columns_to_keep]

    if 'eir_malsim' in df:
        df = df.rename({'eir_malsim': 'eir', 'eir_scalar_timestep_daily': 'eir_scalar_timestep',
                        'eir_scalar_malsim': 'eir_scalar'})
      
    # Save the processed DataFrame to a CSV file
    print(f'Saving CCstep_daily.csv to {wdir}')
    df.to_csv((os.path.join(wdir, 'CCstep_daily.csv')), index=False)


if __name__ == "__main__":
    args = parse_args()
    jdir = args.job_dir

    # Load experiment object 
    file = open(os.path.join(jdir, "exp.obj"), "rb")
    exp = pickle.load(file)

    wdir = os.path.join(exp.sim_out_dir, 'MalSim')
    sweep_variables = ['index']
    all_age_sp = False  # False
    seeds = exp.num_seeds
    age_groups_aggregates = exp.age_groups_aggregates

    daily_path = os.path.join(jdir, 'malsim_jobs/daily.csv')

    if not os.path.isfile(daily_path):
        load_combined_daily_output(jdir, seeds)

    # Run analyzers
    InputEIRAnalyzer(jdir, wdir)

    ## all age by reporting steps
    if 'all_age' in exp.analyzer_list:
        SurveyAllAgeAnalyzer(jdir, wdir, sweep_variables)

    ## Monthly timeseries per age groups
    if 'monthly' in exp.analyzer_list:
        MonthlyAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates)

    ## Annual timeseries per age groups
    if 'annual' in exp.analyzer_list:
        AnnualAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates)

    ## Aggregated timeseries per age groups
    if 'benchmark' in exp.analyzer_list:
        BenchmarkAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates)

    ## Custom analyzers
    if 'cc_step' in exp.analyzer_list:
        InputEIRAnalyzer(jdir, wdir, daily=True)
        CCStepAnalyzer(jdir, wdir, sweep_variables)
