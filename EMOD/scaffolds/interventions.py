from emodpy_malaria.interventions.treatment_seeking import add_treatment_seeking


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
        cm_severe = min(cm_clinical * 1.15, 1)
        if cm_clinical == 0:
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