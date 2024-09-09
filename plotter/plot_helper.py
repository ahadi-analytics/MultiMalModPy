import argparse
import pickle
import os
import numpy as np
import pandas as pd
import matplotlib as mpl

import seaborn as sns

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

mpl.rcParams['pdf.fonttype'] = 3
plt.rcParams.update({'font.size': 16})
plt.rcParams.update({'font.sans-serif': "Arial"})


# Helps process script inputs
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
    parser.add_argument(
        "-m",
        "--modelname",
        nargs='+',
        type=str,
        required=False,
        help="Name of models to compare",
        default=['EMOD', 'OpenMalaria', 'MalSim']
    )

    return parser.parse_args()

def custom_sort_key(age_group):
    return int(age_group.split('-')[0])


# Creates the combined dataframes for all models simulated.
def get_output_df(wdir, modelname, yr=False, mth=False, daily=False, custom_name=None,
                  save_combined=False):
    """
    Load and combine data from the model output files.
    Parameters:
        wdir (str): Working directory where the data files are located.
        modelname (str or list of str): Name of models for which result CSVs should be loaded, case sensitive.
        mth (bool, optional): Set to True if the data files have monthly data. Default is False.
        daily (bool, optional): Set to True if the data files have daily timestep data. Default is False. If both mth and daily are true, only daily will be processed.
        timeseries (bool, optional): Set to True if the unaggregated timeseries data should be read in. Default is False
        condensed (bool, optional): Set to True, only a set list of eirs will be present in the final csv.
    Returns:
        df (DataFrame): Combined DataFrame containing the combined data for the models listed in modelname.
        wdir (str): Updated working directory (if applicable).
    Raises:
        ValueError: If invalid modelname value is specified.
    """
    cols_to_keep = None  # default read all
    fname = 'Benchmark.csv'
    if yr:
        fname = 'PfPR_ClinicalIncidence_yr.csv'
    if mth:
        fname = 'PfPR_ClinicalIncidence_mth.csv'
    if daily:
        fname = 'PfPR_ClinicalIncidence_daily.csv'
        # cols_to_keep = ['index', 'timestep', 'ageGroup', 'simulatedEIR', 'prevalence_2to10', 'prevalence',
        #                'clinical_incidence', 'severe_incidence', 'seed']
    if custom_name:
        fname = f'{custom_name}.csv'

    file_paths = [os.path.join(wdir, fname)]
    model_paths = {'OpenMalaria': 'om', 'EMOD': 'em', 'MalSim': 'MalSim'}

    for model in model_paths:
        if model in modelname:
            file_paths.append(os.path.join(wdir, model_paths[model], fname))

    existing_files = [path for path in file_paths if os.path.isfile(path)]

    if not existing_files:
        return pd.DataFrame(), wdir

    if os.path.isfile(os.path.join(wdir, fname)):
        df = pd.read_csv((os.path.join(wdir, fname)), low_memory=False)
    else:
        # Model-specific file paths
        model_paths = {'OpenMalaria': 'om', 'EMOD': 'em', 'MalSim': 'MalSim'}

        dfs = []
        for model in model_paths:
            if model in modelname:
                model_path = os.path.join(wdir, model_paths[model], fname)
                try:
                    if os.path.isfile(model_path):
                        df = pd.read_csv(model_path, usecols=cols_to_keep)
                        df['modelname'] = model
                        if model == 'EMOD':
                            df['seed'] = df['seed'] + 1
                        dfs.append(df)
                    else:
                        print(f"File not found for {model}: {model_path}")
                except Exception as e:
                    print(f"Error reading {model_path}: {e}")

        if not dfs:
            return pd.DataFrame(), wdir

        df = pd.concat(dfs, ignore_index=True)

        if 'ageGroup' in df.columns:
            try:
                age_grps = sorted(list(df['ageGroup'].unique()), key=custom_sort_key)
            except:
                age_grps = list(df['ageGroup'].unique())
            df['ageGroup'] = df['ageGroup'].astype('category')
            df['ageGroup'] = df['ageGroup'].cat.reorder_categories(age_grps)

        warning_df = df[df['simulatedEIR'] == 0]
        if len(warning_df) > 0 and daily is False:  # we don't want to include simulations were eir was 0 or less, because we won't get any outcome measures and that crashes the system
            print('Warning: some eirs had simulated EIRS of 0, and were removed')
            df = df[df['simulatedEIR'] > 0]
            df = df[df['simulatedEIR'].notnull()]

        if not daily and save_combined:
            df.to_csv(os.path.join(wdir, f'{fname}'), index=False)
    return df, wdir


