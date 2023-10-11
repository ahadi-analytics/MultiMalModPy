import os
import argparse
import pickle
import datetime
import time
import pandas as pd
import numpy as np
import sys

sys.path.append('../')
import manifest
from benchmark_plots import *
from MalSim.sample_plots import *


# TODO ADD FUNCTIONS THAT WILL CONVERT MALSIM VALUES TO APPROPRIATE VALUES
# TO COMPARE TO EMOD AND OPENMALARIA
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
        "--output_dir",
        type=str,
        required=True,
        help="Output Directory of exp.obj")
    return parser.parse_args()


def get_age_group_labels(age_bins):
    age_group_labels = [str(age_bins[i - 1]) + "-" + str(age_bins[i]) for i in range(1, len(age_bins))]
    age_group_labels = [str(0) + "-" + str(age_bins[0])] + age_group_labels
    return age_group_labels


def BenchmarkAnalyzer(wdir, sweep_variables):
    """
    Run the BenchmarkAnalyzer equivalent of EMOD for OpenMalaria experiments.
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup and grp_channels
           all surveys aggregated
    """
    print(f"Running BenchmarkAnalyzer...", flush=True)

    # Read the EIR data from the CSV file
    # eir_df = pd.read_csv(os.path.join(wdir, 'EIR.csv'))
    # eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    df = pd.read_csv(os.path.join(wdir, f'MalSim/daily.csv'))
    df['agebin'] = round(df['age_upper'] / 365, 1)

    df_pfpr2to10 = df.groupby(sweep_variables + ['agebin'])[['prevalence_2to10']].agg(np.mean).reset_index()
    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / 1))
    num_years = np.floor(len(df['timestep'].unique()) / n_surveys_per_year)

    ## Aggregate years
    df = df.groupby(sweep_variables + ['agebin'])[
        ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(
        np.mean).reset_index()
    df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
    df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
    df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

    cdf = pd.DataFrame()
    # Define standard age groups used in benchmarking default for plotting
    age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_on_plot)):
        ages = age_groups_on_plot[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin >= ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            adf = adf.groupby(sweep_variables)[['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                np.sum).reset_index()
            adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
            adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per annum)
            adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'])  # (events per person per annum)
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables)
    scen_df = pd.read_csv(os.path.join(wdir, 'scenarios_wseeds.csv'))
    cdf = cdf.merge(scen_df, on='index', how='inner')
    cdf['simulatedEIR'] = cdf['eir']  ## FIXME, add actual simulatedEIR
    cdf['inputEIR'] = cdf['eir']

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    print(f'\nSaving outputs to: {os.path.join(wdir)}/MalSim')

    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir, 'MalSim', f'Benchmark.csv')), index=False)


def MonthlyBenchmarkAnalyzer(wdir, sweep_variables):
    """
    Run the BenchmarkAnalyzer equivalent of EMOD for OpenMalaria experiments.
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup and grp_channels
           all surveys aggregated
    """
    print(f"Running BenchmarkAnalyzer...", flush=True)

    # Read the EIR data from the CSV file
    # eir_df = pd.read_csv(os.path.join(wdir, 'EIR.csv'))
    # eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    df = pd.read_csv(os.path.join(wdir, f'MalSim/daily.csv'))
    df['agebin'] = round(df['age_upper'] / 365, 1)

    df_pfpr2to10 = df.groupby(sweep_variables + ['agebin', 'month'])[['prevalence_2to10']].agg(np.mean).reset_index()
    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / 1))
    num_years = np.floor(len(df['timestep'].unique()) / n_surveys_per_year)

    ## Aggregate years
    df = df.groupby(sweep_variables + ['agebin', 'month'])[
        ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(
        np.mean).reset_index()
    df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
    df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
    df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

    cdf = pd.DataFrame()
    # Define standard age groups used in benchmarking default for plotting
    age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_on_plot)):
        ages = age_groups_on_plot[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin >= ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            adf = adf.groupby(sweep_variables + ['month'])[['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                np.sum).reset_index()
            adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
            adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per annum)
            adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'])  # (events per person per annum)
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['month'])
    scen_df = pd.read_csv(os.path.join(wdir, 'scenarios_wseeds.csv'))
    cdf = cdf.merge(scen_df, on='index', how='inner')
    cdf['simulatedEIR'] = cdf['eir']  ## FIXME, add actual simulatedEIR
    cdf['inputEIR'] = cdf['eir']

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    print(f'\nSaving outputs to: {os.path.join(wdir)}/MalSim')

    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir, 'MalSim', f'Benchmark_mth.csv')), index=False)


