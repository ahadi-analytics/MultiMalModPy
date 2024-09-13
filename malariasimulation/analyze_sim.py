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


def convert_to_long(output, age_groups, agebins):
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
            'n': output[f"n_{agemin}_{agemax}"],
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


def post_processing(exp, job_directory):
    """
    Perform post-processing of malariasimulation simulation output data.
    This was previously done in R, but was brought to python to match the two other models.

    Parameters:
    - exp: Experiment object.
    - job_directory: Directory containing raw simulation output files.

    Saves:
    - {i}_daily.csv: for each simulation {i} in an experiment, saves the processed daily output.
    - daily.csv: combines all the processed daily outputs for each simulation in the experiment.
    
    Returns:
    None
    """
    agebins = exp.agebins
    agebins_days = [a * 365 for a in exp.agebins]

    columns_to_keep = ['timestep', 'Sm_gamb_count', 'Pm_gamb_count', 'Im_gamb_count', 'EIR_gamb', 'S_count',
                       'A_count', 'U_count', 'Tr_count', 'D_count', 'index']

    columns_with_ages = ['n', 'n_inc',  'n_inc_clinical', 'n_inc_severe', 'n_detect']


    needed_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n', 'nPopulation', 'prevalence_2to10', 'prev',
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
        df = pd.read_csv(os.path.join(job_directory, f'malariasimulation_jobs/{i}_out.csv'))
        df = df.loc[:, df.columns.isin(columns_to_keep + ['n_detect_730_3650','n_730_3650'])]
        days_in_months = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
        days_in_months = np.repeat(days_in_months, [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
        days_in_months = np.tile(days_in_months, int(max(df['timestep']) / 365))
        df['month'] = days_in_months
        df['year'] = np.floor(df['timestep'] / 365.000001).astype(int)
        for pair in age_groups:
            df[f'prev_{pair[0]}_{pair[1]}'] = df[f'n_detect_{pair[0]}_{pair[1]}'] / df[f'n_{pair[0]}_{pair[1]}']

        df['prevalence_2to10'] = df['n_detect_730_3650'] / df['n_730_3650']
        output = convert_to_long(df, age_groups, agebins)
        output['year'] = output['year'] + exp.sim_start_year_malariasimulation
        output = output[needed_channels]
        output = output[output['timestep'] > (exp.burnin * 365)]
        output['timestep'] = output['timestep'] - (exp.burnin * 365)
        #output.to_csv(os.path.join(job_directory, f'malariasimulation_jobs/{i}_daily.csv'), index=False) # not need to be written out per default, since daily.csv is used
        daily = pd.concat([daily, output], axis=0)
    daily.to_csv((os.path.join(wdir, 'daily.csv')), index=False)


def InputEIRAnalyzer(jdir, wdir, daily=False):
    """
    Run the InputEIRAnalyzer for Malariasimulation experiments.
    If daily is True, generate the EIR_daily.csv ONLY.
    """
    print("Running InputEIRAnalyzer...", flush=True)
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns

    channels_to_keep = ['index', 'timestep', 'month', 'year', 'nPopulation', 'EIR_gamb', 'n_infectious_mos',
                        'n_total_mos_pop']

    df = pd.read_csv(os.path.join(wdir, 'daily.csv'))
    df = df[channels_to_keep + ['ageGroup']]
    df = df[df['ageGroup'] == '0-0']

    df = df[channels_to_keep]
    df['EIR_gamb'] = df['EIR_gamb'] / df['nPopulation']
    if daily:
        df_daily = df.merge(scen_df, on='index', how='inner')
        columns_to_keep = ['index', 'seed', 'timestep', 'month', 'year', 'nPopulation', 'EIR_gamb',
                           'cm_clinical', 'seasonality', 'scen_id', 'num_seeds', 'cm_start', 'cm_severe',
                           'n_infectious_mos', 'n_total_mos_pop']

        if 'eir_malariasimulation' in df_daily:  # if the user sets different values between malariasimulation and EMOD, this should catch if the

            columns_to_keep = columns_to_keep + ['eir_malariasimulation', 'eir_scalar_timestep_daily', 'eir_scalar_malariasimulation']

            columns_to_keep = [col for col in columns_to_keep if col in df_daily.columns]
            df_daily = df_daily[columns_to_keep]
            df_daily = df_daily.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)
            df_daily = df_daily.rename(
                {'eir_scalar_timestep_daily': 'eir_scalar_timestep', 'eir_scalar_malariasimulation': 'eir_scalar'}, axis=1)
        else:
            columns_to_keep = columns_to_keep + ['output_target']
            columns_to_keep = [col for col in columns_to_keep if col in df_daily.columns]
            df_daily = df_daily[columns_to_keep]
            df_daily = df_daily.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)

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
        print(f'Saving EIR_mth.csv to {wdir}')
        df_mth.to_csv((os.path.join(wdir, 'EIR_mth.csv')), index=False)

        # Yearly aggregation - keep years
        df_yr = df.groupby(['index', 'year'], as_index=False)['EIR_gamb'].sum()
        vdf_yr = df.groupby(['index', 'year'], as_index=False)[mean_channels].mean()
        df_yr = df_yr.merge(vdf_yr, on=['index', 'year'], how='inner')
        df_yr = df_yr.merge(scen_df, on='index', how='inner')
        df_yr = df_yr.rename({'EIR_gamb': 'simulatedEIR'}, axis=1)
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
        print(f'Saving EIR.csv to {wdir}')
        df_yr.to_csv((os.path.join(wdir, 'EIR.csv')), index=False)


