import os
import argparse
import pickle
import datetime
import pandas as pd
import numpy as np
from sample_plots import *
import sys
sys.path.append('../')
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
        "-o",
        "--job_dir",
        type=str,
        required=True,
        help="Job Directory of exp.obj")
    return parser.parse_args()


def load_combined_daily_output(job_directory, channels=None, save_daily=False):
    daily = pd.DataFrame()
    if exp.emod_step is None: 
        nSims = exp.nexps
    else:
        nSims = int(exp.nexps/exp.num_seeds)
    for i in range(1, nSims + 1):
        i_df = pd.read_csv(os.path.join(job_directory, f'malsim_jobs/daily_{i}.csv'))
        if channels is not None:
            i_df = i_df[channels]
        daily = pd.concat([daily, i_df], axis=0)
    if save_daily:
        daily.to_csv((os.path.join(job_directory, 'malsim_jobs', 'daily.csv')), index=False)
    else:
        return daily


def InputEIRAnalyzer(jdir, wdir):
    """
    Run the InputEIRAnalyzer for Malariasimulation experiments.
    """
    print("Running InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop('x_Temporary_Larval_Habitat', axis=1)

    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'nPopulation', 'EIR_gamb']
    df = load_combined_daily_output(jdir, channels_to_keep + ['ageGroup'])

    df = df[channels_to_keep]
    df['EIR_gamb'] = df['EIR_gamb'] / df['nPopulation']

    # Yearly aggregation - keep years
    df_yr = df.groupby(['index', 'year'], as_index=False)['EIR_gamb'].sum()
    df_yr = df_yr.merge(scen_df, on='index', how='inner')
    df_yr = df_yr.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)
    df_yr['inputEIR'] = df_yr['eir']  # if inputEIR not available from simulations, use 'eir'
    print(f'Saving EIR_yr.csv to {wdir}')
    df_yr.to_csv((os.path.join(wdir, 'EIR_yr.csv')), index=False)

    # Monthly aggregation - keep months
    df_mth = df.groupby(['index', 'month'], as_index=False)['EIR_gamb'].sum()
    df_mth = df_mth.merge(scen_df, on='index', how='inner')
    df_mth = df_mth.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)
    df_mth['inputEIR'] = df_mth['eir']  # if inputEIR not available from simulations, use 'eir'
    print(f'Saving EIR_mth.csv to {wdir}')
    df_mth.to_csv((os.path.join(wdir, 'EIR_mth.csv')), index=False)

    #Yearly and Monthly aggregation - keep years and months
    df_mthyr = df.groupby(['index', 'month', 'year'], as_index = False)['EIR_gamb'].sum()
    df_mthyr = df_mthyr.merge(scen_df, on = 'index', how='inner')
    df_mthyr = df_mthyr.rename({'EIR_gamb': 'simulatedEIR'}, axis = 1)
    df_mthyr['inputEIR'] = df_mthyr['eir']  # if inputEIR not available from simulations, use 'eir'
    print(f'Saving EIR_mthyr.csv to {wdir}')
    df_mthyr.to_csv((os.path.join(wdir, 'EIR_mthyr.csv')), index=False)
    
    # Yearly aggregation - mean
    nyears = len(df['year'].unique())
    df_yr = df.groupby(['index'], as_index=False)['EIR_gamb'].sum()
    df_yr['EIR_gamb'] = df_yr['EIR_gamb'] / nyears
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

    # Read experiment data daily
    sum_channels = ['clinical_incidence', 'incidence', 'severe_incidence', 'nHost']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prevalence']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    df = load_combined_daily_output(jdir, channels_to_keep)

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
    adf.to_csv((os.path.join(wdir,'All_Age_Outputs.csv')), index=False)


def BenchmarkAnalyzer(jdir, wdir, sweep_variables):
    """
    Run the BenchmarkAnalyzer equivalent of EMOD for malariasimulation experiments.
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup and grp_channels
           all surveys aggregated
    """
    print("Running BenchmarkAnalyzer...", flush=True)

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['clinical_incidence', 'incidence', 'severe_incidence', 'nHost']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prevalence']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    df = load_combined_daily_output(jdir, channels_to_keep)
    df['agebin'] = round(df['age_upper'] / 365, 1)

    df_pfpr2to10 = df.groupby(sweep_variables + ['agebin'])[['prevalence_2to10']].agg(np.mean).reset_index()

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
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    cdf = cdf.merge(scen_df, on='index', how='inner')
    cdf = cdf.merge(eir_df, on='index', how='inner')

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    print(f'\nSaving outputs to: {wdir}')

    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir,'Benchmark.csv')), index=False)

