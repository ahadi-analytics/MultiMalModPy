import os
import argparse
import pickle
import datetime
import pandas as pd
import numpy as np
from idmtools.entities import IAnalyzer
from idmtools.entities.simulation import Simulation
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


class InsetChartAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing inset chart report output specific to EMOD.
    Parameters:
    - expt_name (str): Name of the experiment.
    - sweep_variables (list): List of sweep variables. Defaults to None.
    - channels (list): List of inset channels. Defaults to None.
    - daily (bool): Flag indicating whether the data is daily. Defaults to False.
    - working_dir (str): Working directory for the analysis. Defaults to "./".
    - start_year (int): Start year of the simulation. Defaults to 2022.
    - burnin (None or int): Number of burn-in years to remove from results data. Defaults to None.
    """

    @classmethod
    def monthparser(self, x):
        if x == 0:
            return 12
        else:
            return datetime.datetime.strptime(str(x), '%j').month

    def __init__(self, expt_name, sweep_variables=None, channels=None, daily=False, working_dir=".", start_year=2022,
                 burnin=None):
        super(InsetChartAnalyzer, self).__init__(working_dir=working_dir, filenames=["output/InsetChart.json"])
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
        self.burnin = burnin

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
            adf.to_csv(os.path.join(self.working_dir, 'em', 'All_Age_InsetChart_daily.csv'), index=False)

        if self.burnin is not None:
            adf = adf[adf['Year'] >= self.start_year + self.burnin]

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

        # Save the processed DataFrame to a CSV file named 'All_Age_Outputs.csv'
        adf.to_csv(os.path.join(self.working_dir, 'em', 'All_Age_Outputs.csv'), index=False)


class AnnualAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing summary report output specific to EMOD.
    It saves a dataframe per year from annual summary reports for each agebin specified in the report.
    Parameters:
    - expt_name (str): Name of the experiment.
    - sweep_variables (list): List of sweep variables. Defaults to None.
    - working_dir (str): Working directory for the analysis. Defaults to "./".
    - start_year (int): Start year of the simulation. Defaults to 2022.
    - end_year (int): End year of the simulation. Defaults to 2022.
    - burnin (None or int): Number of burn-in years to remove from results data. Defaults to None.
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, burnin=None):

        super(AnnualAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                   filenames=[
                                                       f"output/MalariaSummaryReport_Annual_{start_year}to{end_year}.json"])
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.burnin = burnin

    def map(self, data, simulation: Simulation):

        adf = pd.DataFrame()
        nyears = self.end_year - self.start_year + 1

        # Loop over summary reports
        for fname in self.filenames:

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:nyears]

            for age in list(range(0, len(age_bins))):
                # Extract data per agebin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin'][:nyears]
                pfpr = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['New Infections by Age Bin'][:nyears]
                new_infect = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:nyears]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:nyears]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:nyears]
                pop = [x[age] for x in d]

                # Combine extracted data to dataframe
                simdata = pd.DataFrame({'year': range(self.start_year, self.end_year + 1),
                                        'prevalence': pfpr,
                                        'nInfect': new_infect,
                                        'clinical_incidence': clinical_cases,  # per person per annum
                                        'severe_incidence': severe_cases,  # per person per annum
                                        'nHost': pop})
                simdata['agebin'] = age_bins[age]
                simdata['nUncomp'] = simdata['clinical_incidence'] * simdata[
                    'nHost']  # per total population per year in that age group
                simdata['nSevere'] = simdata['severe_incidence'] * simdata[
                    'nHost']  # per total population per year in that age group
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

        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/em')

        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]

        # Age groups
        age_bins = [int(x) if x == int(x) else x for x in df['agebin'].unique()]
        age_group_labels = [str(age_bins[i - 1]) + "-" + str(age_bins[i]) for i in range(1, len(age_bins))]
        age_group_labels = [str(0) + "-" + str(age_bins[0])] + age_group_labels
        age_df = pd.DataFrame({'agebin': age_bins, 'ageGroup': age_group_labels})
        df = df.merge(age_df, on='agebin', how='inner')

        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        df = df.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['year'])[['Annual EIR']].agg(np.mean).reset_index()
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})
            df = pd.merge(left=df, right=eirdf, on=self.sweep_variables + ['year'])
            # df['eir'] = [round(x, 1) if x < 1 else round(x, 0) for x in df['simulatedEIR']]
        else:
            df['simulatedEIR'] = df['eir']

            #  Reorder the DataFrame columns , by specified first columns to appear first
        df = df.rename(columns={'Run_Number': 'seed'})
        first_columns = ['seed', 'year', 'agebin', 'ageGroup', 'prevalence', 'nInfect', 'nUncomp', 'nSevere']
        df = df[first_columns + df.drop(columns=first_columns).columns.tolist()]

        # Save the processed DataFrame to a CSV file named 'PfPR_ClinicalIncidence_yr.csv'
        df.to_csv((os.path.join(self.working_dir, 'em', 'PfPR_ClinicalIncidence_yr.csv')), index=False)


class MonthlyAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing summary report output specific to EMOD.
    It saves a dataframe per month and yeat from monthly summary reports for each agebin specified in the report.
    Parameters:
    - expt_name (str): Name of the experiment.
    - sweep_variables (list): List of sweep variables. Defaults to None.
    - working_dir (str): Working directory for the analysis. Defaults to "./".
    - start_year (int): Start year of the simulation. Defaults to 2022.
    - end_year (int): End year of the simulation. Defaults to 2022.
    - burnin (None or int): Number of burn-in years to remove from results data. Defaults to None.
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=2000,
                 end_year=2020, burnin=None):

        super(MonthlyAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                    filenames=[f"output/MalariaSummaryReport_Monthly_{x}.json"
                                                               for x in range(start_year, end_year)]
                                                    )
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.burnin = burnin

    def map(self, data, simulation: Simulation):

        adf = pd.DataFrame()
        # Loop over summary reports (separate ones for each year)
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:12]

            for age in list(range(0, len(age_bins))):
                # Extract data per agebin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin'][:12]
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

        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return
        df = pd.concat(selected).reset_index(drop=True)

        print(f'\nSaving outputs to: {os.path.join(self.working_dir, "em")}')

        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]

        # Age group labels
        age_bins = [int(x) if x == int(x) else x for x in df['agebin'].unique()]
        age_group_labels = [str(age_bins[i - 1]) + "-" + str(age_bins[i]) for i in range(1, len(age_bins))]
        age_group_labels = [str(0) + "-" + str(age_bins[0])] + age_group_labels
        age_df = pd.DataFrame({'agebin': age_bins, 'ageGroup': age_group_labels})
        df = df.merge(age_df, on='agebin', how='inner')

        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        df = df.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['year'])[['Annual EIR']].agg(np.mean).reset_index()
            df = pd.merge(left=df, right=eirdf, on=self.sweep_variables + ['year'])

            eirdf_mth = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_mth.csv'))
            eirdf_mth = eirdf_mth.groupby(self.sweep_variables + ['year', 'month'])[['Monthly EIR']].agg(
                np.mean).reset_index()
            df = pd.merge(left=df, right=eirdf_mth, on=self.sweep_variables + ['year', 'month'])

            df = df.rename(columns={"Monthly EIR": "simulatedEIR"})
            # df['eir'] = [round(x, 1) if x < 1 else round(x, 0) for x in df['Annual EIR']]
        else:
            df['simulatedEIR'] = ''

        #  Reorder the DataFrame columns , by specified first columns to appear first
        df = df.rename(columns={'Run_Number': 'seed'})
        df['day'] = 1
        df['date'] = pd.to_datetime(df[['year', 'month', 'day']])
        first_columns = ['seed', 'date', 'year', 'month', 'agebin', 'ageGroup', 'prevalence', 'nInfect', 'nUncomp',
                         'nSevere']
        df = df[first_columns + df.drop(columns=first_columns).columns.tolist()]

        df.to_csv((os.path.join(self.working_dir, 'em', 'PfPR_ClinicalIncidence_mth.csv')), index=False)


class DailyAgebinAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer for analyzing summary report output specific to EMOD.
    It saves a dataframe per month and yeat from monthly summary reports for each agebin specified in the report.
    Parameters:
    - expt_name (str): Name of the experiment.
    - sweep_variables (list): List of sweep variables. Defaults to None.
    - working_dir (str): Working directory for the analysis. Defaults to "./".
    - start_year (int): Start year of the simulation. Defaults to 2022.
    - end_year (int): End year of the simulation. Defaults to 2022.
    - burnin (None or int): Number of burn-in years to remove from results data. Defaults to None.
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=2000,
                 end_year=2020, burnin=None):

        super(DailyAgebinAnalyzer, self).__init__(working_dir=working_dir,
                                                    filenames=[f"output/MalariaSummaryReport_Daily_{x}.json"
                                                               for x in range(start_year, end_year)]
                                                    )
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.burnin = burnin

    def map(self, data, simulation: Simulation):

        adf = pd.DataFrame()
        # Loop over summary reports (separate ones for each year)
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10']

            for age in list(range(0, len(age_bins))):
                # Extract data per agebin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin']
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
                simdata = pd.DataFrame({'day': range(1, 365),
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

        print(f'\nSaving outputs to: {os.path.join(self.working_dir, "em")}')

        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]

        # Age group labels
        age_bins = [int(x) if x == int(x) else x for x in df['agebin'].unique()]
        age_group_labels = [str(age_bins[i - 1]) + "-" + str(age_bins[i]) for i in range(1, len(age_bins))]
        age_group_labels = [str(0) + "-" + str(age_bins[0])] + age_group_labels
        age_df = pd.DataFrame({'agebin': age_bins, 'ageGroup': age_group_labels})
        df = df.merge(age_df, on='agebin', how='inner')

        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        scen_df = scen_df.drop(['eir_malsim', 'eir_om', 'eir_scalar_timestep_5day', 'eir_scalar_timestep_daily', 'eir_scalar_emod','eir_scalar_om', 'eir_scalar_malsim'], axis=1)  ## Other model specific, entomology_mode  not applicable
        df = df.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_daily.csv'))
            df = pd.merge(left=df, right=eirdf, on=self.sweep_variables + ['day','year', 'eir'])
            # df['eir'] = [round(x, 1) if x < 1 else round(x, 0) for x in df['Annual EIR']]
        else:
            df['simulatedEIR'] = ''

        #  Reorder the DataFrame columns , by specified first columns to appear first
        df = df.rename(columns={'Run_Number': 'seed'})
        df.to_csv((os.path.join(self.working_dir, 'em', 'PfPR_ClinicalIncidence_daily.csv')), index=False)


class InputEIRAnalyzer(IAnalyzer):
    """
      A class inherited from idmtools IAnalyzer for generating results dataframe on transmission outcome metrics.
     Parameters:
     - expt_name (str): Name of the experiment.
     - channels (list): List of channels. Defaults to None.
     - sweep_variables (list): List of sweep variables. Defaults to None.
     - working_dir (str): Working directory for the analysis. Defaults to "./".
     - start_year (int): Start year of the analysis. Defaults to 2010.
     - selected_year (None or int): Year to be extracted from the simulation results. Defaults to None (keep all).
     - daily_report (bool): Flag indicating whether to save results dataframe with daily transmission data. Defaults to False.
     - monthly_report (bool): Flag indicating whether to save results dataframe with monthly transmission data. Defaults to False.
     - burnin (None or int): Number of burn-in years to drop from simulation results. Defaults to None (keep all).
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
        self.channels = channels or ['Daily Bites per Human', 'Daily EIR', 'Rainfall']
        self.start_year = start_year
        self.selected_year = selected_year
        self.daily_report = daily_report
        self.monthly_report = monthly_report
        self.expt_name = expt_name
        self.burnin = burnin

    def map(self, data, simulation):
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

        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return

        adf = pd.concat(selected).reset_index(drop=True)

        if self.burnin is not None:
            adf = adf[adf['year'] >= self.start_year + self.burnin]

        # Aggregate data and save for specified time intervals (daily, monthly, annually)
        grp_channels = self.sweep_variables  # [x for x in self.sweep_variables if x != "Run_Number"] ## Keep runs
        adf = adf.groupby(['time', 'date', 'day', 'month', 'year'] + grp_channels)[self.channels].agg(
            np.mean).reset_index()

        # Add Larval Habitat Multipliers and sweep variables to EIR dataframe
        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        adf = adf.merge(scen_df, on='scen_id', how='inner')
        grp_channels = list(set(grp_channels + list(scen_df.columns)))

        if self.daily_report:
            df = adf[['scen_id','Run_Number','time','day','month','year','eir', 'Daily EIR', 'eir_scalar_timestep_daily', 'eir_scalar_emod']]
            df = df.rename({'Daily EIR': 'simulatedEIR','time':'timestep', 'eir_scalar_timestep_daily':'eir_scalar_timestep','eir_scalar_emod':'eir_scalar'}, axis=1) 
            df['day'] = df['day']+1
            df['timestep'] = df['timestep']+1
            df.to_csv(os.path.join(self.working_dir, 'em', 'EIR_daily.csv'), index=False)
        
        sum_channels = ['Daily Bites per Human', 'Daily EIR', 'Rainfall']

        # Monthly aggregation - keep months and years
        if self.monthly_report:
            df = adf.groupby(['year', 'month'] + grp_channels)[sum_channels].agg(np.sum).reset_index()
            df = df.rename(columns={'Daily Bites per Human': 'Monthly Bites per Human', 'Daily EIR': 'Monthly EIR'})
            df.to_csv(os.path.join(self.working_dir, 'em', 'EIR_mth.csv'), index=False)

        # Yearly aggregation - keep years
        df = adf.groupby(['year'] + grp_channels)[sum_channels].agg(np.sum).reset_index()
        df = df.rename(columns={'Daily Bites per Human': 'Annual Bites per Human', 'Daily EIR': 'Annual EIR'})
        df.to_csv(os.path.join(self.working_dir, 'em', 'EIR_yr.csv'), index=False)

        # Mean over monitoring period
        nyears = len(adf['year'].unique())
        df = adf.groupby(grp_channels)[sum_channels].agg(np.sum).reset_index()
        df['Daily EIR'] = df['Daily EIR'] / nyears
        df['Daily Bites per Human'] = df['Daily Bites per Human'] / nyears
        df = df.rename(columns={'Daily Bites per Human': 'Annual Bites per Human', 'Daily EIR': 'Annual EIR'})
        df.to_csv(os.path.join(self.working_dir, 'em', 'EIR.csv'), index=False)

class BenchmarkAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer and modified for analyzing  EMOD summary reports to generate
    and save a results dataframe in the standards of the "Benchmark" format - results aggregated across all surveys
    Parameters:
    - expt_name (str): Name of the experiment.
    - sweep_variables (list): List of sweep variables. Defaults to None.
    - working_dir (str): Working directory for the analysis. Defaults to './'.
    - start_year (int): Start year of the analysis. Defaults to 1920.
    - end_year (int): End year of the analysis. Defaults to 2020.
    - burnin (None or int): Number of burn-in iterations. Defaults to None.
    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, burnin=None):

        super(BenchmarkAnalyzer, self).__init__(working_dir=working_dir,
                                                filenames=[
                                                    f"output/MalariaSummaryReport_Annual_{start_year}to{end_year}.json"])
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.burnin = burnin

    def map(self, data, simulation: Simulation):

        adf = pd.DataFrame()
        nyears = self.end_year - self.start_year + 1
        for fname in self.filenames:

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:nyears]

            for age in list(range(0, len(age_bins))):
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin'][:nyears]
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

        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return

        df = pd.concat(selected).reset_index(drop=True)
        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]
        df_pfpr2to10 = df.groupby(self.sweep_variables)[['prevalence_2to10']].agg(np.mean).reset_index()

        ## Aggregate years
        df = df.groupby(self.sweep_variables + ['agebin'])[
            ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(
            np.mean).reset_index()
        df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
        df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
        df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

        cdf = pd.DataFrame()
        # Define standard age groups used in benchmarking default for plotting
        age_groups_on_plot = [[0,0.5],[0.5,1],[1,2],[2,5], [5, 10], [10, 15], [15, 20], [20,100], [0,5],[0,100]]

        # Loop over age groups to aggregate results data
        for i in range(0, len(age_groups_on_plot)):
            ages = age_groups_on_plot[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.agebin >= ages[0]) & (df.agebin <= ages[1])]
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
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables)[['Annual EIR']].agg(
                np.mean).reset_index()  # mean across monitoring years and runs
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables)
            # cdf['eir'] = [round(x, 1) if x < 1 else round(x, 0) for x in cdf['Annual EIR']]
        else:
            cdf['simulatedEIR'] = cdf['eir']
            cdf['inputEIR'] = cdf['eir']

        # Rename columns for alignment with OpenMalaria results
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['mortality'] = ''
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/em')

        # Save the processed DataFrame to a CSV file named 'Benchmark.csv'
        cdf.to_csv((os.path.join(self.working_dir, 'em', 'Benchmark.csv')), index=False)
        

class MonthlyBenchmarkAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer and modified for analyzing  EMOD summary reports to generate
    and save a results dataframe in the standards of the "Benchmark" format - results aggregated per month across years
    Parameters:
    - expt_name (str): Name of the experiment.
    - sweep_variables (list): List of sweep variables. Defaults to None.
    - working_dir (str): Working directory for the analysis. Defaults to './'.
    - start_year (int): Start year of the analysis. Defaults to 1920.
    - end_year (int): End year of the analysis. Defaults to 2020.
    - burnin (None or int): Number of burn-in iterations. Defaults to None.
    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, burnin=None):
        super(MonthlyBenchmarkAnalyzer, self).__init__(working_dir=working_dir,
                                                       filenames=[f"output/MalariaSummaryReport_Monthly_{x}.json"
                                                                  for x in range(start_year, end_year)]
                                                       )
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.burnin = burnin

    def map(self, data, simulation: Simulation):
        adf = pd.DataFrame()

        # Loop of years that have separate summary reports
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:12]

            for age in list(range(0, len(age_bins))):
                # Extract data for each age bin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin'][:12]
                pfpr = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:12]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:12]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:12]
                pop = [x[age] for x in d]

                # Create a DataFrame for the simulation data
                simdata = pd.DataFrame({'month': range(1, 13),
                                        'prevalence': pfpr,
                                        'clinical_incidence': clinical_cases,  # per person per per annum
                                        'severe_incidence': severe_cases,  # per person per annum
                                        'nHost': pop})
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
        df['year'] = df['year'] + self.start_year
        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]
        df_pfpr2to10 = df.groupby(self.sweep_variables + ['month'])[['prevalence_2to10']].agg(np.mean).reset_index()

        # Aggregate years
        df = df.groupby(self.sweep_variables + ['agebin', 'month'])[
            ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(np.mean).reset_index()
        df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections
        df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
        df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

        cdf = pd.DataFrame()

        # Define standard age groups used in benchmarking default for plotting
        age_groups_on_plot = [[0,0.5],[0.5,1],[1,2],[2,5], [5, 10], [10, 15], [15, 20], [20,100], [0,5],[0,100]]

        # Loop over the age groups to aggregate agebins to the defined groups
        for i in range(0, len(age_groups_on_plot)):
            ages = age_groups_on_plot[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.agebin >= ages[0]) & (df.agebin <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables + ['month'])[['nPatent', 'nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['prevalence'] = adf['nPatent'] / (adf['nHost'])
                adf['clinical_incidence'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per annum)
                adf['severe_incidence'] = adf['nSevere'] / (adf['nHost'])  # (events per person per annum)
                adf['ageGroup'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        scen_df = pd.read_csv(os.path.join(self.working_dir, 'scenarios.csv'))
        cdf = cdf.merge(scen_df, on='scen_id', how='inner')
        if scen_df.entomology_mode[0] == 'dynamic':
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_mth.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['month'])[['Monthly EIR']].agg(
                np.mean).reset_index()  # mean across years and runs per month
            eirdf = eirdf.rename(columns={"Monthly EIR": "simulatedEIR"})

            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables + ['month'])
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables + ['month'])

            eirdf = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables)[['Annual EIR']].agg(
                np.mean).reset_index()  # mean across years and runs
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables)
            # cdf['eir'] = [round(x, 1) if x < 1 else round(x, 0) for x in cdf['Annual EIR']]
        else:
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables + ['month'])
            cdf['simulatedEIR'] = ''
            cdf['inputEIR'] = ''

        # Rename columns for alignment with OpenMalaria results
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['mortality'] = ''
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/em')

        # Save the processed DataFrame to a CSV file named 'Benchmark_mth.csv'
        cdf.to_csv((os.path.join(self.working_dir, 'em', 'Benchmark_mth.csv')), index=False)