def SurveyAllAgeAnalyzer(jdir, wdir, sweep_variables):
    """
    Run the SurveyAllAgeAnalyzer for malariasimulation experiments.
    """
    print("Running SurveyAllAgeAnalyzer...", flush=True)

    # Read the scenario data from the CSV file
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'output_target'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns

    # Read experiment data daily
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev']
    channels_to_keep = ['index', 'timestep', 'month', 'year','ageGroup',
                        'age_upper'] + sum_channels + mean_channels

    df = pd.read_csv(os.path.join(wdir, 'daily.csv'))
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


def TimeavrgAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None):
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

    Returns:
        None
    """
    print("Running TimeavrgAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR.csv'))
    eir_df = eir_df[['index', 'output_target', 'simulatedEIR','n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels

    df = pd.read_csv(os.path.join(wdir, 'daily.csv'))
    df = df[channels_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n']

    df_pfpr2to10 = df.groupby(sweep_variables)[['prevalence_2to10']].agg(np.mean).reset_index()

    ## Aggregate years
    n_surveys_per_year = 365
    n_surveys = round(len(df['timestep'].unique()), 0)
    n_years = round(n_surveys / 365, 0)
    df = df.groupby(sweep_variables + ['agebin'])[
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
            adf = adf.groupby(sweep_variables)[['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(
                np.sum).reset_index()
            adf['prevalence'] = adf['n_prev'] / (adf['n'])

            # (events per person per annum)
            adf['clinical_incidence'] = adf['n_inc_clinical'] / adf['n']
            adf['severe_incidence'] = adf['n_inc_severe'] / adf['n'] 
            adf['ageGroup'] = ageCond_labels
            adf['n'] = adf['n'] / n_years
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables)
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'output_target'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on='index', how='inner')

    #Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence']  * ( 0.5 * cdf['cm_severe'] + ( 1 - cdf['cm_severe']) )
    
    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    
    cdf = cdf.rename({'n': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])

    print(f'\nSaving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file named 'mmmpy_timeavrg.csv'
    cdf.to_csv((os.path.join(wdir, 'mmmpy_timeavrg.csv')), index=False)
    
    if exp.run_mode == 'calibrun':
            u5 = cdf[cdf['ageGroup']=='0-5'].groupby('scen_id')['clinical_incidence'].agg('mean').reset_index()
            u5 = u5.rename(columns={'clinical_incidence':'clinical_incidence_U5'})
            all_ages = cdf[cdf['ageGroup']=='0-100'].groupby('scen_id')['clinical_incidence'].agg('mean').reset_index()
            cdf = cdf[cdf['ageGroup']=='0-100']
            cdf = cdf.groupby(['scen_id','model_input_malariasimulation','seasonality','cm_clinical'])[['simulatedEIR','prevalence_2to10','prevalence','severe_incidence','n_total_mos_pop']].agg('mean').reset_index()
            cdf = cdf.merge(all_ages, on = 'scen_id')
            cdf = cdf.merge(u5, on = 'scen_id')
            cdf = cdf.drop(['scen_id'],axis=1)
            cdf['modelname'] = 'malariasimulation'
            cdf = cdf.rename(columns={'model_input_malariasimulation':'input_target'})
            cdf.to_csv((os.path.join(wdir, 'interpolation_data.csv')), index=False)
            cdf.to_csv((os.path.join(exp.interp_path, 'malariasimulation', f'{exp.exp_name}_interpolation_data.csv')))


def DailyAgeBinAnalyzer(jdir, wdir, sweep_variables,age_groups_aggregates=None):
    """
    Run the DailyAgeBinAnalyzer equivalent for malariasimulation experiments.
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
    print("Running DailyAgeBinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Convert the experiment data to a DataFrame and format it
    sum_channels = ['n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']
    mean_channels = ['nPopulation', 'prevalence_2to10', 'prev', 'n_infectious_mos', 'n_total_mos_pop']
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup',
                        'age_upper'] + sum_channels + mean_channels
    # df = load_combined_daily_output(jdir, channels_to_keep)
    df = pd.read_csv(os.path.join(wdir, 'daily.csv'))
    df = df[channels_to_keep]
    df['n_prev'] = df['prev'] * df['n']
    df['incidence'] = (df['n_inc'] / df['n'])
    df['clinical_incidence'] = (df['n_inc_clinical'] / (df['n'] / 365)) ## Daily to annualized incidence
    df['severe_incidence'] = (df['n_inc_severe'] / (df['n'] / 365))
    df['agebin'] = round(df['age_upper'] / 365, 1)

    # Align to common output terminology used
    df = df.rename({'n': 'nHost', 'n_inc': 'nInfect', 'n_inc_clinical': 'nUncomp', 'n_inc_severe': 'nSevere',
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
            adf = adf.groupby(sweep_variables + ['timestep','month', 'year']).agg(
                nHost=('nHost', 'sum'),
                prevalence=('prevalence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                clinical_incidence=('clinical_incidence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                severe_incidence=('severe_incidence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                prevalence_2to10=('prevalence_2to10', 'mean')
            ).reset_index()
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    ## Add scenarios variables
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'output_target'], axis=1, errors='ignore')  ## remove EMOD specific columns

    df = cdf.merge(scen_df, on=sweep_variables, how='inner')
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_daily.csv'))
    eir_df = eir_df[['index', 'timestep', 'month', 'year', 'simulatedEIR', 'output_target']]
    df = df.merge(eir_df, on=['index', 'timestep', 'month', 'year'], how='inner')

    #Severe Incidence Recalculation
    df['severe_incidence'] = df['severe_incidence']  * ( 0.5 * df['cm_severe'] + ( 1 - df['cm_severe']) )

    # Let's limit the output of daily, so its a little more reasonable for us to process.
    columns_to_keep = ['index', 'scen_id', 'seed', 'ageGroup', 'timestep', 'simulatedEIR', 'n_infectious_mos',
                       'n_total_mos_pop', 'nHost', 'clinical_incidence', 'severe_incidence', 'prevalence', 'prevalence_2to10']

    # Iterate over columns to drop and check if they exist
    columns_to_keep = [col for col in columns_to_keep if col in df.columns]
    df = df[columns_to_keep]

    # Save the processed DataFrame to a CSV file
    print(f'\nSaving outputs to: {wdir}')
    df.to_csv((os.path.join(wdir, 'mmmpy_daily.csv')), index=False)


def FiveDayAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates=None, cc = None):
    """
    Run the FiveDayAgebinAnalyzer for OpenMalaria experiments to generate
    and save a results dataframe for defined age groups over time (5days and years).

    Args:
        jdir (str): Path to the directory containing simulation job data.
        wdir (str): Path to the working directory.
        sweep_variables (list): List of sweep variables.
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.

    Saves:
        mmmpy_5day.csv

    Returns:
        None
    """
    print("Running FiveDayAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],[0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_daily.csv'))
    eir_df = eir_df.groupby(sweep_variables + ['year', 'timestep'])[['simulatedEIR', 'output_target','n_infectious_mos', 'n_total_mos_pop']].agg( np.mean).reset_index()  # mean across runs per  timestep , month and year
    eir_df = eir_df[['index', 'timestep', 'year', 'simulatedEIR' ,'n_infectious_mos', 'n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    channels_to_keep = ['index', 'timestep',  'year', 'ageGroup', 'age_upper',
                        'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n', 'nPopulation', 'prevalence_2to10', 'prev']

    df = pd.read_csv(os.path.join(wdir, 'daily.csv'),usecols=channels_to_keep)
    #df = df[channels_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n']

    df['day'] = (df['timestep'] - 1) % 365 + 1
    df['5day'] = df['day'].apply(lambda x: 5 * math.ceil(x/5))
    df = df.groupby(sweep_variables + ['agebin', '5day',  'year']).agg({'n_prev':['sum'],
                                                                        'n_inc':['sum'], 
                                                                        'n_inc_clinical':['sum'], 
                                                                        'n_inc_severe':['sum'], 
                                                                        'n':['sum'],
                                                                        'nPopulation':['mean'],
                                                                        'prevalence_2to10':['mean'],
                                                                        'prev':['mean']}).reset_index()
    df.columns = df.columns.get_level_values(0)
    df = df.rename(columns={'5day': 'day'})

    ## EIR
    eir_df['day'] = (eir_df['timestep'] - 1) % 365 + 1
    eir_df['5day'] = eir_df['day'].apply(lambda x: 5 * math.ceil(x/5))
    eir_df = eir_df.groupby(sweep_variables + ['5day','year']).agg({'simulatedEIR':['sum'],'n_infectious_mos':['mean'], 
                                                          'n_total_mos_pop':['mean'], 'timestep':['max']}).reset_index()
    eir_df.columns = eir_df.columns.get_level_values(0)
    eir_df = eir_df.rename(columns={'5day': 'day'})
    df_pfpr2to10 = df.groupby(sweep_variables + ['day', 'year'])[['prevalence_2to10']].agg(
        np.mean).reset_index()
    df = df[sweep_variables +['agebin', 'day', 'year', 'n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']]

    df['n'] = df['n'] / (365 / 73)
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
            adf = adf.groupby(sweep_variables + ['day','year'])[
                ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()

            adf['prevalence'] = adf['n_prev'] / (adf['n'])
            # events per person per annum (annualized)
            # adf['incidence'] = (adf['n_inc'] / adf['n']/ 12)
            adf['clinical_incidence'] = (adf['n_inc_clinical'] / (adf['n'] / 73))  ## 5-Daily to annualized incidence
            adf['severe_incidence'] = (adf['n_inc_severe'] / (adf['n'] / 73))
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['day', 'year'])
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['entomology_mode'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')

    cdf = cdf.merge(eir_df, on=['index', 'day',  'year'], how='inner')

    #Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence']  * ( 0.5 * cdf['cm_severe'] + ( 1 - cdf['cm_severe']) )

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    cdf = cdf.rename({'n': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])
    #cdf['date'] = cdf.apply(lambda x: datetime.date(int(x['year']), 1, 1) + datetime.timedelta(days=int(x['day']) - 1), axis=1)

    print(f'\nSaving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file
    cdf.to_csv((os.path.join(wdir, 'mmmpy_5day.csv')), index=False)
    if cc:
        cdf = cdf[['scen_id', 'seed', 'timestep', 'cm_clinical', 'seasonality', 'output_target', 'cc_change', 
                'cc_title', 'ageGroup', 'timestep', 'simulatedEIR', 'prevalence_2to10', 'prevalence', 
                'clinical_incidence', 'severe_incidence', 'n_total_mos_pop', 'n_infectious_mos']]
        cdf.to_csv((os.path.join(wdir, 'mmmpy_ccstep_daily.csv')), index=False)


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
        mmmpy_mth.csv

    Returns:
        None
    """
    print("Running MonthlyAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_mth.csv'))
    eir_df = eir_df.groupby(sweep_variables + ['month', 'year'])[['simulatedEIR', 'output_target', 'n_total_mos_pop']].agg(
        np.mean).reset_index()  # mean across runs per month and year
    eir_df = eir_df[['index', 'month', 'year', 'output_target', 'simulatedEIR', 'n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup', 'age_upper',
                        'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n', 'nPopulation', 'prevalence_2to10', 'prev']

    df = pd.read_csv(os.path.join(wdir, 'daily.csv'))
    df = df[channels_to_keep]
    df['agebin'] = round(df['age_upper'] / 365, 1)
    df['n_prev'] = df['prev'] * df['n']

    df_pfpr2to10 = df.groupby(sweep_variables + ['month', 'year'])[['prevalence_2to10']].agg(np.mean).reset_index()

    ## Aggregate days to month and years
    n_surveys_per_year = int(round(len(df['timestep'].unique()) / len(df['year'].unique()), 0))

    df = df.groupby(sweep_variables + ['agebin', 'month', 'year'])[
        ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()

    df['n'] = df['n'] / (365 / 12)
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
            adf = adf.groupby(sweep_variables + ['month', 'year'])[
                ['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n']].agg(np.sum).reset_index()

            adf['prevalence'] = adf['n_prev'] / (adf['n'])
            # events per person per annum (annualized)
            # adf['incidence'] = (adf['n_inc'] / adf['n']/ 12)
            adf['clinical_incidence'] = (adf['n_inc_clinical'] / (adf['n'] / 12))
            adf['severe_incidence'] = (adf['n_inc_severe'] / (adf['n'] / 12))
            adf['ageGroup'] = ageCond_labels
            cdf = pd.concat([cdf, adf])

    cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=sweep_variables + ['month', 'year'])
    scen_df = pd.read_csv(os.path.join(jdir, 'scenarios_wseeds.csv'))
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'output_target'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on=['index', 'month', 'year'], how='inner')

    #Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence']  * ( 0.5 * cdf['cm_severe'] + ( 1 - cdf['cm_severe']) )

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    cdf = cdf.rename({'n': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])
    cdf['date'] = cdf.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)

    print(f'\nSaving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file
    cdf.to_csv((os.path.join(wdir, 'mmmpy_mth.csv')), index=False)


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
        mmmpy_yr.csv

    Returns:
        None
    """
    print("Run AnnualAgebinAnalyzer...", flush=True)

    if not age_groups_aggregates:
        age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Read the EIR data from the CSV file
    eir_df = pd.read_csv(os.path.join(wdir, 'EIR_yr.csv'))
    eir_df = eir_df[['index', 'year', 'output_target', 'simulatedEIR', 'n_total_mos_pop']]

    # Convert the experiment data to a DataFrame and format it
    channels_to_keep = ['index', 'timestep', 'month', 'year', 'ageGroup',
                        'age_upper', 'prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe', 'n', 'nPopulation',
                        'prevalence_2to10']
    # df = load_combined_daily_output(jdir, channels_to_keep)
    df = pd.read_csv(os.path.join(wdir, 'daily.csv'))
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
    scen_df = scen_df.drop(['x_Temporary_Larval_Habitat', 'entomology_mode', 'output_target'],
                           axis=1, errors='ignore')  ## remove EMOD specific columns
    cdf = cdf.merge(scen_df, on=sweep_variables, how='inner')
    cdf = cdf.merge(eir_df, on=['index', 'year'], how='inner')

    #Severe Incidence Recalculation
    cdf['severe_incidence'] = cdf['severe_incidence']  * ( 0.5 * cdf['cm_severe'] + ( 1 - cdf['cm_severe']) )

    # Rename columns for alignment with OpenMalaria results
    cdf['mortality'] = ''
    cdf = cdf.rename({'n': 'nHost'}, axis=1)
    cdf = cdf.drop(columns=['n_prev', 'n_inc', 'n_inc_clinical', 'n_inc_severe'])

    print(f'\nSaving outputs to: {wdir}')
    # Save the processed DataFrame to a CSV file
    cdf.to_csv((os.path.join(wdir, 'mmmpy_yr.csv')), index=False)


if __name__ == "__main__":
    args = parse_args()
    jdir = args.job_dir
    # Load experiment object 
    file = open(os.path.join(jdir, "exp.obj"), "rb")
    exp = pickle.load(file)

    wdir = os.path.join(exp.sim_out_dir, 'malariasimulation')
    sweep_variables = ['index']
    all_age_sp = False  # False
    seeds = exp.num_seeds
    age_groups_aggregates = exp.age_groups_aggregates

    # Python Post-Processing
    post_processing(exp, jdir)
    daily_path = os.path.join(wdir, 'daily.csv')

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
    if 'timeavrg' in exp.analyzer_list:
        TimeavrgAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates)

    ## 5 day (or daily) timeseries per age groups
    if 'daily' in exp.analyzer_list or '5day' in exp.analyzer_list or 'cc_step' in exp.analyzer_list:
        InputEIRAnalyzer(jdir, wdir, daily=True)
        if 'daily' in exp.analyzer_list:
            DailyAgeBinAnalyzer(jdir, wdir, sweep_variables)
        if '5day' in exp.analyzer_list or 'cc_step' in exp.analyzer_list:
            ccstep = 'cc_step' in exp.intervention_list
            FiveDayAgebinAnalyzer(jdir, wdir, sweep_variables, age_groups_aggregates,cc=ccstep)