def AnnualBenchmarkAnalyzer(wdir, sweep_variables):
    """
    Run the BenchmarkAnalyzer equivalent of EMOD for OpenMalaria experiments.
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup and grp_channels
           all surveys aggregated
    """
    print(f"Running BenchmarkAnalyzer...", flush=True)

    # Read the EIR data from the CSV file
    # eir_df = pd.read_csv(os.path.join(wdir, 'EIR.csv'))
    # eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    df = pd.read_csv(os.path.join(wdir, f'MalSim/daily.csv'))
    df['agebin'] = round(df['age_upper'] / 365, 1)

    df_pfpr2to10 = df.groupby(sweep_variables + ['agebin', 'year'])[['prevalence_2to10']].agg(np.mean).reset_index()
    # get number of years aggregated
    n_surveys_per_year = np.floor((365 / 1))
    num_years = np.floor(len(df['timestep'].unique()) / n_surveys_per_year)

    ## Aggregate years
    df = df.groupby(sweep_variables + ['agebin', 'year'])[
        ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(
        np.mean).reset_index()
    df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
    df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
    df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

    cdf = pd.DataFrame()
    # Define standard age groups used in benchmarking default for plotting
    age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]

    # Loop over age groups to aggregate results data
    for i in range(0, len(age_groups_on_plot)):
        ages = age_groups_on_plot[i]
        ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
        adf = df[(df.agebin >= ages[0]) & (df.agebin <= ages[1])]
        if adf.empty:
            pass
        else:
            adf = adf.groupby(sweep_variables + ['year'])[['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                np.sum).reset_index()
            adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
            adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per annum)
            adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'])  # (events per person per annum)
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['year'])
    scen_df = pd.read_csv(os.path.join(wdir, 'scenarios_wseeds.csv'))
    cdf = cdf.merge(scen_df, on='index', how='inner')
    cdf['simulatedEIR'] = cdf['eir']  ## FIXME, add actual simulatedEIR
    cdf['inputEIR'] = cdf['eir']

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    print(f'\nSaving outputs to: {os.path.join(wdir)}/MalSim')

    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir, 'MalSim', f'Benchmark_yr.csv')), index=False)


