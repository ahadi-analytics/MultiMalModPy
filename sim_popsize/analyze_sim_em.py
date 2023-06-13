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


class BenchmarkAnalyzer(IAnalyzer):

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
        df = df.groupby(self.sweep_variables + ['age'])[['nUncomp_annualized', 'nSevere_annualized', 'nHost']].agg(
            np.mean).reset_index()
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
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'annual_transmission_report.csv'))
            eirdf = eirdf.groupby(self.sweep_variables)[['Annual EIR']].agg(np.mean).reset_index()
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})

            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables)
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables)
            cdf = cdf.rename(
                columns={"x_Temporary_Larval_Habitat": "eir"})  # technicall wrong and lhs, but for consistency
            cdf['eirinput'] = "x_Temporary_Larval_Habitat"
        else:
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables)
            cdf = cdf.rename(columns={"EIR_scale_factor": "eir"})
            cdf['inputEIR'] = cdf['eir'] # to align with OM
            cdf['simulatedEIR'] = cdf['eir'] # to align with OM columnsf

        cdf = cdf.rename(columns={"Run_Number": "seed",
                                  "cm_clinical_U5": "access",
                                  "nUncomp": "clinical_incidence",
                                  "nSevere": "severe_incidence"})
        cdf['mortality'] = ''
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}')
        cdf.to_csv((os.path.join(self.working_dir, f'EMOD_benchmark.csv')), index=False)


class BenchmarkAnalyzer_yr(IAnalyzer):

    def __init__(self, expt_name, sweep_variables=None, working_dir='./', start_year=1920,
                 end_year=2020, burnin=None):

        super(BenchmarkAnalyzer_yr, self).__init__(working_dir=working_dir,
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
        df_pfpr2to10 = df.groupby(self.sweep_variables+['year'])[['prevalence_2to10']].agg(np.mean).reset_index()

        ## Aggregate years
        df = df.groupby(self.sweep_variables + ['age', 'year'])[
            ['nUncomp_annualized', 'nSevere_annualized', 'nHost']].agg(np.mean).reset_index()
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
                adf = adf.groupby(self.sweep_variables + ['year'])[['nUncomp', 'nSevere', 'nHost']].agg(
                    np.sum).reset_index()
                adf['nUncomp'] = adf['nUncomp'] / (adf['nHost'])  # (events per person per year)
                adf['nSevere'] = adf['nSevere'] / (adf['nHost'])  # (events per person per year)
                adf['age_group'] = ageCond_labels
                cdf = pd.concat([cdf, adf])

        if "x_Temporary_Larval_Habitat" in self.sweep_variables:
            time.sleep(5)
            eirdf = pd.read_csv(os.path.join(self.working_dir, 'annual_transmission_report.csv'))
            eirdf = eirdf.groupby(self.sweep_variables + ['year'])[['Annual EIR']].agg(np.mean).reset_index()
            eirdf = eirdf.rename(columns={"Annual EIR": "simulatedEIR"})

            cdf = pd.merge(left=cdf, right=eirdf, on=self.sweep_variables + ['year'])
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables + ['year'])
            cdf = cdf.rename(
                columns={"x_Temporary_Larval_Habitat": "eir"})  # technicall wrong and lhs, but for consistency
            cdf['eirinput'] = "x_Temporary_Larval_Habitat"
        else:
            cdf = pd.merge(left=cdf, right=df_pfpr2to10, on=self.sweep_variables + ['year'])
            cdf = cdf.rename(columns={"EIR_scale_factor": "eir"})
            cdf['inputEIR'] = cdf['eir'] # to align with OM
            cdf['simulatedEIR'] = cdf['eir'] # to align with OM columns

        cdf = cdf.rename(columns={"Run_Number": "seed",
                                  "cm_clinical_U5": "access",
                                  "nUncomp": "clinical_incidence",
                                  "nSevere": "severe_incidence"})
        cdf['mortality'] = ''
        print(f'\nSaving outputs to: {os.path.join(self.working_dir)}')
        cdf.to_csv((os.path.join(self.working_dir, f'EMOD_benchmark_yr.csv')), index=False)


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

    exp_tags = ['Run_Number', eirchannel, 'seasonality', 'cm_clinical_U5', 'x_Base_Population']  # ,'seasonality'
    start_year = exp.sim_start_year
    end_year = exp.end_year - 1
    monitoring_start = end_year - exp.monitoring_years
    burnin = None  # exp.burnin  ## Years burnin
    testmode = exp.testmode

    ## FIXME best location of output files
    wdir = os.path.join(exp.sim_out_dir, 'em')

    with Platform('SLURM_LOCAL', job_directory=os.path.join(manifest.job_directory, exp.SUITEname)) as platform:

        analyzer = [AnnualAgebinPfPRAnalyzer(expt_name=exp_name,
                                             sweep_variables=exp_tags,
                                             working_dir=wdir,
                                             start_year=start_year,
                                             end_year=end_year,
                                             burnin=burnin),
                    BenchmarkAnalyzer(expt_name=exp_name,
                                      sweep_variables=exp_tags,
                                      working_dir=wdir,
                                      start_year=start_year,
                                      end_year=end_year,
                                      burnin=burnin),
                    BenchmarkAnalyzer_yr(expt_name=exp_name,
                                         sweep_variables=exp_tags,
                                         working_dir=wdir,
                                         start_year=start_year,
                                         end_year=end_year,
                                         burnin=burnin)]

        manager = AnalyzeManager(configuration={}, ids=[(exp_id, ItemType.EXPERIMENT)], analyzers=analyzer,
                                 partial_analyze_ok=True)
        manager.analyze()

        if testmode:
            sample_plot_yr(wdir, exp_tags)