# Calculates x-axis and y-axis values for each plot
def get_x_y(df, grpvar, x_channel, y_channel):
    """
    Load and combine data from the model output files.
    Parameters:
        df (DataFrame): The Dataframe we will use to group and calculate our x and y values.
        grpvar (str): The variable in the dataframe we will group the x and y values by.
        x_channel (str): The variable that will serve as our x axis in the graph
        y_channel (str): The variable that will serve as our y axis in the graph
    Returns:
        xmean (DataFrame): a DataFrame containing values for the x axis.
        ymean (DataFrame): a DataFrame containing values for the y axis as well as either 95% confidence interval or percentiles 2.75 to 97.25
    """
    xmean = df.groupby(grpvar)[x_channel].agg(np.mean).reset_index()
    ymean = df.groupby(grpvar)[y_channel].agg(np.mean).reset_index()
    p_df = pd.DataFrame(columns=[grpvar, f'{y_channel}_min', f'{y_channel}_max'])
    for i, row in ymean.iterrows():
        p = df[df[grpvar] == row[grpvar]]
        pmin = np.nanpercentile(p[y_channel], 2.5, axis=0)
        pmax = np.nanpercentile(p[y_channel], 97.5, axis=0)
        new_row = pd.DataFrame([{grpvar: row[grpvar], f'{y_channel}_min': pmin, f'{y_channel}_max': pmax}])
        p_df = pd.concat([p_df, new_row], axis=0, ignore_index=True)
    ymean = pd.merge(left=ymean, right=p_df, on=grpvar)
    return xmean, ymean


def convert_to_date(x):
    import datetime
    return datetime.date(2005, 1, 1) + datetime.timedelta(days=x)


def color_selector(i, s):
    if s == 'EMOD':
        return 0
    elif s == 'MalSim':
        return 1
    elif s == 'OpenMalaria':
        return 2
    else:
        return i


def get_ylab(channel):
    channel_labels = {'prevalence_2to10': '$\it{Pf}$PR$_{2-10}$ (%)',
                      'prevalence': '$\it{Pf}$PR (%)',
                      'clinical_incidence': 'Clinical incidence (pppy)',
                      'severe_incidence': 'Severe incidence (pppy)',
                      'simulatedEIR': 'simulated EIR'
                      }

    return channel_labels.get(channel)


def subset_dataframe_for_plot(df, figure_vars, agegrp=None, filter_target=True):
    txt = 'Filtered dataset by: '

    if agegrp is not None:
        if 'ageGroup' not in figure_vars:
            if isinstance(agegrp, list):
                df = df[df['ageGroup'].isin(agegrp)]
                txt += f'ageGroup in {agegrp}, '
            else:
                df = df[df['ageGroup'] == agegrp]
                txt += f'ageGroup {agegrp}, '

    if 'cm_clinical' not in figure_vars:
        selected_cm = df['cm_clinical'].min()
        df = df[df['cm_clinical'] == selected_cm]
        txt += f'cm_clinical {selected_cm}, '

    if 'seasonality' not in figure_vars:
        selected_season = 'seasonal' if 'seasonal' in df['seasonality'].unique() else df['seasonality'].unique()[0]
        df = df[df['seasonality'] == selected_season]
        txt += f'seasonality {selected_season}, '

    if filter_target:
      if not any(var in figure_vars for var in ['simulatedEIR', 'prevalence_2to10', 'output_target']) :
          selected_output = df['output_target'].max()
          df = df[df['output_target'] == selected_output]
          txt += f'output_target {selected_output}, '

    if 'modelname' not in figure_vars and df['modelname'].nunique() > 1:
        raise ValueError('modelname needs to be specified in plot if results were combined for more than 1 model')

    # Remove trailing comma and space if any filtering has been done
    if txt.endswith(', '):
        txt = txt[:-2]

    return df, txt