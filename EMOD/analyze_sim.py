import os
import argparse
import pickle
import datetime
import time
import pandas as pd
import numpy as np
import sys
from idmtools.entities import IAnalyzer
from idmtools.entities.simulation import Simulation

sys.path.append('../')
import manifest
from benchmark_plots import *
from EMOD.sample_plots import *

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
        "-i",
        "--exp_id",
        type=str,
        required=False, 
        help="Unique ID of simulation experiment, required for EMOD runs",
        default=None
    )
    return parser.parse_args()


class InsetChartAnalyzer(IAnalyzer):

    @classmethod
    def monthparser(self, x):
        if x == 0:
            return 12
        else:
            return datetime.datetime.strptime(str(x), '%j').month

    def __init__(self, expt_name, sweep_variables=None, channels=None, working_dir=".", start_year=2022, burnin=None):
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
        self.burnin = burnin

    def map(self, data, simulation: Simulation):
        simdata = pd.DataFrame({x: data[self.filenames[0]]['Channels'][x]['Data'] for x in self.inset_channels})
        simdata['Time'] = simdata.index
        simdata['Day'] = simdata['Time'] % 365
        simdata['Year'] = simdata['Time'].apply(lambda x: int(x / 365) + self.start_year)
        simdata['date'] = simdata.apply(
            lambda x: datetime.date(int(x['Year']), 1, 1) + datetime.timedelta(int(x['Day']) - 1), axis=1)

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

        if self.burnin is not None:
            selected = selected[selected['Year'] >= self.start_year + self.burnin]

        adf = pd.concat(selected).reset_index(drop=True)
        adf.to_csv(os.path.join(self.working_dir, 'All_Age_InsetChart.csv'), index=False)


class AnnualAgebinPfPRAnalyzer(IAnalyzer):

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, burnin=None):

        super(AnnualAgebinPfPRAnalyzer, self).__init__(working_dir=working_dir,
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
            reports = data[fname]['DataByTime']['Time Of Report'][:nyears]
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:nyears]

            for age in list(range(0, len(age_bins))):
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

                simdata = pd.DataFrame({'year': [x / 365 for x in reports],
                                        'pfpr': pfpr,
                                        'nInfect': new_infect,
                                        'nUncomp_annualized': clinical_cases,
                                        'nSevere_annualized': severe_cases,
                                        'nHost': pop})
                simdata['age'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

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

        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}')

        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]
        df = df.loc[df['age'] <= 100]

        df.to_csv((os.path.join(self.working_dir, f'PfPR_ClinicalIncidence_yr.csv')),
                  index=False)


