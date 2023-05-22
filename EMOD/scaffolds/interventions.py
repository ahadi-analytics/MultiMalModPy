import emodpy_malaria.interventions.treatment_seeking as cm


def treatment_camp(camp, cm_start=1, cm_clinical_U5=0.4, cm_clinical_adult=None, cm_severe=None):
    if cm_clinical_adult is None:
        cm_clinical_adult = cm_clinical_U5 * 0.75
    if cm_severe is None:
        cm_severe = min(cm_clinical_U5 * 1.15, 1)

    cm.add_treatment_seeking(camp, start_day=cm_start, drug=['Artemether', 'Lumefantrine'],
                             targets=[
                                 {'trigger': 'NewClinicalCase', 'coverage': cm_clinical_U5, 'agemin': 0, 'agemax': 5,
                                  'seek': 1, 'rate': 0.3},
                                 {'trigger': 'NewClinicalCase', 'coverage': cm_clinical_adult, 'agemin': 5,
                                  'agemax': 115,
                                  'seek': 1, 'rate': 0.3},
                                 {'trigger': 'NewSevereCase', 'coverage': cm_severe, 'agemin': 0, 'agemax': 115,
                                  'seek': 1, 'rate': 0.5}],
                             broadcast_event_name="Received_Treatment")