class AnnualBenchmarkAnalyzer(IAnalyzer):
    """
    A class inherited from idmtools IAnalyzer and modified for analyzing  EMOD summary reports to generate
    and save a results dataframe in the standards of the "Benchmark" format - but keeping year separate
    Parameters:
    - expt_name (str): Name of the experiment.
    - sweep_variables (list): List of sweep variables. Defaults to None.
    - working_dir (str): Working directory for the analysis. Defaults to './'.
    - start_year (int): Start year of the analysis. Defaults to 1920.
    - end_year (int): End year of the analysis. Defaults to 2020.
    - burnin (None or int): Number of burn-in iterations. Defaults to None.
    Returns:
        None
    """

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, burnin=None):

        super(AnnualBenchmarkAnalyzer, self).__init__(working_dir=working_dir,
                                                      filenames=[
                                                          f"output/MalariaSummaryReport_Annual_{start_year}to{end_year}.json"])
        self.sweep_variables = sweep_variables or ["Run_Number"]
        self.expt_name = expt_name
        self.start_year = start_year
        self.end_year = end_year
        self.burnin = burnin

    def map(self, data, simulation: Simulation):

        adf = pd.DataFrame()
        nyears = self.end_year - self.start_year + 1
        for fname in self.filenames:

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:nyears]

            for age in list(range(0, len(age_bins))):
                # Extract data for each age bin
                d = data[fname]['DataByTimeAndAgeBins']['PfPR by Age Bin'][:nyears]
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

        selected = [data for sim, data in all_data.items()]
        if len(selected) == 0:
            print("\nWarning: No data have been returned... Exiting...")
            return

        df = pd.concat(selected).reset_index(drop=True)
        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]
        df_pfpr2to10 = df.groupby(self.sweep_variables + ['year'])[['prevalence_2to10']].agg(np.mean).reset_index()

        # Aggregate years
        df = df.groupby(self.sweep_variables + ['agebin', 'year'])[
            ['prevalence', 'clinical_incidence', 'severe_incidence', 'nHost']].agg(np.mean).reset_index()
        df['nPatent'] = df['prevalence'] * df['nHost']  ## total patent infections per annum
        df['nUncomp'] = df['clinical_incidence'] * df['nHost']  ## total cases per annum
        df['nSevere'] = df['severe_incidence'] * df['nHost']  ## total cases per annum

        cdf = pd.DataFrame()
        # Define age groups to aggregate, have U5 aggregated and disaggregated in dataframeto write out
        # [[0, 5]] + [[(age_groups[i - 1]), (age_groups[i])] for i in range(1, len(age_groups))]
        age_groups_on_plot = [[0,0.5],[0.5,1],[1,2],[2,5], [5, 10], [10, 15], [15, 20], [20,100], [0,5],[0,100]]

        # Loop over the age groups to aggregate agebins to the defined groups
        for i in range(0, len(age_groups_on_plot)):
            ages = age_groups_on_plot[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.agebin >= ages[0]) & (df.agebin <= ages[1])]
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
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'em', 'EIR_yr.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['year'])[['Annual EIR']].agg(np.mean).reset_index()
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables + ['year'])
            # cdf['eir'] = [round(x, 1) if x < 1 else round(x, 0) for x in cdf['Annual EIR']]
        else:
            cdf['simulatedEIR'] = cdf['eir']
            cdf['inputEIR'] = cdf['eir']

        # Rename columns for alignment with OpenMalaria results
        cdf = cdf.rename(columns={"Run_Number": "seed"})
        cdf['mortality'] = ''

        # Save the processed DataFrame to a CSV file named 'Benchmark_yr.csv'
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}/em')
        cdf.to_csv((os.path.join(self.working_dir, 'em', 'Benchmark_yr.csv')), index=False)


