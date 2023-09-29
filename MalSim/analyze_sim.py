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

#TODO ADD FUNCTIONS THAT WILL CONVERT MALSIM VALUES TO APPROPRIATE VALUES
#TO COMPARE TO EMOD AND OPENMALARIA
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
    
    
def malsim_conversions(wdir = None):
    """
    Takes the daily.csv malsim output file and creates pfpr_clinical csv's and benchmark csv's
    TODO Make sure that the prevalences, incidences and other variables match the unit we expect (i.e. per person per annum)
    """
    
    #Access daily.csv from output folder, add day, update year and update the first two age groups to match age group names in EMOD and OpenMalaria
    fname = 'daily.csv'
    df = pd.read_csv(os.path.join(wdir, f'MalSim/{fname}'))
    if 'ageGroup' in df.columns:
        age_grps = list(df['ageGroup'].unique())
        df['ageGroup'] = df['ageGroup'].astype('category')
        df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)  
    df['day'] = 1
    df['year'] = df['year'] + 1999
    df['ageGroup'] = df['ageGroup'].replace('0-0','0-0.5')
    df['ageGroup'] = df['ageGroup'].replace('0-1','0.5-1')
    
    # Create PfPR Monthly df, calculate Columns necessary, save to csv
    df_mth = df.groupby(['eir','cm_clinical','seasonality', 'year', 'month', 'ageGroup','seed'])[['nHost','prevalence_2to10','prevalence','clinical_incidence','severe_incidence','day']].agg(np.mean).reset_index()
    df_mth['nPatent'] = df_mth['prevalence'] * df_mth['nHost']
    df_mth['nUncomp'] = df_mth['clinical_incidence'] * df_mth['nHost']
    df_mth['nSevere'] = df_mth['severe_incidence'] * df_mth['nHost']
    df_mth['date'] = pd.to_datetime(dict(year=df_mth.year,month=df_mth.month,day=df_mth.day))  
    df_mth.to_csv(os.path.join(wdir, 'MalSim', 'PfPR_ClinicalIncidence_mth.csv'), index=False)
    
    
    # Create PfPR yearly df, calculate Columns necessary, save to csv
    df_year = df.groupby(['eir','cm_clinical','seasonality', 'year','ageGroup','seed'])[['nHost','prevalence_2to10','prevalence','clinical_incidence','severe_incidence','day']].agg(np.mean).reset_index()
    df_year['nPatent'] = df_year['prevalence'] * df_year['nHost']
    df_year['nUncomp'] = df_year['clinical_incidence'] * df_year['nHost']
    df_year['nSevere'] = df_year['severe_incidence'] * df_year['nHost']
    df_year.to_csv(os.path.join(wdir, 'MalSim', 'PfPR_ClinicalIncidence_yr.csv'), index=False)
    
    #Create Benchmark csv's
    #First group together under 5 age groups into one agegroup 0-5, then combine with older age groups (ignore 20-100 as it is not reported in other benchmark.csv's although it could be included if we decide), then save that as the "Benchmark.csv"
    #Note due to a memory issue with .groupby, we need to call the daily.csv again for both u5 and above5 groups
    u5_ages = ['0-0','0-1','1-2','2-5']
    df1 = pd.read_csv(os.path.join(wdir, f'MalSim/{fname}'))
    df_u5 = df1[df1['ageGroup'].isin(u5_ages)]
    df_u5 = df_u5.groupby(['eir','cm_clinical','seasonality','year','month'])[['nHost','prevalence_2to10','prevalence','clinical_incidence', 'severe_incidence']].agg(np.mean).reset_index()
    df_u5['ageGroup'] = '0-5'  
    
    above5_ages = ['5-10','10-15','15-20']
    df2 = pd.read_csv(os.path.join(wdir, f'MalSim/{fname}'))
    df_above5 = df2[df2['ageGroup'].isin(above5_ages)]
    df_above5 = df_above5.groupby(['eir','cm_clinical','seasonality','year','month','ageGroup'])[['nHost','prevalence_2to10','prevalence','clinical_incidence', 'severe_incidence']].agg(np.mean).reset_index()
    
    df_benchmark = pd.concat([df_u5, df_above5])
    df_benchmark.to_csv(os.path.join(wdir, 'MalSim', 'Benchmark.csv'), index=False)
    
    
    #Create benchmark_mth csv
    df_bmth = df_benchmark.groupby(['eir','cm_clinical','seasonality','ageGroup','month'])[['nHost','prevalence_2to10','prevalence','clinical_incidence','severe_incidence']].agg(np.mean).reset_index()
    df_bmth['nPatent'] = df_bmth['prevalence'] * df_bmth['nHost']
    df_bmth['nUncomp'] = df_bmth['clinical_incidence'] * df_bmth['nHost']
    df_bmth['nSevere'] = df_bmth['severe_incidence'] * df_bmth['nHost']
    df_bmth.to_csv(os.path.join(wdir, 'MalSim', 'Benchmark_mth.csv'), index=False)
    
    #Create benchmark_yr csv
    df_byr = df_benchmark.groupby(['eir','cm_clinical','seasonality','ageGroup','year'])[['nHost','prevalence_2to10','prevalence','clinical_incidence','severe_incidence']].agg(np.mean).reset_index()
    df_byr['nPatent'] = df_byr['prevalence'] * df_byr['nHost']
    df_byr['nUncomp'] = df_byr['clinical_incidence'] * df_byr['nHost']
    df_byr['nSevere'] = df_byr['severe_incidence'] * df_byr['nHost']
    df_byr.to_csv(os.path.join(wdir, 'MalSim', 'Benchmark_yr.csv'), index=False)
    return


if __name__ == "__main__":
    args = parse_args()
    wdir = args.output_dir
    malsim_conversions(wdir)
    
    exp_tags = ['eir', 'cm_clinical', 'seasonality']
      
    emodom = ['MalSim']
    sweepvar = 'eir'
    monthly_trends(wdir, emodom, channel='clinical_incidence', sweepvar=sweepvar)
    monthly_trends(wdir, emodom, channel='severe_incidence', sweepvar=sweepvar)
    monthly_trends(wdir, emodom, channel='prevalence', sweepvar=sweepvar)
    monthly_trends(wdir, emodom, channel='prevalence_2to10', sweepvar=sweepvar)
    monthly_trends(wdir, emodom=emodom, channel='eir', sweepvar=sweepvar)
    
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