def MonthlyBenchmarkAnalyzer(jdir, wdir, sweep_variables):
    """
    Run the BenchmarkAnalyzer equivalent of EMOD for malariasimulation experiments.
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup and grp_channels
           all surveys aggregated
    """
    print("Running BenchmarkAnalyzer...", flush=True)

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_mth.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper','clinical_incidence', 'incidence', 'severe_incidence', 
                        'nHost','nPopulation', 'prevalence_2to10', 'prevalence']
    df = load_combined_daily_output(jdir, channels_to_keep)
    df['agebin'] = round(df['age_upper'] / 365, 1)

    df_pfpr2to10 = df.groupby(sweep_variables + ['agebin', 'month'])[['prevalence_2to10']].agg(np.mean).reset_index()

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
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    cdf = cdf.merge(scen_df, on='index', how='inner')
    cdf = cdf.merge(eir_df, on='index', how='inner')

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    print(f'\nSaving outputs to: {wdir}')

    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir,'Benchmark_mth.csv')), index=False)


def AnnualBenchmarkAnalyzer(jdir, wdir, sweep_variables):
    """
    Run the BenchmarkAnalyzer equivalent of EMOD for OpenMalaria experiments.
    Saves: CSV dataframe in 'benchmark' format of selected simulation outcome metrics per fixed agegroup and grp_channels
           all surveys aggregated
    """
    print("Running BenchmarkAnalyzer...", flush=True)

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_yr.csv'))
    eir_df = eir_df[['index', 'inputEIR', 'simulatedEIR']]

    # Convert the experiment data to a DataFrame and format it
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper','clinical_incidence', 'incidence', 'severe_incidence', 'nHost', 'nPopulation', 'prevalence_2to10', 'prevalence']
    df = load_combined_daily_output(jdir, channels_to_keep)
    df['agebin'] = round(df['age_upper'] / 365, 1)

    df_pfpr2to10 = df.groupby(sweep_variables + ['agebin', 'year'])[['prevalence_2to10']].agg(np.mean).reset_index()

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
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    cdf = cdf.merge(scen_df, on='index', how='inner')
    cdf = cdf.merge(eir_df, on='index', how='inner')

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    print(f'\nSaving outputs to: {wdir}')

    # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
    cdf.to_csv((os.path.join(wdir,'Benchmark_yr.csv')), index=False)


def MonthlyAgebinAnalyzer(jdir, wdir, sweep_variables, sim_start):
    """
    Run the MonthlyAgebinAnalyzer equivalent for malariasimulation experiments.
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
    print("Running MonthlyAgebinAnalyzer...", flush=True)

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['clinical_incidence', 'incidence', 'severe_incidence', 'nHost']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prevalence']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    df = load_combined_daily_output(jdir, channels_to_keep)

    age_grps = list(df['ageGroup'].unique())
    df['ageGroup'] = df['ageGroup'].astype('category')
    df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)
    df['day'] = 1
    df['ageGroup'] = df['ageGroup'].replace('0-0', '0-0.5')
    df['ageGroup'] = df['ageGroup'].replace('0-1', '0.5-1')

    # Create PfPR Monthly df, calculate Columns necessary, save to csv
    df_mth = df.groupby(sweep_variables + ['year', 'month', 'ageGroup'])[
        ['nHost', 'prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence', 'day']].agg(
        np.mean).reset_index()
    df_mth['nPatent'] = df_mth['prevalence'] * df_mth['nHost']
    df_mth['nUncomp'] = df_mth['clinical_incidence'] * df_mth['nHost']
    df_mth['nSevere'] = df_mth['severe_incidence'] * df_mth['nHost']
    df_mth['date'] = pd.to_datetime(dict(year=df_mth.year, month=df_mth.month, day=df_mth.day))
    df_mth[['agebin_low', 'agebin']] = df_mth['ageGroup'].str.split('-', expand=True)

    # Reorder outcome columns
    first_columns = sweep_variables + ['date', 'year', 'month', 'agebin', 'ageGroup', 'nHost', 'prevalence',
                                       'clinical_incidence', 'severe_incidence']
    df_mth = df_mth[first_columns + df_mth.drop(columns=first_columns).columns.tolist()]

    ## Add scenarios variables
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    df_mth = df_mth.merge(scen_df, on='index', how='inner')
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_mthyr.csv'))
    eir_df = eir_df[['index','month','year', 'simulatedEIR', 'inputEIR']]
    df_mth = df_mth.merge(eir_df, on = ['index', 'month', 'year'], how='inner')
    # Save the processed DataFrame to a CSV file
    print(f'Saving PfPR_ClinicalIncidence_mth.csv to {wdir}')
    df_mth.to_csv((os.path.join(wdir, 'PfPR_ClinicalIncidence_mth.csv')), index=False)


def AnnualAgebinAnalyzer(jdir, wdir, sweep_variables, sim_start):
    """
    Run the MonthlyAgebinAnalyzer equivalent for malariasimulation experiments.
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
    print("Running AnnualAgebinAnalyzer...", flush=True)

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['clinical_incidence', 'incidence', 'severe_incidence', 'nHost']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prevalence']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'sim_year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    df = load_combined_daily_output(jdir, channels_to_keep)

    age_grps = list(df['ageGroup'].unique())
    df['ageGroup'] = df['ageGroup'].astype('category')
    df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)
    df['day'] = 1
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

    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    df_yr = df_yr.merge(scen_df, on='index', how='inner')
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_yr.csv'))
    eir_df = eir_df[['index','year', 'simulatedEIR', 'inputEIR']]
    df_yr = df_yr.merge(eir_df, on = ['index', 'year'], how='inner')
    # Save the processed DataFrame to a CSV file
    print(f'Saving PfPR_ClinicalIncidence_yr.csv to {wdir}')
    df_yr.to_csv((os.path.join(wdir, 'PfPR_ClinicalIncidence_yr.csv')), index=False)