class MonthlyAgebinPfPRAnalyzer(IAnalyzer):

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=2000,
                 end_year=2020, burnin=None):

        super(MonthlyAgebinPfPRAnalyzer, self).__init__(working_dir=working_dir,
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
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:12]

            for age in list(range(0, len(age_bins))):
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

                simdata = pd.DataFrame({'month': range(1, 13),
                                        'pfpr': pfpr,
                                        'nInfect': new_infect,
                                        'nUncomp_annualized': clinical_cases,
                                        'nSevere_annualized': severe_cases,
                                        'nHost': pop})
                simdata['year'] = year
                simdata['age'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

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

        print(f'\nSaving outputs to: {os.path.join(self.working_dir, self.expt_name)}')

        if self.burnin is not None:
            df = df[df['year'] >= self.start_year + self.burnin]
        df = df.loc[df['age'] <= 100]

        df.to_csv((os.path.join(self.working_dir, f'PfPR_ClinicalIncidence_mth.csv')),
                  index=False)

class TransmissionReport(IAnalyzer):

    @classmethod
    def monthparser(self, x):
        if x == 0:
            return 12
        else:
            return datetime.datetime.strptime(str(x), '%j').month

    def __init__(self, expt_name, channels=None, sweep_variables=None, working_dir='./', start_year=2010,
                 selected_year=None, daily_report=False, monthly_report=False, burnin=None):
        super(TransmissionReport, self).__init__(working_dir=working_dir,
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
            adf = selected[adf['year'] >= self.start_year + self.burnin]

        grp_channels = self.sweep_variables  # [x for x in self.sweep_variables if x != "Run_Number"] ## Keep runs
        adf = adf.groupby(['time', 'date', 'day', 'month', 'year'] + grp_channels)[self.channels].agg(
            np.mean).reset_index()
        if self.daily_report:
            adf.to_csv(os.path.join(self.working_dir, f'daily_transmission_report.csv'), index=False)

        sum_channels = ['Daily Bites per Human', 'Daily EIR', 'Rainfall']
        if self.monthly_report:
            df = adf.groupby(['year', 'month'] + grp_channels)[sum_channels].agg(np.sum).reset_index()
            df = df.rename(columns={'Daily Bites per Human': 'Monthly Bites per Human', 'Daily EIR': 'Monthly EIR'})
            df.to_csv(os.path.join(self.working_dir, f'monthly_transmission_report.csv'), index=False)

        df = adf.groupby(['year'] + grp_channels)[sum_channels].agg(np.sum).reset_index()
        df = df.rename(columns={'Daily Bites per Human': 'Annual Bites per Human', 'Daily EIR': 'Annual EIR'})
        df.to_csv(os.path.join(self.working_dir, f'annual_transmission_report.csv'), index=False)
        
class BenchmarkAnalyzer(IAnalyzer):

    def __init__(self, expt_name, sweep_variables=None,  working_dir='./', start_year=1920,
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
            reports = data[fname]['DataByTime']['Time Of Report'][:nyears]
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:nyears]

            for age in list(range(0, len(age_bins))):
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:nyears]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:nyears]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:nyears]
                pop = [x[age] for x in d]

                simdata = pd.DataFrame({'year': [x / 365 for x in reports],
                                        'nUncomp_annualized': clinical_cases,
                                        'nSevere_annualized': severe_cases,
                                        'nHost': pop})
                simdata['age'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

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
        df_pfpr2to10 = df.groupby(self.sweep_variables)[['prevalence_2to10']].agg(np.mean).reset_index()

        ## Aggregate years
        df = df.groupby(self.sweep_variables + ['age'])[['nUncomp_annualized', 'nSevere_annualized', 'nHost']].agg(np.mean).reset_index()
        df['nUncomp'] = df['nUncomp_annualized'] * df['nHost']  ## total cases
        df['nSevere'] = df['nSevere_annualized'] * df['nHost']  ## total cases


        cdf = pd.DataFrame()
        age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]
        for i in range(0, len(age_groups_on_plot)):
            ages = age_groups_on_plot[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.age >= ages[0]) & (df.age <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables)[['nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['nUncomp'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per year)
                adf['nSevere'] = adf['nSevere'] / (adf['nHost'])  # (events per person per year)
                adf['age_group'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        if "x_Temporary_Larval_Habitat" in self.sweep_variables:
            time.sleep(5) 
            eirdf = pd.read_csv(os.path.join(self.working_dir,'annual_transmission_report.csv'))
            eirdf = eirdf.groupby(self.sweep_variables)[['Annual EIR']].agg(np.mean).reset_index()
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})
            
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables)
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables)
            cdf = cdf.rename(columns={"x_Temporary_Larval_Habitat": "inputEIR"}) # technicall wrong and lhs, but for consistency
            cdf['eirinput'] = "x_Temporary_Larval_Habitat"
        else:
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables)
            cdf = cdf.rename(columns={"EIR_scale_factor": "inputEIR"})
            cdf['simulatedEIR'] = cdf['inputEIR']

        cdf = cdf.rename(columns={"Run_Number": "seed",
                                  "cm_clinical_U5": "access",
                                  "nUncomp": "clinical_incidence",
                                  "nSevere": "severe_incidence"})
        cdf['mortality'] = ''
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}')
        cdf.to_csv((os.path.join(self.working_dir, f'EMOD_benchmark.csv')), index=False)
        
        