if __name__ == "__main__":
    # Load additional required modules
    from idmtools.analysis.analyze_manager import AnalyzeManager
    from idmtools.core import ItemType
    from idmtools.core.platform_factory import Platform

    # Parse command line arguments
    args = parse_args()
    job_directory = args.directory
    exp_id = args.exp_id
    #job_directory = 
    #exp_id = 

    # Load experiment object
    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)
    # Set location of output files
    wdir = exp.sim_out_dir
    create_sampleplots = False

    exp_name = exp.exp_name

    # Define tags and simulation experiment configurations
    exp_tags = ['scen_id', 'Run_Number']

    start_year = exp.sim_start_year_em
    end_year = exp.end_year
    monitoring_start = end_year - exp.monitoring_years

    if exp.emod_step == 'burnin':
        end_year = start_year + exp.burnin
        burnin = 0  ## Keep all years
    elif exp.emod_step == 'pickup':
        burnin = 0
    else:
        burnin = int(exp.burnin)  ## Years burnin to discard when running burnin+pickup together

    # Define which outcome metrics to process in inset_chart (all age per daily timestep)
    channels_inset_chart = ['Statistical Population', 'Births', 'Disease Deaths',
                            'New Infections', 'Newly Symptomatic', 'New Clinical Cases', 'New Severe Cases',
                            'Fever Prevalence', 'True Prevalence', 'PCR Gametocyte Prevalence',
                            'PCR Parasite Prevalence', 'Blood Smear Parasite Prevalence', 'PfHRP2 Prevalence',
                            'Infectious Vectors', 'Daily EIR']
    # Run analyzers
    with Platform('SLURM_LOCAL', job_directory=exp.suite_directory, mem_per_cpu=int(5000)) as platform:
        all_age_analyzer = [InsetChartAnalyzer(expt_name=exp_name,
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
        
        annual_analyzers = [AnnualAgebinAnalyzer(expt_name=exp_name,
                                                 sweep_variables=exp_tags,
                                                 working_dir=wdir,
                                                 start_year=start_year,
                                                 end_year=end_year - 1,
                                                 burnin=burnin)]

        monthly_analyzers = [MonthlyAgebinAnalyzer(expt_name=exp_name,
                                                   start_year=start_year,
                                                   end_year=end_year,
                                                   sweep_variables=exp_tags,
                                                   working_dir=wdir,
                                                   burnin=burnin)]
        daily_analyzers = [DailyAgebinAnalyzer(expt_name=exp_name,
                                                   start_year=start_year,
                                                   end_year=end_year,
                                                   sweep_variables=exp_tags,
                                                   working_dir=wdir,
                                                   burnin=burnin)]
        
        analyzers_benchmark = [BenchmarkAnalyzer(expt_name=exp_name,
                                                 sweep_variables=exp_tags,
                                                 working_dir=wdir,
                                                 start_year=start_year,
                                                 end_year=end_year - 1,
                                                 burnin=burnin),
                               AnnualBenchmarkAnalyzer(expt_name=exp_name,
                                                       sweep_variables=exp_tags,
                                                       working_dir=wdir,
                                                       start_year=start_year,
                                                       end_year=end_year - 1,
                                                       burnin=burnin),
                               MonthlyBenchmarkAnalyzer(expt_name=exp_name,
                                                        sweep_variables=exp_tags,
                                                        working_dir=wdir,
                                                        start_year=start_year,
                                                        end_year=end_year,
                                                        burnin=burnin)]

        if exp.entomology_mode == 'dynamic':
            manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=eir_analyzer, # we run eir_analyzers first to avoid any of the other analyzers running without this dependency completed.
                                 partial_analyze_ok=True)
            manager.analyze()
            analyzer = annual_analyzers
        
        if exp.emod_step != 'burnin':
            analyzer = analyzer + monthly_analyzers + analyzers_benchmark
            if 'cc_step' in exp.intervention_list: # for now if the intervention cc_step step is present, we do not want to run any of the other analyzers
                daily_eir_analyzer = [InputEIRAnalyzer(expt_name=exp_name,
                                         sweep_variables=exp_tags,
                                         start_year=start_year,
                                         daily_report=True,
                                         monthly_report=False,
                                         burnin=burnin,
                                         working_dir=wdir)]
                manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=daily_eir_analyzer,
                                 partial_analyze_ok=True)
                manager.analyze()
                
                analyzer = daily_analyzers
        
        manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=analyzer,
                                 partial_analyze_ok=True)
        manager.analyze()

    # Create sample plots if specified
    if create_sampleplots and 'cc_step' not in exp.intervention_list: #For daily we shouldn't request anything beyond the daily_EIR and daily_analyzers
        exp_tags = [tag for tag in exp_tags if tag != 'Run_Number'] + ['seed']
        channels_inset_chart = ['Statistical Population', 'Births', 'New Infections', 'Newly Symptomatic',
                                'New Clinical Cases', 'New Severe Cases',
                                'Fever Prevalence', 'True Prevalence', 'PCR Gametocyte Prevalence',
                                'PCR Parasite Prevalence', 'Blood Smear Parasite Prevalence', 'PfHRP2 Prevalence',
                                'Infectious Vectors', 'EIR']
        all_age_sample_plot(wdir=os.path.join(exp.sim_out_dir, 'em'), sweep_variables=exp_tags,
                            sample_channels=channels_inset_chart)
        sample_plot_yr(wdir=os.path.join(exp.sim_out_dir, 'em'), sweep_variables=exp_tags)

        if exp.emod_step != 'burnin':
            sample_plot_mth(wdir=os.path.join(exp.sim_out_dir, 'em'), sweep_variables=exp_tags)

            emodom = ['EMOD']
            sweepvar = 'eir'
            monthly_trends(wdir, emodom, channel='clinical_incidence', sweepvar=sweepvar)
            monthly_trends(wdir, emodom, channel='severe_incidence', sweepvar=sweepvar)
            monthly_trends(wdir, emodom, channel='prevalence', sweepvar=sweepvar)
            monthly_trends(wdir, emodom, channel='prevalence_2to10', sweepvar=sweepvar)
            monthly_trends(wdir, emodom=emodom, channel='simulatedEIR', sweepvar=sweepvar)

            channel_list = ['clinical_incidence', 'severe_incidence', 'prevalence', 'simulatedEIR',
                            'x_Temporary_Larval_Habitat']
            for channel in channel_list:
                monthly_timeseries(wdir=exp.sim_out_dir, emodom=emodom, channel=channel, sweepvar='emodom',
                                   facet_var='eir', agegrp='5-10')

            sweepvar = 'cm_clinical'
            prevalence2to10_to_incidence(wdir, emodom, channel='prevalence')
            prevalence2to10_to_incidence(wdir, emodom, channel='clinical_incidence')
            prevalence2to10_to_incidence(wdir, emodom, channel='severe_incidence')
            eir_to_outcome(wdir, emodom, sweepvar=sweepvar, eir_val='simulatedEIR')