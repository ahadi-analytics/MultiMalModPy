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
    """
    Parses command-line arguments for simulation specifications.

    This function uses the argparse library to handle command-line inputs
    required for running simulation experiments. It defines required and optional
    arguments, including the job directory and model names.

    Returns:
        argparse.Namespace: An object containing the parsed command-line arguments.

    Command Line Arguments:
        -d/--directory (str): The job directory where the exp.obj file is located. This argument is required.
        -m/--modelname (str): One or more model names to compare. This argument is optional
                              and defaults to ['EMOD', 'OpenMalaria', 'malariasimulation'].
    """

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
        default=['EMOD', 'OpenMalaria', 'malariasimulation']
    )

    return parser.parse_args()


def custom_sort_key(age_group):
    """
    Custom sort key function for sorting age groups.

    This function extracts the lower bound of an age group represented as
    a string in the format 'X-Y' and returns it as an integer. It is
    primarily used for sorting age groups in ascending order based on
    their lower bounds.

    Args:
        age_group (str): The age group string in the format 'X-Y',
                         where X is the lower bound and Y is the upper bound.

    Returns:
        int: The lower bound of the age group as an integer.
    """

    return int(age_group.split('-')[0])


# Creates the combined dataframes for all models simulated.
def get_output_df(wdir, modelname, yr=False, mth=False, daily=False, custom_name=None,
                  save_combined=False):
    """
    Load and combine data from the model output files.

    This function reads model output files from a specified working directory
    and combines the data into a single DataFrame. It supports different data
    formats based on the specified parameters for yearly, monthly, or daily
    data.

    Args:
        wdir (str): Working directory where the data files are located.
        modelname (str or list of str): Name of models for which result CSVs
                                         should be loaded (case sensitive).
        yr (bool, optional): Set to True if the data files have yearly data.
                             Defaults to False.
        mth (bool, optional): Set to True if the data files have monthly data.
                             Defaults to False.
        daily (bool, optional): Set to True if the data files have daily timestep
                                data. Defaults to False. If both mth and daily
                                are True, only daily will be processed.
        custom_name (str, optional): Custom filename to use instead of the default
                                      based on the time period. Defaults to None.
        save_combined (bool, optional): Set to True to save the combined DataFrame
                                         to a CSV file. Defaults to False.

    Returns:
        tuple: A tuple containing:
            - df (DataFrame): Combined DataFrame containing the combined data
                              for the models listed in modelname.
            - wdir (str): Updated working directory (if applicable).

    Raises:
        ValueError: If an invalid modelname value is specified.
    """

    cols_to_keep = None  # default read all
    fname = 'mmmpy_timeavrg.csv'
    if yr:
        fname = 'mmmpy_yr.csv'
    if mth:
        fname = 'mmmpy_mth.csv'
    if daily:
        fname = 'mmmpy_daily.csv'
        # cols_to_keep = ['index', 'timestep', 'ageGroup', 'simulatedEIR', 'prevalence_2to10', 'prevalence',
        #                'clinical_incidence', 'severe_incidence', 'seed']
    if custom_name:
        fname = f'{custom_name}.csv'

    file_paths = [os.path.join(wdir, fname)]

    for model in modelname:
        file_paths.append(os.path.join(wdir, model, fname))

    existing_files = [path for path in file_paths if os.path.isfile(path)]

    if not existing_files:
        return pd.DataFrame(), wdir

    if os.path.isfile(os.path.join(wdir, fname)):
        df = pd.read_csv((os.path.join(wdir, fname)), low_memory=False)
    else:

        dfs = []
        for model in modelname:
            model_path = os.path.join(wdir, model, fname)
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
    Calculate x-axis and y-axis values for each plot.

    This function groups the input DataFrame by a specified variable and
    calculates the mean values for the specified x and y channels. It also
    computes the 95% confidence interval for the y values.

    Args:
        df (DataFrame): The DataFrame used to group and calculate x and y values.
        grpvar (str): The variable in the DataFrame used to group the x and y values.
        x_channel (str): The variable serving as the x-axis in the graph.
        y_channel (str): The variable serving as the y-axis in the graph.

    Returns:
        tuple: A tuple containing:
            - xmean (DataFrame): A DataFrame containing values for the x-axis.
            - ymean (DataFrame): A DataFrame containing values for the y-axis,
                                 including the 95% confidence interval (min and max).
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
    """
    Convert a number of days since January 1, 2005, to a date.

    This function takes an integer representing the number of days
    since January 1, 2005, and returns the corresponding date.

    Args:
        x (int): The number of days since January 1, 2005.

    Returns:
        date: A datetime.date object representing the corresponding date.
    """

    import datetime
    return datetime.date(2005, 1, 1) + datetime.timedelta(days=x)


def color_selector(i, s):
    """
    Select a color index based on the model name.

    This function returns a color index based on the specified model name.
    If the model name is recognized, a predefined index is returned;
    otherwise, the input index is returned.

    Args:
        i (int): The default index to return if the model name is not recognized.
        s (str): The name of the model. Possible values include:
            - 'EMOD'
            - 'malariasimulation'
            - 'OpenMalaria'

    Returns:
        int: The color index corresponding to the model name.
    """

    if s == 'EMOD':
        return 0
    elif s == 'malariasimulation':
        return 1
    elif s == 'OpenMalaria':
        return 2
    else:
        return i


def get_ylab(channel):
    """
    Retrieve the y-axis label for a given channel.

    This function returns a formatted string representing the y-axis label
    based on the specified channel name. The labels correspond to specific
    epidemiological measures.

    Args:
        channel (str): The name of the channel for which to retrieve the label.
            Possible values include:
            - 'prevalence_2to10'
            - 'prevalence'
            - 'clinical_incidence'
            - 'severe_incidence'
            - 'simulatedEIR'

    Returns:
        str: The corresponding y-axis label for the channel, or None if the
        channel is not recognized.
    """

    channel_labels = {'prevalence_2to10': '$\it{Pf}$PR$_{2-10}$ (%)',
                      'prevalence': '$\it{Pf}$PR (%)',
                      'clinical_incidence': 'Clinical incidence (pppy)',
                      'severe_incidence': 'Severe incidence (pppy)',
                      'simulatedEIR': 'simulated EIR'
                      }

    return channel_labels.get(channel)


def subset_dataframe_for_plot(df, figure_vars, agegrp=None, filter_target=True):
    """
    Filter the input DataFrame for plotting based on specified criteria.

    This function filters the DataFrame according to the provided figure variables,
    optional age groups, and other selection criteria to prepare the data for
    visualization. It also returns a string summarizing the filtering applied.

    Args:
        df (pd.DataFrame): The input DataFrame containing simulation results.
        figure_vars (list of str): List of variables used for plotting, which influences
            the filtering process.
        agegrp (str or list of str, optional): Specific age group(s) to filter by.
            If provided, only the data for these age groups will be retained.
            Defaults to None, meaning no filtering by age group will occur.
        filter_target (bool, optional): If True, the function will filter the DataFrame
            to retain the maximum output target value if certain variables are not
            present in `figure_vars`. Defaults to True.

    Returns:
        tuple: A tuple containing:
            - pd.DataFrame: The filtered DataFrame.
            - str: A summary string describing the filtering that was applied.

    Raises:
        ValueError: If 'modelname' is not included in `figure_vars` and there
        are multiple unique model names in the DataFrame.
    """

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