def MonthlyAgebinAnalyzer(wdir, sweep_variables):
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

    # Convert the experiment data to a DataFrame and format it
    df = pd.read_csv(os.path.join(wdir, f'MalSim/daily.csv'))
    age_grps = list(df['ageGroup'].unique())
    df['ageGroup'] = df['ageGroup'].astype('category')
    df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)
    df['day'] = 1
    df['year'] = df['year'] + 1999
    df['ageGroup'] = df['ageGroup'].replace('0-0', '0-0.5')
    df['ageGroup'] = df['ageGroup'].replace('0-1', '0.5-1')

    # Create PfPR Monthly df, calculate Columns necessary, save to csv
    df_mth = df.groupby(sweep_variables +['year', 'month', 'ageGroup'])[
        ['nHost', 'prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'day']].agg(
        np.mean).reset_index()
    df_mth['nPatent'] = df_mth['prevalence'] * df_mth['nHost']
    df_mth['nUncomp'] = df_mth['clinical_incidence'] * df_mth['nHost']
    df_mth['nSevere'] = df_mth['severe_incidence'] * df_mth['nHost']
    df_mth['date'] = pd.to_datetime(dict(year=df_mth.year, month=df_mth.month, day=df_mth.day))
    df_mth[['agebin_low', 'agebin']] = df_mth['ageGroup'].str.split('-', expand=True)

    # Reorder outcome columns
    first_columns = sweep_variables + [ 'date', 'year', 'month', 'agebin', 'ageGroup', 'nHost', 'prevalence',
                     'clinical_incidence', 'severe_incidence']
    df_mth = df_mth[first_columns + df_mth.drop(columns=first_columns).columns.tolist()]

    ## Add scenarios variables
    scen_df = pd.read_csv(os.path.join(wdir, 'scenarios_wseeds.csv'))
    df_mth = df_mth.merge(scen_df, on='index', how='inner')

    # Save the processed DataFrame to a CSV file
    print(f'Saving PfPR_ClinicalIncidence_mth.csv to {wdir}')
    df_mth.to_csv((os.path.join(wdir, f'PfPR_ClinicalIncidence_mth.csv')), index=False)


def AnnualAgebinAnalyzer(wdir, sweep_variables):
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

    # Convert the experiment data to a DataFrame and format it
    df = pd.read_csv(os.path.join(wdir, f'MalSim/daily.csv'))
    age_grps = list(df['ageGroup'].unique())
    df['ageGroup'] = df['ageGroup'].astype('category')
    df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)
    df['day'] = 1
    df['year'] = df['year'] + 1999
    df['ageGroup'] = df['ageGroup'].replace('0-0', '0-0.5')
    df['ageGroup'] = df['ageGroup'].replace('0-1', '0.5-1')

    # Create PfPR Monthly df, calculate Columns necessary, save to csv
    df_yr = df.groupby(sweep_variables + ['year', 'ageGroup'])[
        ['nHost', 'prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'day']].agg(
        np.mean).reset_index()
    df_yr['nPatent'] = df_yr['prevalence'] * df_yr['nHost']
    df_yr['nUncomp'] = df_yr['clinical_incidence'] * df_yr['nHost']
    df_yr['nSevere'] = df_yr['severe_incidence'] * df_yr['nHost']
    df_yr['date'] = pd.to_datetime(dict(year=df_yr.year, month=1, day=1))
    df_yr[['agebin_low', 'agebin']] = df_yr['ageGroup'].str.split('-', expand=True)

    # Reorder outcome columns
    first_columns = sweep_variables + ['date', 'year', 'agebin', 'ageGroup', 'nHost', 'prevalence',
                                       'clinical_incidence', 'severe_incidence']
    df_yr = df_yr[first_columns + df_yr.drop(columns=first_columns).columns.tolist()]

    scen_df = pd.read_csv(os.path.join(wdir, 'scenarios_wseeds.csv'))
    df_yr = df_yr.merge(scen_df, on='index', how='inner')

    # Save the processed DataFrame to a CSV file
    print(f'Saving PfPR_ClinicalIncidence_yr.csv to {wdir}')
    df_yr.to_csv((os.path.join(wdir, f'PfPR_ClinicalIncidence_yr.csv')), index=False)


if __name__ == "__main__":
    args = parse_args()
    wdir = args.output_dir

    # Load experiment object
    file = open(os.path.join(wdir, "exp.obj"), "rb")
    exp = pickle.load(file)
    sweep_variables = ['index']
    create_sampleplots = True #False

    BenchmarkAnalyzer(wdir, sweep_variables)
    MonthlyBenchmarkAnalyzer(wdir, sweep_variables)
    AnnualBenchmarkAnalyzer(wdir, sweep_variables)
    MonthlyAgebinAnalyzer(wdir, sweep_variables)
    AnnualAgebinAnalyzer(wdir, sweep_variables)

    # Create sample plots if specified
    if create_sampleplots:
        file = open(os.path.join(wdir, "exp.obj"), "rb")
        exp = pickle.load(file)
        exp_tags = [x for x in exp.sweep_list if x != 'seed']  # + ['seed']
        #exp_tags = ['eir', 'cm_clinical', 'seasonality']

        channels_inset_chart = ['nPopulation', 'nHost', 'prevalence',
                                'incidence', 'clinical_incidence',
                                'severe_incidence', 'prevalence_2to10']
        all_age_sample_plot(wdir=os.path.join(wdir, 'MalSim'), sweep_variables=exp_tags,
                            inset_channels=channels_inset_chart)
        sample_plot_yr(wdir=os.path.join(wdir, 'MalSim'), sweep_variables=exp_tags)
        sample_plot_mth(wdir=os.path.join(wdir, 'MalSim'), sweep_variables=exp_tags)

        emodom = ['MalSim']
        sweepvar = 'eir'
        monthly_trends(wdir, emodom, channel='clinical_incidence', sweepvar=sweepvar)
        monthly_trends(wdir, emodom, channel='severe_incidence', sweepvar=sweepvar)
        monthly_trends(wdir, emodom, channel='prevalence', sweepvar=sweepvar)
        monthly_trends(wdir, emodom, channel='prevalence_2to10', sweepvar=sweepvar)
        #monthly_trends(wdir, emodom=emodom, channel='eir', sweepvar=sweepvar)

        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence']
        for channel in channel_list:
            monthly_timeseries(wdir, emodom, channel, sweepvar='emodom', facet_var='eir', agegrp='5-10')

        sweepvar = 'cm_clinical'
        prevalence2to10_to_incidence(wdir, emodom, channel='prevalence', y_lim=1)
        prevalence2to10_to_incidence(wdir, emodom, channel='clinical_incidence', y_lim=25)
        prevalence2to10_to_incidence(wdir, emodom, channel='severe_incidence', y_lim=1)
        eir_to_prevalence2to10(wdir, emodom, sweepvar=sweepvar, eir_val='eir')
        eir_to_prevalence2to10(wdir, emodom, sweepvar=sweepvar, eir_val='eir')
        input_to_simulated_eir(wdir, emodom, sweepvar=sweepvar)
