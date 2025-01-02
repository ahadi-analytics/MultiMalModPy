import os
import sys
import argparse
import pickle
import datetime
import pandas as pd
import numpy as np
from idmtools.entities import IAnalyzer
from idmtools.entities.simulation import Simulation
import math

parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(parent_dir)
from utility.experiment import LoadExperiment


def parse_args():
    """
    Parse command-line arguments for simulation specifications.

    This function sets up the argument parser to handle command-line inputs,
    specifically for specifying the job directory and an optional experiment ID.
    The job directory is required to locate the `exp.obj` file, while the
    experiment ID is optional and is necessary for EMOD runs.

    Returns:
        Namespace: A namespace object containing the parsed command-line arguments.
        The attributes include:
            - directory (str): The job directory where `exp.obj` is located.
            - exp_id (str or None): The unique ID of the simulation experiment,
              or None if not specified.
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
        "-i",
        "--exp_id",
        type=str,
        required=False,
        help="Unique ID of simulation experiment, required for EMOD runs",
        default=None
    )
    return parser.parse_args()


class SurveyAllAgeAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.

    This class provides functionality to parse and analyze output data from inset charts produced
    by EMOD simulations. It allows for aggregation and processing of simulation results, focusing
    on various channels of interest.

    Args:
        expt_name (str): Name of the experiment.
        sweep_variables (list): List of sweep variables. Defaults to None.
        inset_channels (list): List of inset channels. Defaults to None.
        daily (bool): Flag indicating whether the data is daily. Defaults to False.
        working_dir (str): Working directory for the analysis. Defaults to "./".
        start_year (int): Start year of the simulation. Defaults to 2022.
        burnin (None or int): Number of burn-in years to remove from results data. Defaults to None.
    Saves:
        All_Age_Outputs.csv
    Returns:

    """

    @classmethod
    def monthparser(self, x):
        if x == 0:
            return 12
        else:
            return datetime.datetime.strptime(str(x), '%j').month

    def __init__(self, expt_name, sweep_variables=None, channels=None, daily=False, working_dir=".", start_year=2022,
                 burnin=None):
        super(SurveyAllAgeAnalyzer, self).__init__(working_dir=working_dir, filenames=["output/InsetChart.json"])
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.inset_channels = channels or ['Statistical Population', 'Births', 'Disease Deaths',
                                           'New Infections', 'Newly Symptomatic', 'New Clinical Cases',
                                           'New Severe Cases'
                                           'Fever Prevalence', 'True Prevalence', 'PCR Gametocyte Prevalence',
                                           'PCR Parasite Prevalence', 'Blood Smear Parasite Prevalence',
                                           'PfHRP2 Prevalence',
                                           'Infectious Vectors', 'Daily EIR']
        self.expt_name = expt_name
        self.start_year = start_year
        self.daily = daily
        self.emod_burnin = burnin

    def map(self, data, simulation: Simulation):
        simdata = pd.DataFrame({x: data[self.filenames[0]]['Channels'][x]['Data'] for x in self.inset_channels})

        # Create time variables
        simdata['Time'] = simdata.index
        simdata['Day'] = simdata['Time'] % 365
        simdata['Year'] = simdata['Time'].apply(lambda x: int(x / 365) + self.start_year)
        simdata['date'] = simdata.apply(
            lambda x: datetime.date(int(x['Year']), 1, 1) + datetime.timedelta(int(x['Day']) - 1), axis=1)

        # Add scenario sweeps (parameter that were varied) to data
        for sweep_var in self.sweep_variables:
            if sweep_var in simulation.tags.keys():
                simdata[sweep_var] = simulation.tags[sweep_var]
            elif sweep_var == 'Run_Number':
                simdata[sweep_var] = 0
        return simdata

    def reduce(self, all_data):

        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("No data have been returned... Exiting...")
            return

        adf = pd.concat(selected).reset_index(drop=True)
        adf = adf.rename(columns={'Daily Bites per Human': 'Bites per Human', 'Daily EIR': 'EIR'})
        if self.daily:
            adf.to_csv(os.path.join(self.working_dir, 'EMOD', 'All_Age_InsetChart_daily.csv'), index=False)

        if self.emod_burnin is not None:
            adf = adf[adf['Year'] >= self.start_year + self.emod_burnin]

        # Change data to Year-months format, exclude days
        adf['date'] = pd.to_datetime(adf['date'])
        adf['date'] = adf['date'].dt.strftime('%b-%Y')

        # Aggregate data per date and sweep_variables using sum and mean specific to outcome channel
        sum_channels = ['Births', 'Disease Deaths', 'New Infections', 'Newly Symptomatic', 'New Clinical Cases',
                        'New Severe Cases', 'Infectious Vectors', 'EIR']
        mean_channels = ['Statistical Population', 'Fever Prevalence', 'True Prevalence', 'PCR Gametocyte Prevalence',
                         'PCR Parasite Prevalence', 'Blood Smear Parasite Prevalence',
                         'PfHRP2 Prevalence']

        sdf = adf.groupby(['date'] + self.sweep_variables)[sum_channels].agg(np.sum).reset_index()
        mdf = adf.groupby(['date'] + self.sweep_variables)[mean_channels].agg(np.mean).reset_index()
        adf = pd.merge(left=sdf, right=mdf, on=(self.sweep_variables + ['date']))

        adf = adf.rename(columns={'Run_Number': 'seed'})
        adf['seed'] = adf['seed'] + 1

        # Save the processed DataFrame to a CSV file named 'All_Age_Outputs.csv'
        adf.to_csv(os.path.join(self.working_dir, 'EMOD', 'All_Age_Outputs.csv'), index=False)


class InputEIRAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for generating results DataFrame on transmission outcome metrics.

    This class processes simulation output data related to transmission metrics and provides
    functionality to generate daily, monthly, and yearly reports on transmission outcomes.

    Args:
        expt_name (str): Name of the experiment.
        channels (list): List of channels. Defaults to None.
        sweep_variables (list): List of sweep variables. Defaults to None.
        working_dir (str): Working directory for the analysis. Defaults to "./".
        start_year (int): Start year of the analysis. Defaults to 2010.
        selected_year (None or int): Year to be extracted from the simulation results. Defaults to None (keep all).
        daily_report (bool): Flag indicating whether to save results DataFrame with daily transmission data. Defaults to False.
        monthly_report (bool): Flag indicating whether to save results DataFrame with monthly transmission data. Defaults to False.
        burnin (None or int): Number of burn-in years to drop from simulation results. Defaults to None (keep all).

    Saves:
        One or more CSV files based on the `daily` flag:
            - `EIR_daily.csv`: Contains daily EIR data, if `daily=True`.
            - `EIR_mth.csv`: Contains monthly aggregated EIR data, if `daily=False`.
            - `EIR_yr.csv`: Contains yearly aggregated EIR data, if `daily=False`.
            - `EIR.csv`: Contains mean EIR over the monitoring period, if `daily=False`.
    """

    @classmethod
    def monthparser(self, x):
        if x == 0:
            return 12
        else:
            return datetime.datetime.strptime(str(x), '%j').month

    def __init__(self, expt_name, channels=None, sweep_variables=None, working_dir='./', start_year=2010,
                 selected_year=None, daily_report=False, monthly_report=False, burnin=None):

        super(InputEIRAnalyzer, self).__init__(working_dir=working_dir,
                                               filenames=["output/InsetChart.json"])  # ReportMalariaFiltered
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.channels = channels or ['Daily Bites per Human', 'Daily EIR', 'Rainfall', 'Adult Vectors',
                                     'Infectious Vectors']
        self.start_year = start_year
        self.selected_year = selected_year
        self.daily_report = daily_report
        self.monthly_report = monthly_report
        self.expt_name = expt_name
        self.emod_burnin = burnin

    def map(self, data, simulation):
        """Process the simulation data and map it to a DataFrame.

        Args:
            data (dict): Dictionary containing simulation data.
            simulation (Simulation): The simulation instance for extracting tags.

        Returns:
            pd.DataFrame: DataFrame containing the mapped simulation data with additional time variables.
        """

        simdata = pd.DataFrame({x: data[self.filenames[0]]['Channels'][x]['Data'] for x in self.channels})
        # simdata = simdata[-365:]
        simdata['time'] = simdata.index
        simdata['day'] = simdata['time'] % 365
        simdata['month'] = simdata['day'].apply(lambda x: self.monthparser((x + 1) % 365))
        simdata['year'] = simdata['time'].apply(lambda x: int(x / 365) + self.start_year)
        simdata['date'] = simdata.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)
        if self.selected_year is not None:
            simdata = simdata.loc[(simdata['year'] == self.selected_year)]

        # Add varying parameter values that describe and identify the simulation scenarios
        for sweep_var in self.sweep_variables:
            if sweep_var in simulation.tags.keys():
                try:
                    simdata[sweep_var] = simulation.tags[sweep_var]
                except:
                    simdata[sweep_var] = '-'.join([str(x) for x in simulation.tags[sweep_var]])
        return simdata

    def reduce(self, all_data):
        """Aggregate and process all simulation data.

        Args:
            all_data (dict): Dictionary containing data from multiple simulations.

        Returns:
            None: If no data is returned or if processing is complete.
        """
        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return

        adf = pd.concat(selected).reset_index(drop=True)
        adf['Infectious Vectors'] = round(adf['Infectious Vectors'] * adf['Adult Vectors'], 0)
        if self.emod_burnin is not None:
            adf = adf[adf['year'] >= self.start_year + self.emod_burnin]

        # Aggregate data and save for specified time intervals (daily, monthly, annually)
        grp_channels = self.sweep_variables  # [x for x in self.sweep_variables if x != "Run_Number"] ## Keep runs
        adf = adf.groupby(['time', 'date', 'day', 'month', 'year'] + grp_channels)[self.channels].agg(
            np.mean).reset_index()

        # Add Larval Habitat Multipliers and sweep variables to EIR dataframe
        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        adf = adf.merge(scen_df, on='scen_id', how='inner')
        grp_channels = list(set(grp_channels + list(scen_df.columns)))
        adf = adf.rename(columns={'Adult Vectors': 'n_total_mos_pop', 'Infectious Vectors': 'n_infectious_mos'})
        if self.daily_report:
            outcome_cols = ['Daily EIR', 'n_total_mos_pop', 'n_infectious_mos']
            columns_to_keep = ['scen_id', 'Run_Number', 'time', 'day', 'month', 'year', 'eir'] + outcome_cols

            columns_to_keep = [col for col in columns_to_keep if col in adf.columns]
            df = adf[columns_to_keep]
            df = df.rename(columns={'Daily EIR': 'simulatedEIR', 'time': 'timestep'})

            df['day'] = df['day'] + 1
            df['timestep'] = (df['timestep'] + 1) - (self.emod_burnin * 365)
            df.to_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_daily.csv'), index=False)
        else:
            sum_channels = ['Daily Bites per Human', 'Daily EIR', 'Rainfall']
            mean_channels = ['n_total_mos_pop', 'n_infectious_mos']

            # Monthly aggregation - keep months and years
            if self.monthly_report:
                df = adf.groupby(['year', 'month'] + grp_channels)[sum_channels].agg(np.sum).reset_index()
                df = df.rename(columns={'Daily Bites per Human': 'Monthly Bites per Human', 'Daily EIR': 'Monthly EIR'})
                vdf = adf.groupby(['year', 'month'] + grp_channels)[mean_channels].agg(np.mean).reset_index()
                df = df.merge(vdf, on=(['year', 'month'] + grp_channels), how='inner')
                df.to_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_mth.csv'), index=False)

            # Yearly aggregation - keep years
            df = adf.groupby(['year'] + grp_channels)[sum_channels].agg(np.sum).reset_index()
            vdf = adf.groupby(['year'] + grp_channels)[mean_channels].agg(np.mean).reset_index()
            df = df.merge(vdf, on=(['year'] + grp_channels), how='inner')
            df = df.rename(columns={'Daily Bites per Human': 'Annual Bites per Human', 'Daily EIR': 'Annual EIR'})
            df.to_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_yr.csv'), index=False)

            # Mean over monitoring period
            nyears = len(adf['year'].unique())
            df = adf.groupby(grp_channels)[sum_channels].agg(np.sum).reset_index()
            vdf = adf.groupby(grp_channels)[mean_channels].agg(np.mean).reset_index()
            df = df.merge(vdf, on=grp_channels, how='inner')
            df['Daily EIR'] = df['Daily EIR'] / nyears
            df['Daily Bites per Human'] = df['Daily Bites per Human'] / nyears
            df['n_total_mos_pop'] = df['n_total_mos_pop'] / nyears
            df['n_infectious_mos'] = df['n_infectious_mos'] / nyears
            df = df.rename(columns={'Daily Bites per Human': 'Annual Bites per Human', 'Daily EIR': 'Annual EIR'})
            df.to_csv(os.path.join(self.working_dir, 'EMOD', 'EIR.csv'), index=False)


class TimeavrgAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing EMOD summary reports to generate
    and save a results DataFrame for defined age groups aggregated over the monitoring period.

    Args:
        expt_name (str): Name of the experiment.
        sweep_variables (list): List of sweep variables. Defaults to None.
        working_dir (str): Working directory for the analysis. Defaults to './'.
        start_year (int): Start year of the simulation experiment. Defaults to 1920.
        end_year (int): End year of the simulation experiment. Defaults to 2020.
        age_groups_aggregates (list): List of age group aggregates. Defaults to a predefined set of age groups.
        burnin (None or int): Number of burn-in iterations. Defaults to None.

    Saves:
        mmmpy_timeavrg.csv
        interpolation_data.csv (if exp.run_mode == 'calibrun')

    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, age_groups_aggregates=None, burnin=None):
        """
        Initialize the TimeavrgAgebinAnalyzer instance.
        """

        super(TimeavrgAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                     filenames=[
                                                         f"output/MalariaSummaryReport_Annual_{start_year}to{end_year}.json"])
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.age_groups_aggregates = age_groups_aggregates or [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15],
                                                               [15, 20], [20, 100],
                                                               [0, 5], [0, 100]]
        self.emod_burnin = burnin

    def map(self, data, simulation: Simulation):
        """Process the simulation data and map it to a DataFrame.

        Args:
            data (dict): Dictionary containing simulation data.
            simulation (Simulation): The simulation instance for extracting tags.

        Returns:
            pd.DataFrame: DataFrame containing the mapped simulation data with additional time variables.
        """

        adf = pd.DataFrame()
        nyears = self.end_year - self.start_year + 1
        for fname in self.filenames:

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10-True'][:nyears]

            for age in list(range(0, len(age_bins))):
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin-True'][:nyears]
                pfpr = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:nyears]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:nyears]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:nyears]
                pop = [x[age] for x in d]

                simdata = pd.DataFrame({'year': range(self.start_year, self.end_year + 1),
                                        'prevalence': pfpr,
                                        'clinical_incidence': clinical_cases,  # per person per annum
                                        'severe_incidence': severe_cases,  # per person per annum
                                        'nHost': pop})
                simdata['agebin'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

        # Add varying parameter values that describe and identify the simulation scenarios
        for sweep_var in self.sweep_variables:
            if sweep_var in simulation.tags.keys():
                try:
                    adf[sweep_var] = simulation.tags[sweep_var]
                except:
                    adf[sweep_var] = '-'.join([str(x) for x in simulation.tags[sweep_var]])

        return adf

    def reduce(self, all_data):
        """Aggregate and process all simulation data.

        Args:
            all_data (dict): Dictionary containing data from multiple simulations.

        Returns:
            None: If no data is returned or if processing is complete.
        """

        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return

        df = pd.concat(selected).reset_index(drop=True)
        if self.emod_burnin is not None:
            df = df[df['year'] >= self.start_year + self.emod_burnin]
        df_pfpr2to10 = df.groupby(self.sweep_variables)[['prevalence_2to10']].agg(np.mean).reset_index()

        ## Aggregate years
        df = df.groupby(self.sweep_variables + ['agebin'])[
            ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(
            np.mean).reset_index()
        df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
        df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
        df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

        cdf = pd.DataFrame()

        # Loop over age groups to aggregate results data
        for i in range(0, len(self.age_groups_aggregates)):
            ages = self.age_groups_aggregates[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables)[['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
                adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per annum)
                adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'])  # (events per person per annum)
                adf['ageGroup'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables)
        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        cdf = cdf.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables)[['Annual EIR', 'n_total_mos_pop', 'n_infectious_mos']].agg(
                np.mean).reset_index()  # mean across monitoring years and runs
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables)
            # cdf['eir'] = [round(x, 1) if x < 1 else round(x, 0) for x in cdf['Annual EIR']]
        else:
            cdf['simulatedEIR'] = cdf['model_input_emod']
            cdf['inputEIR'] = cdf['model_input_emod']

        # Rename columns for alignment with OpenMalaria results
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['seed'] = cdf['seed'] + 1
        cdf['mortality'] = ''
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/EMOD')

        # Save the processed DataFrame to a CSV file named 'mmmpy_timeavrg.csv'
        cdf.to_csv((os.path.join(self.working_dir, 'EMOD', 'mmmpy_timeavrg.csv')), index=False)

        if exp.run_mode == 'calibrun':
            u5 = cdf[cdf['ageGroup'] == '0-5'].groupby('scen_id')['clinical_incidence'].agg('mean').reset_index()
            u5 = u5.rename(columns={'clinical_incidence': 'clinical_incidence_U5'})
            all_ages = cdf[cdf['ageGroup'] == '0-100'].groupby('scen_id')['clinical_incidence'].agg(
                'mean').reset_index()
            cdf = cdf[cdf['ageGroup'] == '0-100']
            cdf = cdf.groupby(['scen_id', 'model_input_emod', 'seasonality', 'cm_clinical'])[
                ['simulatedEIR', 'prevalence_2to10', 'prevalence', 'severe_incidence', 'n_total_mos_pop']].agg(
                'mean').reset_index()
            cdf = cdf.merge(all_ages, on='scen_id')
            cdf = cdf.merge(u5, on='scen_id')
            cdf = cdf.drop(['scen_id'], axis=1)
            cdf['modelname'] = 'EMOD'
            cdf = cdf.rename(columns={'model_input_emod': 'input_target'})
            cdf.to_csv((os.path.join(wdir, 'EMOD', 'interpolation_data.csv')), index=False)
            cdf.to_csv((os.path.join(exp.interp_path, 'EMOD', f'{exp.exp_name}_interpolation_data.csv')), index=False)


class AnnualAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer and modified for analyzing EMOD summary reports to generate
    and save a results dataframe for defined age groups over time (years).

    Parameters:
        - expt_name (str): Name of the experiment.
        - sweep_variables (list): List of sweep variables. Defaults to None.
        - working_dir (str): Working directory for the analysis. Defaults to './'.
        - start_year (int): Start year of the simulation experiment. Defaults to 1920.
        - end_year (int): End year of the simulation experiment. Defaults to 2020.
        - age_groups_aggregates (list): List of age group aggregates. Defaults to None.
        - burnin (None or int): Number of burn-in iterations. Defaults to None.

    Saves:
        mmmpy_yr.csv

    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, age_groups_aggregates=None, burnin=None):

        super(AnnualAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                   filenames=[
                                                       f"output/MalariaSummaryReport_Annual_{start_year}to{end_year}.json"])
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.age_groups_aggregates = age_groups_aggregates or [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15],
                                                               [15, 20], [20, 100], [0, 5], [0, 100]]
        self.emod_burnin = burnin

    def map(self, data, simulation: Simulation):
        """
        Processes the simulation data and maps it to a DataFrame.

        Args:
            data (dict): Dictionary containing simulation data.
            simulation (Simulation): The simulation instance for extracting tags.

        Returns:
            pd.DataFrame: Mapped DataFrame containing simulation data for age bins.
        """
        adf = pd.DataFrame()
        nyears = self.end_year - self.start_year + 1
        for fname in self.filenames:

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10-True'][:nyears]

            for age in list(range(0, len(age_bins))):
                # Extract data for each age bin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin-True'][:nyears]
                pfpr = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:nyears]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:nyears]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:nyears]
                pop = [x[age] for x in d]

                # Create a DataFrame for the simulation data
                simdata = pd.DataFrame({'year': range(self.start_year, self.end_year + 1),
                                        'prevalence': pfpr,
                                        'clinical_incidence': clinical_cases,  # per person per year
                                        'severe_incidence': severe_cases,  # per person per year
                                        'nHost': pop})
                simdata['agebin'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

        # Add varying parameter values that describe and identify the simulation scenarios
        for sweep_var in self.sweep_variables:
            if sweep_var in simulation.tags.keys():
                try:
                    adf[sweep_var] = simulation.tags[sweep_var]
                except:
                    adf[sweep_var] = '-'.join([str(x) for x in simulation.tags[sweep_var]])

        return adf

    def reduce(self, all_data):
        """
        Aggregates and processes all simulation data.

        Args:
            all_data (dict): Dictionary containing data from multiple simulations.

        Returns:
            None: If no data is returned or if processing is complete.
        """
        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return

        df = pd.concat(selected).reset_index(drop=True)
        if self.emod_burnin is not None:
            df = df[df['year'] >= self.start_year + self.emod_burnin]
        df_pfpr2to10 = df.groupby(self.sweep_variables + ['year'])[['prevalence_2to10']].agg(np.mean).reset_index()

        # Aggregate months to years
        df = df.groupby(self.sweep_variables + ['agebin', 'year'])[
            ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(np.mean).reset_index()

        df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
        df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
        df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

        cdf = pd.DataFrame()

        # Loop over the age groups to aggregate agebins to the defined groups
        for i in range(0, len(self.age_groups_aggregates)):
            ages = self.age_groups_aggregates[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables + ['year'])[['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
                adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per year)
                adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'])  # (events per person per year)
                adf['ageGroup'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables + ['year'])
        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        cdf = cdf.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['year'])[['Annual EIR', 'n_total_mos_pop']].agg(
                np.mean).reset_index()
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables + ['year'])

        else:
            cdf['simulatedEIR'] = cdf['model_input_emod']
            cdf['inputEIR'] = cdf['model_input_emod']

        # Rename columns for alignment with OpenMalaria results
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['seed'] = cdf['seed'] + 1
        cdf['mortality'] = ''

        # Save the processed DataFrame to a CSV file
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/EMOD')
        cdf.to_csv((os.path.join(self.working_dir, 'EMOD', 'mmmpy_yr.csv')), index=False)


class MonthlyAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing EMOD summary reports
    and generating a results dataframe for defined age groups over time (monthly and yearly).

    Args:
        expt_name (str): Name of the experiment.
        sweep_variables (list, optional): List of sweep variables. Defaults to None.
        working_dir (str, optional): Working directory for the analysis. Defaults to './'.
        start_year (int, optional): Start year of the simulation experiment. Defaults to 1920.
        end_year (int, optional): End year of the simulation experiment. Defaults to 2020.
        age_groups_aggregates (list, optional): List of age group aggregates. Defaults to None.
        burnin (int, optional): Number of burn-in iterations. Defaults to None.

    Saves:
        mmmpy_mth.csv

    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, age_groups_aggregates=None, burnin=None):
        """
        Initializes the MonthlyAgebinAnalyzer with the provided parameters.
        """
        super(MonthlyAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                    filenames=[f"output/MalariaSummaryReport_Monthly_{x}.json"
                                                               for x in range(start_year, end_year)]
                                                    )
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.age_groups_aggregates = age_groups_aggregates or [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15],
                                                               [15, 20], [20, 100], [0, 5], [0, 100]]
        self.emod_burnin = burnin

    def map(self, data, simulation: Simulation):
        """
        Processes the simulation data and maps it to a DataFrame.

        Args:
            data (dict): Dictionary containing simulation data.
            simulation (Simulation): The simulation instance for extracting tags.

        Returns:
            pd.DataFrame: Mapped DataFrame containing simulation data for age bins.
        """
        adf = pd.DataFrame()
        # Loop over summary reports (separate ones for each year)
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10-True'][:12]

            for age in list(range(0, len(age_bins))):
                # Extract data per agebin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin-True'][:12]
                pfpr = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['New Infections by Age Bin'][:12]
                new_infect = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:12]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:12]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:12]
                pop = [x[age] for x in d]

                # Combine extracted data into a dataframe
                simdata = pd.DataFrame({'month': range(1, 13),
                                        'prevalence': pfpr,
                                        'nInfect': new_infect,
                                        'clinical_incidence': clinical_cases,  # per person per year
                                        'severe_incidence': severe_cases,  # per person per year
                                        'nHost': pop})
                simdata['nUncomp'] = [x * 12 for x in simdata['clinical_incidence']]  # per person per month
                simdata['nSevere'] = [x * 12 for x in simdata['severe_incidence']]  # per person per month
                simdata['year'] = year
                simdata['agebin'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

        # Add varying parameter values that describe and identify the simulation scenarios
        for sweep_var in self.sweep_variables:
            if sweep_var in simulation.tags.keys():
                try:
                    adf[sweep_var] = simulation.tags[sweep_var]
                except:
                    adf[sweep_var] = '-'.join([str(x) for x in simulation.tags[sweep_var]])
        return adf

    def reduce(self, all_data):
        """
        Aggregates and processes all simulation data.

        Args:
            all_data (dict): Dictionary containing data from multiple simulations.

        Returns:
            None: If no data is returned or if processing is complete.
        """
        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return
        df = pd.concat(selected).reset_index(drop=True)

        print(f'\nSaving outputs to: {os.path.join(self.working_dir, "EMOD")}')

        if self.emod_burnin is not None:
            df = df[df['year'] >= self.start_year + self.emod_burnin]

        df_pfpr2to10 = df.groupby(self.sweep_variables + ['year', 'month'])[['prevalence_2to10']].agg(
            np.mean).reset_index()

        df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
        df['nUncomp'] = df['clinical_incidence'] * (df['nHost'] / 12)  ## total cases per annum
        df['nSevere'] = df['severe_incidence'] * (df['nHost'] / 12)  ## total cases per annum

        cdf = pd.DataFrame()

        # Loop over the age groups to aggregate agebins to the defined groups
        for i in range(0, len(self.age_groups_aggregates)):
            ages = self.age_groups_aggregates[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables + ['year', 'month'])[
                    ['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
                adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'] / 12)  # (events per person per year)
                adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'] / 12)  # (events per person per year)
                adf['ageGroup'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables + ['year', 'month'])
        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        cdf = cdf.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['year'])[['Annual EIR']].agg(np.mean).reset_index()
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables + ['year'])

            eirdf_mth = pd.read_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_mth.csv'))
            eirdf_mth = eirdf_mth.groupby(self.sweep_variables + ['year', 'month'])[
                ['Monthly EIR', 'n_total_mos_pop']].agg(
                np.mean).reset_index()
            cdf = pd.merge(left=cdf, right=eirdf_mth, on=self.sweep_variables + ['year', 'month'])

            cdf = cdf.rename(columns={"Monthly EIR": "simulatedEIR"})
        else:
            cdf['simulatedEIR'] = cdf['model_input_emod']
            cdf['inputEIR'] = cdf['model_input_emod']

        # Rename columns for alignment with OpenMalaria results
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['seed'] = cdf['seed'] + 1
        cdf['mortality'] = ''
        cdf['date'] = cdf.apply(lambda x: datetime.date(int(x['year']), int(x['month']), 1), axis=1)

        # Save the processed DataFrame to a CSV file named 'PfPR_ClinicalIncidence_mth.csv'
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/EMOD')
        cdf.to_csv((os.path.join(self.working_dir, 'EMOD', 'mmmpy_mth.csv')), index=False)


class FiveDayAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer and modified for analyzing EMOD summary reports to generate
    and save a results dataframe for defined age groups over time (5day and years).
    We have a 5 Day Agebin Analyzer to accommodate OpenMalaria, which has a minimum reporting period of 5 days.

    Args:
        expt_name (str): Name of the experiment.
        sweep_variables (list): List of sweep variables. Defaults to None.
        working_dir (str): Working directory for the analysis. Defaults to './'.
        start_year (int): Start year of the simulation experiment. Defaults to 1920.
        end_year (int): End year of the simulation experiment. Defaults to 2020.
        age_groups_aggregates (list): List of age group aggregates. Defaults to None.
        burnin (None or int): Number of burn-in iterations. Defaults to None.
        cc (bool): Flag for change in conditions. Defaults to False.

    Saves:
        mmmpy_5day.csv (or mmmpy_ccstep_daily.csv if cc is True)

    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, age_groups_aggregates=None, burnin=None, cc=False):

        super(FiveDayAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                    filenames=[f"output/MalariaSummaryReport_FiveDaily_{x}.json"
                                                               for x in range(start_year, end_year)]
                                                    )
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.age_groups_aggregates = age_groups_aggregates or [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15],
                                                               [15, 20], [20, 100], [0, 5], [0, 100]]
        self.emod_burnin = burnin
        self.cc = cc

    def map(self, data, simulation: Simulation):
        """
        Process the simulation data and map it to a DataFrame.

        Args:
            data (dict): Dictionary containing simulation data.
            simulation (Simulation): The simulation instance for extracting tags.

        Returns:
            pd.DataFrame: Mapped DataFrame containing simulation data for age bins.
        """
        adf = pd.DataFrame()
        # Loop over summary reports (separate ones for each year)
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10-True'][:73]
            # timestep = data[fname]['DataByTime']['Time Of Report'][:73]

            for age in list(range(0, len(age_bins))):
                # Extract data per agebin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin-True'][:73]
                pfpr = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['New Infections by Age Bin'][:73]
                new_infect = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:73]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:73]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:73]
                pop = [x[age] for x in d]

                # Combine extracted data into a dataframe
                simdata = pd.DataFrame({'day': [t * 5 for t in range(1, 74)],
                                        'prevalence': pfpr,
                                        'nInfect': new_infect,
                                        'clinical_incidence': clinical_cases,  # per person per year
                                        'severe_incidence': severe_cases,  # per person per year
                                        'nHost': pop})
                simdata['nUncomp'] = [x * (365 / 5) for x in simdata['clinical_incidence']]  # per person per 5 days
                simdata['nSevere'] = [x * (365 / 5) for x in simdata['severe_incidence']]  # per person per 5 days
                simdata['year'] = year
                simdata['agebin'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

        # Add varying parameter values that describe and identify the simulation scenarios
        for sweep_var in self.sweep_variables:
            if sweep_var in simulation.tags.keys():
                try:
                    adf[sweep_var] = simulation.tags[sweep_var]
                except:
                    adf[sweep_var] = '-'.join([str(x) for x in simulation.tags[sweep_var]])
        return adf

    def reduce(self, all_data):
        """
        Aggregate and process all simulation data.

        Args:
            all_data (dict): Dictionary containing data from multiple simulations.

        Returns:
            None: If no data is returned or if processing is complete.
        """
        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return
        df = pd.concat(selected).reset_index(drop=True)

        print(f'\nSaving outputs to: {os.path.join(self.working_dir, "EMOD")}')

        if self.emod_burnin is not None:
            df = df[df['year'] >= self.start_year + self.emod_burnin]

        df_pfpr2to10 = df.groupby(self.sweep_variables + ['year', 'day'])[['prevalence_2to10']].agg(
            np.mean).reset_index()

        df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
        df['nUncomp'] = df['clinical_incidence'] * (df['nHost'] / (365 / 5))  ## total cases per annum
        df['nSevere'] = df['severe_incidence'] * (df['nHost'] / (365 / 5))  ## total cases per annum

        cdf = pd.DataFrame()

        # Loop over the age groups to aggregate agebins to the defined groups
        for i in range(0, len(self.age_groups_aggregates)):
            ages = self.age_groups_aggregates[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.agebin > ages[0]) & (df.agebin <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables + ['year', 'day'])[
                    ['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
                adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'] / (365 / 5))  # (events per person per year)
                adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'] / (365 / 5))  # (events per person per year)
                adf['ageGroup'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables + ['year', 'day'])

        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['year'])[['Annual EIR']].agg(np.mean).reset_index()
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables + ['year'])

            eirdf_daily = pd.read_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_daily.csv'))
            eirdf_daily = eirdf_daily.groupby(self.sweep_variables + ['year', 'day', 'timestep'])[
                ['simulatedEIR', 'n_total_mos_pop', 'n_infectious_mos']].agg('mean').reset_index()

            eirdf_daily['5day'] = eirdf_daily['day'].apply(lambda x: 5 * math.ceil(x / 5))
            eirdf_5day = eirdf_daily.groupby(self.sweep_variables + ['5day', 'year']).agg({'simulatedEIR': ['sum'],
                                                                                           'n_total_mos_pop': ['mean'],
                                                                                           'n_infectious_mos': ['mean'],
                                                                                           'timestep': [
                                                                                               'max']}).reset_index()
            eirdf_5day.columns = eirdf_5day.columns.get_level_values(0)
            eirdf_5day = eirdf_5day.rename(columns={'5day': 'day'})
            cdf = pd.merge(left=cdf, right=eirdf_5day, on=self.sweep_variables + ['year', 'day'])
        else:
            cdf['simulatedEIR'] = cdf['model_input_emod']
            cdf['inputEIR'] = cdf['model_input_emod']

        cdf = cdf.merge(scen_df, on='scen_id', how='inner')
        # Rename columns for alignment with OpenMalaria results
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['seed'] = cdf['seed'] + 1
        cdf['mortality'] = ''
        # cdf['date'] = cdf.apply( lambda x: datetime.date(int(x['year']), 1, 1) + datetime.timedelta(x['day'] - 1), axis=1)

        # Save the processed DataFrame to a CSV file
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/EMOD')
        cols_to_keep = ['scen_id', 'index', 'seed', 'output_target', 'model_input_emod', 'timestep',
                        'day', 'year', 'ageGroup', 'seasonality', 'cm_clinical', 'entomology_mode',
                        'simulatedEIR', 'prevalence_2to10', 'prevalence', 'clinical_incidence', 'severe_incidence',
                        'n_total_mos_pop', 'n_infectious_mos']
        if self.cc:
            cols_to_keep = cols_to_keep + ['cc_change', 'cc_factor', 'cc_timestep', 'cc_title']
            cdf.to_csv((os.path.join(self.working_dir, 'EMOD', 'mmmpy_ccstep_daily.csv')), index=False)
        else:
            cdf.to_csv((os.path.join(self.working_dir, 'EMOD', 'mmmpy_5day.csv')), index=False)


class DailyAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing summary report output specific to EMOD.

    This class saves a DataFrame per day and year from daily summary reports for each age bin
    specified in the report.

    Args:
        expt_name (str): Name of the experiment.
        sweep_variables (list): List of sweep variables. Defaults to None.
        working_dir (str): Working directory for the analysis. Defaults to "./".
        start_year (int): Start year of the simulation. Defaults to 2022.
        end_year (int): End year of the simulation. Defaults to 2022.
        burnin (None or int): Number of burn-in years to remove from results data. Defaults to None.
        age_groups_aggregates (list): List of age groups for aggregating results. Defaults to a predefined set of age groups.

    Saves:
        mmmpy_daily.csv

    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=2000,
                 end_year=2020, age_groups_aggregates=None, burnin=None):
        """
        Initialize the DailyAgebinAnalyzer instance.
        """

        super(DailyAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                  filenames=[f"output/MalariaSummaryReport_Daily_{x}.json"
                                                             for x in range(start_year, end_year)])
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.age_groups_aggregates = age_groups_aggregates or [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15],
                                                               [15, 20], [20, 100], [0, 5], [0, 100]]
        self.emod_burnin = burnin

    def map(self, data, simulation: Simulation):

        adf = pd.DataFrame()
        # Loop over summary reports (separate ones for each year)
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10-True']

            for age in list(range(0, len(age_bins))):
                # Extract data per agebin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin-True']
                pfpr = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['New Infections by Age Bin']
                new_infect = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin']
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin']
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin']
                pop = [x[age] for x in d]

                # Combine extracted data into a dataframe
                simdata = pd.DataFrame({'day': range(1, 366),
                                        'prevalence': pfpr,
                                        'nInfect': new_infect,
                                        'clinical_incidence': clinical_cases,  # per person per year
                                        'severe_incidence': severe_cases,  # per person per year
                                        'nHost': pop})
                simdata['nUncomp'] = [x for x in simdata['clinical_incidence']]  # per person per 1 day period
                simdata['nSevere'] = [x for x in simdata['severe_incidence']]  # per person per 1 day period
                simdata['year'] = year
                simdata['agebin'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

        # Add varying parameter values that describe and identify the simulation scenarios
        for sweep_var in self.sweep_variables:
            if sweep_var in simulation.tags.keys():
                try:
                    adf[sweep_var] = simulation.tags[sweep_var]
                except:
                    adf[sweep_var] = '-'.join([str(x) for x in simulation.tags[sweep_var]])
        return adf

    def reduce(self, all_data):

        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return
        df = pd.concat(selected).reset_index(drop=True)
        if self.emod_burnin is not None:
            df = df[df['year'] >= self.start_year + self.emod_burnin]

        cdf = pd.DataFrame()
        # Age group labels
        for i in range(0, len(self.age_groups_aggregates)):
            ages = self.age_groups_aggregates[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df['agebin'] > ages[0]) & (df['agebin'] <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables + ['day', 'year']).agg(
                    nHost=('nHost', 'sum'),
                    prevalence=('prevalence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                    clinical_incidence=(
                        'clinical_incidence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                    severe_incidence=('severe_incidence', lambda x: np.average(x, weights=adf.loc[x.index, 'nHost'])),
                    prevalence_2to10=('prevalence_2to10', 'mean')
                ).reset_index()
                adf['ageGroup'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))

        cdf = cdf.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'EMOD', 'EIR_daily.csv'))
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables + ['day', 'year', 'eir'])
        else:
            cdf['simulatedEIR'] = ''
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['seed'] = cdf['seed'] + 1

        #  Reorder the DataFrame columns , by specified first columns to appear first
        print(f'\nSaving outputs to: {os.path.join(self.working_dir, "EMOD")}')
        cdf.to_csv((os.path.join(self.working_dir, 'EMOD', 'mmmpy_daily.csv')), index=False)


if __name__ == "__main__":
    # Load additional required modules
    from idmtools.analysis.analyze_manager import AnalyzeManager
    from idmtools.core import ItemType
    from idmtools.core.platform_factory import Platform

    # Parse command line arguments
    args = parse_args()
    job_directory = args.directory
    exp_id = args.exp_id
    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    # Set location of output files
    wdir = exp.sim_out_dir

    exp_name = exp.exp_name
    age_groups_aggregates = exp.age_groups_aggregates  # Defined in utility.helper.py

    # Define tags and simulation experiment configurations
    exp_tags = ['scen_id', 'Run_Number']

    start_year = exp.sim_start_year_emod
    end_year = exp.end_year
    monitoring_start = end_year - exp.monitoring_years

    if exp.emod_step == 'burnin':
        end_year = start_year + exp.emod_burnin
        burnin = 0  ## Keep all years
    elif exp.emod_step == 'pickup':
        burnin = 0
    else:
        burnin = int(exp.emod_burnin)  ## Years burnin to discard when running burnin+pickup together

    # Define which outcome metrics to process in inset_chart (all age per daily timestep)
    channels_inset_chart = ['Statistical Population', 'Births', 'Disease Deaths',
                            'New Infections', 'Newly Symptomatic', 'New Clinical Cases', 'New Severe Cases',
                            'Fever Prevalence', 'True Prevalence', 'PCR Gametocyte Prevalence',
                            'PCR Parasite Prevalence', 'Blood Smear Parasite Prevalence', 'PfHRP2 Prevalence',
                            'Infectious Vectors', 'Daily EIR']
    # Run analyzers
    with Platform('SLURM_LOCAL', job_directory=exp.suite_directory) as platform:
        all_age_analyzer = [SurveyAllAgeAnalyzer(expt_name=exp_name,
                                               channels=channels_inset_chart,
                                               sweep_variables=exp_tags,
                                               start_year=start_year,
                                               burnin=burnin,
                                               working_dir=wdir)]

        eir_analyzer = [InputEIRAnalyzer(expt_name=exp_name,
                                         sweep_variables=exp_tags,
                                         start_year=start_year,
                                         daily_report=False,
                                         monthly_report=True,
                                         burnin=burnin,
                                         working_dir=wdir)]

        daily_analyzers = [DailyAgebinAnalyzer(expt_name=exp_name,
                                               start_year=start_year,
                                               end_year=end_year,
                                               age_groups_aggregates=age_groups_aggregates,
                                               sweep_variables=exp_tags,
                                               working_dir=wdir,
                                               burnin=burnin)]

        fiveday_analyzers = [FiveDayAgebinAnalyzer(expt_name=exp_name,
                                                   start_year=start_year,
                                                   end_year=end_year,
                                                   age_groups_aggregates=age_groups_aggregates,
                                                   sweep_variables=exp_tags,
                                                   working_dir=wdir,
                                                   burnin=burnin)]

        monthly_analyzers = [MonthlyAgebinAnalyzer(expt_name=exp_name,
                                                   start_year=start_year,
                                                   end_year=end_year,
                                                   age_groups_aggregates=age_groups_aggregates,
                                                   sweep_variables=exp_tags,
                                                   working_dir=wdir,
                                                   burnin=burnin)]

        annual_analyzers = [AnnualAgebinAnalyzer(expt_name=exp_name,
                                                 sweep_variables=exp_tags,
                                                 working_dir=wdir,
                                                 start_year=start_year,
                                                 end_year=end_year - 1,
                                                 age_groups_aggregates=age_groups_aggregates,
                                                 burnin=burnin)]

        analyzers_timeavrg = [TimeavrgAgebinAnalyzer(expt_name=exp_name,
                                                     sweep_variables=exp_tags,
                                                     working_dir=wdir,
                                                     start_year=start_year,
                                                     end_year=end_year - 1,
                                                     age_groups_aggregates=age_groups_aggregates,
                                                     burnin=burnin)]
        ## EIR analyzer
        # Run eir_analyzers first to avoid any of the other analyzers running without this dependency completed.
        if exp.entomology_mode == 'dynamic':
            manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=eir_analyzer,
                                     partial_analyze_ok=True)
            manager.analyze()
            if 'daily' in exp.analyzer_list or '5day' in exp.analyzer_list or 'cc_step' in exp.analyzer_list:
                daily_eir_analyzer = [InputEIRAnalyzer(expt_name=exp_name,
                                                       sweep_variables=exp_tags,
                                                       start_year=start_year,
                                                       daily_report=True,
                                                       monthly_report=True,
                                                       burnin=burnin,
                                                       working_dir=wdir)]
                manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)],
                                         analyzers=daily_eir_analyzer,
                                         partial_analyze_ok=True)
                manager.analyze()

        # Default
        analyzer = []
        # Age groups aggregated to all and time intervals are kept unaggregated (1day, InsetChart)
        if 'surveyallage' in exp.analyzer_list:
            analyzer = analyzer + all_age_analyzer
        # Aggregated timeseries per age groups
        if 'timeavrg' in exp.analyzer_list:
            analyzer = analyzer + analyzers_timeavrg
        # Annual timeseries per age groups
        if 'annual' in exp.analyzer_list:
            analyzer = analyzer + annual_analyzers
        # Monthly timeseries per age groups
        if 'monthly' in exp.analyzer_list:
            analyzer = analyzer + monthly_analyzers
        # 5 day timeseries per age groups
        if '5day' in exp.analyzer_list or 'cc_step' in exp.analyzer_list:
            ccstep = 'cc_step' in exp.intervention_list
            analyzer = analyzer + [FiveDayAgebinAnalyzer(expt_name=exp_name,
                                                         start_year=start_year,
                                                         end_year=end_year,
                                                         sweep_variables=exp_tags,
                                                         working_dir=wdir,
                                                         burnin=burnin,
                                                         cc=ccstep)]
        ## Daily timeseries per age groups
        if 'daily' in exp.analyzer_list:
            analyzer = analyzer + daily_analyzers

        manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=analyzer,
                                 partial_analyze_ok=True)
        manager.analyze()
