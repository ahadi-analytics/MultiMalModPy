from emodpy_malaria.interventions.treatment_seeking import add_treatment_seeking
from emodpy_malaria.interventions.scale_larval_habitats import add_scale_larval_habitats
import pandas as pd
#from emodpy_malaria.interventions.drug_campaign import add_drug_campaign

def treatment_camp_simple(camp, cm_start, cm_clinical, cm_severe):
    """
    This function helps us establish treatment seeking behavior in an EMOD simulation.

    Parameters:
    - camp: Campaign object from EMOD.
    - cm_start: Day when the treatment campaign starts.
    - cm_clinical: Clinical case coverage (float).
    - cm_severe: Severe case coverage (float).

    Returns:
    A dictionary containing the start day of the treatment campaign, clinical case coverage, and severe case coverage.
    """
    cm_clinical = float(cm_clinical)
    cm_severe = float(cm_severe)
        
    if cm_clinical * 1.15 > cm_severe:
        cm_severe = min(cm_clinical * 1.15, 1)
    if cm_clinical == 0:
        cm_severe = 0

    add_treatment_seeking(camp, start_day=cm_start, drug=['Artemether', 'Lumefantrine'],
                             targets=[
                                 {'trigger': 'NewClinicalCase', 'coverage': cm_clinical, 'agemin': 0, 'agemax': 115,
                                  'rate': 0.3}],
                             broadcast_event_name="Received_Treatment")

    add_treatment_seeking(camp, start_day=cm_start, drug=['Artemether', 'Lumefantrine'],
                             targets=[
                                 {'trigger': 'NewSevereCase', 'coverage': cm_severe, 'agemin': 0, 'agemax': 115,
                                  'rate': 0.5}],
                             broadcast_event_name="Received_Severe_Treatment")
                             
    return {'cm_start': cm_start,'cm_clinical': cm_clinical, 'cm_severe': cm_severe}

def treatment_camp_granular(camp, cm_df):
    """
    Adds year-specific, age-specific, drug-specific treatment-seeking campaigns to EMOD,
    driven by a case management schedule (e.g. cm_2004_2025.csv, pre-filtered to one DS_Name).

    Parameters:
    - camp: Campaign object from EMOD.
    - cm_df: DataFrame with one row per year, columns:
        year, coverage_u5, coverage_o5, drugs_used, severe_cov, simday, duration

    Returns:
    A dictionary of scalar summary values describing the applied schedule.
    """
    drug_regimen_map = {
        'AL': ['Artemether', 'Lumefantrine'],
    }

    regimens_used = set()

    for _, row in cm_df.iterrows():
        regimen = str(row['drugs_used']).strip().upper()
        if regimen not in drug_regimen_map:
            raise ValueError(
                f"Unrecognized drug regimen code '{regimen}' for year {row['year']}. "
                f"Known regimens: {list(drug_regimen_map.keys())}")
        drug_list = drug_regimen_map[regimen]
        regimens_used.add(regimen)

        start_day = int(row['simday'])
        duration = int(row['duration'])

        add_treatment_seeking(camp, start_day=start_day, drug=drug_list,
                               targets=[
                                   {'trigger': 'NewClinicalCase', 'coverage': float(row['coverage_u5']),
                                    'agemin': 0, 'agemax': 5, 'rate': 0.3},
                                   {'trigger': 'NewClinicalCase', 'coverage': float(row['coverage_o5']),
                                    'agemin': 5, 'agemax': 115, 'rate': 0.3},
                               ],
                               duration=duration,
                               broadcast_event_name="Received_Treatment")

        add_treatment_seeking(camp, start_day=start_day, drug=drug_list,
                               targets=[
                                   {'trigger': 'NewSevereCase', 'coverage': float(row['severe_cov']),
                                    'agemin': 0, 'agemax': 115, 'rate': 0.5},
                               ],
                               duration=duration,
                               broadcast_event_name="Received_Severe_Treatment")

    return {
        'cm_start_year': int(cm_df['year'].min()),
        'cm_end_year': int(cm_df['year'].max()),
        'cm_n_years': int(len(cm_df)),
        'cm_drugs_used': '-'.join(sorted(regimens_used)),
    }

def load_cm_schedule(csv_path, ds_name):
    """
    Reads a case management schedule CSV and filters to one district.

    Parameters:
    - csv_path: full path to the case management CSV (e.g. cm_2004_2025.csv).
    - ds_name: district/site name to filter to (single-node scope).

    Returns:
    A DataFrame with one row per year for the specified district, sorted by year.
    """
    df = pd.read_csv(csv_path)
    df = df[df['DS_Name'] == ds_name].sort_values('year').reset_index(drop=True)
    if df.empty:
        raise ValueError(f"No case management rows found for DS_Name='{ds_name}' in {csv_path}")
    return df

def carrying_capacity(camp, row):
    cc_factor_df = pd.DataFrame({'CONSTANT': [row.cc_factor_EMOD]})
    add_scale_larval_habitats(camp, df=cc_factor_df,
                                  start_day=row.cc_timestep_EMOD,
                                  repetitions=1)
    return camp

# SMC currently not supported
# def smc_campaign(camp, row, start_array):
#     """
#     This function helps us establish an SMC regimen within a EMOD simulation.
#
#     Parameters:
#     - camp: Campaign object from EMOD.
#     - row: row refers to the specific simulation in the scen_df, so we accuratley input the correct
#       smc coverage (smc coverage is simulation dependent).
#     - start_array: An array containing start days of SMC campaign rounds.
#
#     #Note, additional parameters might be added to SMC in future , i.e. repetitions or target group
#     #Right now we are hard coding that SMC occurs 4 times within a year, 28 days apart,
#     #In children 6 months to 5 years old.
#
#     Returns:
#     A dictionary containing information about the SMC campaign, including the start days of rounds and coverage.
#     """
#     add_drug_campaign(camp, campaign_type="SMC", start_days=start_array,
#                       drug_code="SPAQ", repetitions=4,
#                       tsteps_btwn_repetitions=28,
#                       coverage=float(row.smc_coverage),
#                       target_group={'agemin': 0.25, 'agemax': 5},
#                       receiving_drugs_event_name="Received_SMC")
#     start_arrays = '; '.join([str(x) for x in start_array])
#     return {'smc_start_emod': start_arrays, 'smc_coverage': row.smc_coverage}


def carrying_capacity(camp, row):
    cc_factor_df = pd.DataFrame({'CONSTANT': [row.cc_factor_EMOD]})
    add_scale_larval_habitats(camp, df=cc_factor_df,
                                  start_day=row.cc_timestep_EMOD,
                                  repetitions=1)
    return camp
