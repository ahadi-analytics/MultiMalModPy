from emodpy_malaria.interventions.treatment_seeking import add_treatment_seeking
from emodpy_malaria.interventions.drug_campaign import add_drug_campaign

def treatment_camp_simple(camp, cm_start, cm_clinical, cm_severe):

    cm_clinical = float(cm_clinical)
    cm_severe = float(cm_severe)
        
    if cm_clinical * 1.15 > cm_severe:
        cm_severe = min(cm_clinical * 1.15, 1)
    if cm_clinical == 0:
        cm_severe = 0

    add_treatment_seeking(camp, start_day=cm_start, drug=['Artemether', 'Lumefantrine'],
                             targets=[
                                 {'trigger': 'NewClinicalCase', 'coverage': cm_clinical, 'agemin': 0, 'agemax': 115,
                                  'seek': 1, 'rate': 0.3}],
                             broadcast_event_name="Received_Treatment")

    add_treatment_seeking(camp, start_day=cm_start, drug=['Artemether', 'Lumefantrine'],
                             targets=[
                                 {'trigger': 'NewSevereCase', 'coverage': cm_severe, 'agemin': 0, 'agemax': 115,
                                  'seek': 1, 'rate': 0.5}],
                             broadcast_event_name="Received_Severe_Treatment")
                             
    return {'cm_start': cm_start,'cm_clinical': cm_clinical, 'cm_severe': cm_severe}

def treatment_camp(camp, cm_start, cm_clinical_U5, cm_clinical_adult=None, cm_severe=None):

   
    if cm_clinical_adult is None:
        cm_clinical_adult = cm_clinical_U5 * 0.75
    if cm_severe is None:
        cm_severe = min(cm_clinical_U5 * 1.15, 1)
        if cm_clinical_U5 == 0:
            cm_severe = 0

    add_treatment_seeking(camp, start_day=cm_start, drug=['Artemether', 'Lumefantrine'],
                             targets=[
                                 {'trigger': 'NewClinicalCase', 'coverage': cm_clinical_U5, 'agemin': 0, 'agemax': 5,
                                  'seek': 1, 'rate': 0.3},
                                 {'trigger': 'NewClinicalCase', 'coverage': cm_clinical_adult, 'agemin': 5,
                                  'agemax': 115,
                                  'seek': 1, 'rate': 0.3}],
                             broadcast_event_name="Received_Treatment")

    add_treatment_seeking(camp, start_day=cm_start, drug=['Artemether', 'Lumefantrine'],
                             targets=[
                                 {'trigger': 'NewSevereCase', 'coverage': cm_severe, 'agemin': 0, 'agemax': 115,
                                  'seek': 1, 'rate': 0.5}],
                             broadcast_event_name="Received_Severe_Treatment")
                             
    return {'cm_start': cm_start,'cm_clinical': cm_clinical_U5, 'cm_clinical_adult': cm_clinical_adult,  'cm_severe': cm_severe}

def smc_campaign(camp, row, start_array):
    # add_drug_campaign(camp, campaign_type = "SMC", start_days = [396,761,1126,1491,1856],
    ## Note, additional parameters might be added to SMC in future , i.e. repetitions or target group
    add_drug_campaign(camp, campaign_type="SMC", start_days=start_array,
                      drug_code="SPAQ", repetitions=4,
                      tsteps_btwn_repetitions=28,
                      coverage=float(row.smc_coverage),
                      target_group={'agemin': 0.25, 'agemax': 5},
                      receiving_drugs_event_name="Received_SMC")
    start_arrays = '; '.join([str(x) for x in start_array])
    return {'smc_start_emod': start_arrays, 'smc_coverage': row.smc_coverage}