if __name__ == "__main__":
    args = parse_args()
    jdir = args.job_dir
    # Load experiment object
    file = open(os.path.join(jdir, "exp.obj"), "rb")
    exp = pickle.load(file)
    wdir = os.path.join(exp.sim_out_dir,'MalSim')
    sweep_variables = ['index']
    create_sampleplots = True  # False
    all_age_sp = True # False 
    sim_start = exp.sim_start_year_ms

    # Execute all analyzers
    InputEIRAnalyzer(jdir, wdir)
    SurveyAllAgeAnalyzer(jdir, wdir, sweep_variables)
    BenchmarkAnalyzer(jdir, wdir, sweep_variables)
    MonthlyBenchmarkAnalyzer(jdir, wdir, sweep_variables)
    AnnualBenchmarkAnalyzer(jdir, wdir, sweep_variables)
    MonthlyAgebinAnalyzer(jdir, wdir, sweep_variables, sim_start)
    AnnualAgebinAnalyzer(jdir, wdir, sweep_variables, sim_start)

    # Create sample plots if specified
    if create_sampleplots:
        exp_tags = [x for x in exp.sweep_list if x != 'seed']  # + ['seed']
        # exp_tags = ['eir', 'cm_clinical', 'seasonality']

        channels_sample_chart = ['nPopulation', 'nHost', 'prevalence',
                                'incidence', 'clinical_incidence',
                                'severe_incidence', 'prevalence_2to10', 'EIR_gamb']
        if all_age_sp:
            all_age_sample_plot( wdir, sweep_variables=['index'], sample_channels=channels_sample_chart)
        sample_plot_yr(wdir, sweep_variables=exp_tags)
        sample_plot_mth(wdir, sweep_variables=exp_tags)

        emodom = ['MalSim']
        sweepvar = 'eir'
        monthly_trends(wdir=exp.sim_out_dir, emodom=emodom, channel='clinical_incidence', sweepvar=sweepvar)
        monthly_trends(wdir=exp.sim_out_dir, emodom=emodom, channel='severe_incidence', sweepvar=sweepvar)
        monthly_trends(wdir=exp.sim_out_dir, emodom=emodom, channel='prevalence', sweepvar=sweepvar)
        monthly_trends(wdir=exp.sim_out_dir, emodom=emodom, channel='prevalence_2to10', sweepvar=sweepvar)

        channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR']
        for channel in channel_list:
            monthly_timeseries(wdir=exp.sim_out_dir, emodom=emodom, channel=channel, sweepvar='emodom', facet_var='eir', agegrp='5-10')

        sweepvar = 'cm_clinical'
        prevalence2to10_to_incidence(wdir=exp.sim_out_dir, emodom=emodom, channel='prevalence')
        prevalence2to10_to_incidence(wdir=exp.sim_out_dir, emodom=emodom, channel='clinical_incidence')
        prevalence2to10_to_incidence(wdir=exp.sim_out_dir, emodom=emodom, channel='severe_incidence')
        input_to_simulated_eir(wdir=exp.sim_out_dir, emodom=emodom, sweepvar=sweepvar)
        eir_to_prevalence2to10(wdir=exp.sim_out_dir, emodom=emodom, sweepvar=sweepvar, eir_val='eir')
        eir_to_prevalence2to10(wdir=exp.sim_out_dir, emodom=emodom, sweepvar=sweepvar, eir_val='eir')