class MonthlyBenchmarkAnalyzer(IAnalyzer):

    def __init__(self, expt_name, sweep_variables=None,  working_dir='./', start_year=1920,
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
        nyears = self.end_year - self.start_year + 1
        for year, fname in zip(range(self.start_year, self.end_year), self.filenames):

            age_bins = data[fname]['Metadata']['Age Bins']
            reports = data[fname]['DataByTime']['Time Of Report'][:12]
            pfpr2to10 = data[fname]['DataByTime']['PfPR_2to10'][:12]

            for age in list(range(0, len(age_bins))):
                d = data[fname]['DataByTimeAndAgeBins']['Annual Clinical Incidence by Age Bin'][:12]
                clinical_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Annual Severe Incidence by Age Bin'][:12]
                severe_cases = [x[age] for x in d]
                d = data[fname]['DataByTimeAndAgeBins']['Average Population by Age Bin'][:12]
                pop = [x[age] for x in d]

                simdata = pd.DataFrame({'month': range(1, 13),
                                        'nUncomp_annualized': clinical_cases,
                                        'nSevere_annualized': severe_cases,
                                        'nHost': pop})
                simdata['year'] = year
                simdata['age'] = age_bins[age]
                simdata['prevalence_2to10'] = pfpr2to10
                adf = pd.concat([adf, simdata])

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
        df_pfpr2to10 = df.groupby(self.sweep_variables + ['month'])[['prevalence_2to10']].agg(np.mean).reset_index()
        
        ## Aggregate years
        df = df.groupby(self.sweep_variables + ['age','month'])[['nUncomp_annualized', 'nSevere_annualized', 'nHost']].agg(np.mean).reset_index()
        df['nUncomp'] = df['nUncomp_annualized'] * df['nHost']  ## total cases
        df['nSevere'] = df['nSevere_annualized'] * df['nHost']  ## total cases


        cdf = pd.DataFrame()
        age_groups_on_plot = [[0, 5], [5, 10], [10, 15], [15, 20]]
        for i in range(0, len(age_groups_on_plot)):
            ages = age_groups_on_plot[i]
            ageCond_labels = f'{str(ages[0])}-{str(ages[1])}'
            adf = df[(df.age >= ages[0]) & (df.age <= ages[1])]
            if adf.empty:
                pass
            else:
                adf = adf.groupby(self.sweep_variables + ['month'])[['nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['nUncomp'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per year)
                adf['nSevere'] = adf['nSevere'] / (adf['nHost'])  # (events per person per year)
                adf['age_group'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        if "x_Temporary_Larval_Habitat" in self.sweep_variables:
            time.sleep(5) 
            eirdf = pd.read_csv(os.path.join(self.working_dir,'monthly_transmission_report.csv'))
            eirdf = eirdf.groupby(self.sweep_variables+ ['month'])[['Monthly EIR']].agg(np.sum).reset_index()
            eirdf = eirdf.rename(columns={"Monthly EIR": "simulatedEIR"})
            
            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables+ ['month'])
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables+ ['month'])
            cdf = cdf.rename(columns={"x_Temporary_Larval_Habitat": "inputEIR"}) # technicall wrong and lhs, but for consistency
            cdf['eirinput'] = "x_Temporary_Larval_Habitat"
        else:
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables+ ['month'])
            cdf = cdf.rename(columns={"EIR_scale_factor": "inputEIR"})
            cdf['simulatedEIR'] = ''

        cdf = cdf.rename(columns={"Run_Number": "seed",
                                  "cm_clinical_U5": "access",
                                  "nUncomp": "clinical_incidence",
                                  "nSevere": "severe_incidence"})
        cdf['mortality'] = ''
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}')
        cdf.to_csv((os.path.join(self.working_dir, f'EMOD_benchmark_mth.csv')), index=False)
        
              
