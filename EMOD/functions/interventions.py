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