if __name__ == "__main__":

    from idmtools.analysis.analyze_manager import AnalyzeManager
    from idmtools.core import ItemType
    from idmtools.core.platform_factory import Platform

    args = parse_args()
    job_directory = args.directory
    exp_id = args.exp_id

    file = open(os.path.join(job_directory, "exp.obj"), "rb")
    exp = pickle.load(file)

    exp_name = exp.exp_name
    # exp_tags =  exp.sweeps ## to do
    if exp.entomology_mode == 'dynamic':
        eirchannel = "x_Temporary_Larval_Habitat"
    else:
        eirchannel = "EIR_scale_factor"

    exp_tags = ['Run_Number',eirchannel, 'cm_clinical_U5'] #,'seasonality'
    start_year = exp.sim_start_year
    end_year = exp.end_year - 1
    monitoring_start = end_year - exp.monitoring_years
    burnin = None  # exp.burnin  ## Years burnin
    testmode = exp.testmode

    channels_inset_chart = ['Statistical Population', 'Births', 'Disease Deaths',
                            'New Infections', 'Newly Symptomatic', 'New Clinical Cases', 'New Severe Cases',
                            'Fever Prevalence', 'True Prevalence', 'PCR Gametocyte Prevalence',
                            'PCR Parasite Prevalence', 'Blood Smear Parasite Prevalence', 'PfHRP2 Prevalence',
                            'Infectious Vectors', 'Daily EIR']

    ## FIXME best location of output files    
    wdir = os.path.join(exp.sim_out_dir, 'em')

    with Platform('SLURM_LOCAL', job_directory=manifest.job_directory) as platform:

        all_age_analyzer = [InsetChartAnalyzer(expt_name=exp_name,
                                               channels=channels_inset_chart,
                                               sweep_variables=exp_tags,
                                               start_year=start_year,
                                               burnin=burnin,
                                               working_dir=wdir)]
                            
        eir_analyzer = [TransmissionReport(expt_name=exp_name,
                                               sweep_variables=exp_tags,
                                               start_year=start_year,
                                               monthly_report = True,
                                               burnin=burnin,
                                               working_dir=wdir)]
                            
        annual_analyzers = [AnnualAgebinPfPRAnalyzer(expt_name=exp_name,
                                                     sweep_variables=exp_tags,
                                                     working_dir=wdir,
                                                     start_year=start_year,
                                                     end_year=end_year,
                                                     burnin=burnin)]

        monthly_analyzers= [MonthlyAgebinPfPRAnalyzer(expt_name=exp_name,
                                                       start_year=start_year,
                                                       end_year=end_year,
                                                       sweep_variables=exp_tags,
                                                       working_dir=wdir,
                                                       burnin=burnin)]

        analyzers_benchmark = [BenchmarkAnalyzer(expt_name=exp_name,
                                                     sweep_variables=exp_tags,
                                                     working_dir=wdir,
                                                     start_year=start_year,
                                                     end_year=end_year,
                                                     burnin=burnin),
                                MonthlyBenchmarkAnalyzer(expt_name=exp_name,
                                                     sweep_variables=exp_tags,
                                                     working_dir=wdir,
                                                     start_year=start_year,
                                                     end_year=end_year,
                                                     burnin=burnin)]
                                                     
        analyzer = all_age_analyzer + annual_analyzers + monthly_analyzers
        if exp.entomology_mode == 'dynamic':
            analyzer = analyzer + eir_analyzer
            
        analyzer =  analyzers_benchmark + analyzer
        manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=analyzer,
                                 partial_analyze_ok=True)
        manager.analyze()

        if testmode:
            all_age_sample_plot(wdir, exp_tags, channels_inset_chart)
            sample_plot_yr(wdir, exp_tags)
            sample_plot_mth(wdir, exp_tags)
            eir_to_prevalence2to10(wdir= exp.sim_out_dir, emodom=['EMOD'], sweepvar ='access')
            
            