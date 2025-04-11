from emodpy_malaria.interventions.treatment_seeking import add_treatment_seeking
from emodpy_malaria.interventions.scale_larval_habitats import add_scale_larval_habitats
import pandas as pd
from emod_api.interventions.common import *
import random
from emodpy_malaria.interventions.common import add_campaign_event
from emod_api import schema_to_class as s2c

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


def carrying_capacity(camp, row):
    cc_factor_df = pd.DataFrame({'CONSTANT': [row.cc_factor_EMOD]})
    add_scale_larval_habitats(camp, df=cc_factor_df,
                                  start_day=row.cc_timestep_EMOD,
                                  repetitions=1)
    return camp

def mda(camp, row):
    add_drug_campaign(camp, campaign_type = 'MDA', drug_code = 'MDA_CUSTOM', start_days = [row.mda_timestep_EMOD],
                      coverage = row.mda_coverage, repetitions = 1)
    return camp


# Different configurations of regimens and drugs
drug_cfg = {
    "ALP": ["Artemether", "Lumefantrine", "Primaquine"],
    "AL": ["Artemether", "Lumefantrine"],
    "ASA": ["Artesunate", "Amodiaquine"],
    "DP": ["DHA", "Piperaquine"],
    "DPP": ["DHA", "Piperaquine", "Primaquine"],
    "PPQ": ["Piperaquine"],
    "DHA_PQ": ["DHA", "Primaquine"],
    "DHA": ["DHA"],
    "PMQ": ["Primaquine"],
    "DA": ["DHA", "Abstract"],
    "CQ": ["Chloroquine"],
    "SP": ["Sulfadoxine", "Pyrimethamine"],
    "SPP": ["Sulfadoxine", "Pyrimethamine", 'Primaquine'],
    "SPA": ["Sulfadoxine", "Pyrimethamine", 'Amodiaquine'],
    "Vehicle": ["Vehicle"],
    "MDA_CUSTOM": ["MDA_CUSTOM"]
}

def add_drug_campaign(campaign,
                      campaign_type: str = 'MDA',
                      drug_code: str = None,
                      start_days: list = None,
                      coverage: float = 1.0,
                      repetitions: int = 1,
                      tsteps_btwn_repetitions: int = 60,
                      trigger_coverage: float = 1.0,
                      treatment_delay: int = 0,
                      triggered_campaign_delay: int = 0,
                      node_ids: list = None,
                      target_group: any = 'Everyone',
                      drug_ineligibility_duration: int = 0,
                      ind_property_restrictions: list = None,
                      disqualifying_properties: list = None,
                      trigger_condition_list: list = None,
                      listening_duration: int = -1,
                      target_residents_only: int = 1,
                      check_eligibility_at_trigger: bool = False,
                      receiving_drugs_event_name='Received_Campaign_Drugs'):
    """ 
    Add a drug intervention campaign from a list of malaria campaign types.
    This intervention uses the
    :doc:`emod/parameter-campaign-individual-malariadiagnostic` class
    to create either a scheduled or a triggered event to the campaign and the
    :doc:`emod/parameter-campaign-individual-antimalarialdrug` class
    to configure drug interventions. You can also specify a delay period for a
    triggered event that broadcasts afterwards.  If the campaign is repeated
    or triggered, separate 
    :doc:`emod/parameter-campaign-node-nodelevelhealthtriggerediv`
    interventions are created with a delay that sends an event to distribute
    drugs.

    Args:
        campaign: The :py:obj:`emod_api:emod_api.campaign` object to which the intervention will
            be added. 
        campaign_type: The type of drug campaign. Available options are:
            MDA - Add a mass drug administration intervention.
        drug_code: The code of the drug regimen to distribute. This must be 
            listed in the ``drug_cfg`` dictionary.
        start_days: List of start days (integers) when the drug regimen will
            be distributed. Due to diagnostic/treatment configuration,
            the earliest start day is 1. When **trigger_condition_list** is used,
            the first entry of **start_days** is the day to start listening
            for the trigger(s).
        coverage: The demographic coverage of the distribution (the fraction of
            people at home during the campaign).
        repetitions: The number of repetitions.
        tsteps_btwn_repetitions: The timesteps between the repetitions.
        trigger_coverage: The fraction of trigger events that will trigger reactive
            case detection (RCD). Used when **campaign_type** is set to rfMSAT or rfMDA. 
            To set the fraction of individuals reached during RCD response, use **coverage**.
        trigger_name: Name of broadcast event sent out after trigger event.
            Also used as in drug campaign with default "Received_{trigger_name}"
            Example:
                "IPTi_{x}" with x = number of IPTi dose
        snowballs: The number of times each triggered intervention will be distributed
            to surrounding nodes. For example, one snowball gives drugs to nodes
            neighboring the first node and two snowballs gives drugs to the nodes 
            neighboring those nodes. Used when **campaign_type** is set to rfMSAT.
        treatment_delay: For **campaign_type** set to MSAT or fMDA, the length of time 
            between administering a diagnostic and giving drugs; for values of rfMSAT 
            or rfMDA, the length of time between treating the index case and triggering 
            an RCD response.
        triggered_campaign_delay: When using **trigger_condition_list**, this
            indicates the delay period between receiving the trigger event
            and running the triggered campaign intervention.
        delay_distribution: For triggered_campaign_delay_event used in IPTi campaign,
            dictionary of parameters that define the distribution for duration at node, including the distribution
            Default: None
            Durations are in days.

            Examples::

                {"Delay_Period_Distribution":"GAUSSIAN_DISTRIBUTION",
                 "Delay_Period_Gaussian_Mean": triggered_campaign_delay, "Delay_Period_Gaussian_Std_Dev" 3}

        node_ids: The setting for **Node_List** in :ref:`campaign-nodeset-config`.
        target_group: A dictionary of ``{'agemin': x, 'agemax': y}`` to
            target MDA, SMC, MSAT, fMDA to individuals between x and y years
            of age. Default is Everyone.
        drug_ineligibility_duration: The number of days to set the **DrugStatus** 
            individual property to **RecentDrug**, after which the property value
            is reverted. This property value prevents people from receiving drugs too
            frequently, but they can still receive diagnostics during this period.
            For more information, see :doc:`emod/model-targeted-interventions`.
        ind_property_restrictions: The setting for **Property_Restrictions_Within_Node**
            in :doc:`emod/parameter-campaign-event-triggeredeventcoordinator`
            that individuals must have to receive the diagnostic intervention.
        ind_prop_restr_birthtrigger_event: List of IndividualProperty key:value pairs that
            individuals must have to create trigger event for the intervention.
            For example, ``[{"IndividualProperty1":"PropertyValue1"},
            {"IndividualProperty2":"PropertyValue2"}]``. Default is no restrictions.
            Used in triggered_campaign_delay_event that creates BroadcastEvent to trigger vaccine campaign.
        disqualifying_properties: The setting for **Disqualifying_Properties**
            in :doc:`emod/parameter-campaign-individual-antimalarialdrug` or
            in :doc:`emod/parameter-campaign-individual-malariadiagnostic`.
        trigger_condition_list: The setting for **Start_Trigger_Condition_List** in
            :doc:`emod/parameter-campaign-event-triggeredeventcoordinator`.
        listening_duration: The setting for **Duration** in
            :doc:`emod/parameter-campaign-event-triggeredeventcoordinator`.
        target_residents_only: The setting for **Target_Residents_Only** in
            :doc:`emod/parameter-campaign-event-triggeredeventcoordinator`.
        check_eligibility_at_trigger: Set to True to check the individual or node's 
            eligibility at the initial trigger; set to False to check eligibility
            when the event is actually distributed after a delay.
        receiving_drugs_event_name: The event to broadcast when a person receives drugs.

    Returns:
        A dictionary with drug campaign parameters.
    """

    drug_configs = drug_configs_from_code(campaign, drug_code=drug_code)
    if not ind_property_restrictions:
        ind_property_restrictions = []
    if not disqualifying_properties:
        disqualifying_properties = []

    # set up events to broadcast when receiving campaign drug
    receiving_drugs_event = BroadcastEvent(campaign, Event_Trigger=receiving_drugs_event_name)
    if campaign_type[0] == 'r':  # if reactive campaign
        receiving_drugs_event.Broadcast_Event = 'Received_RCD_Drugs'
    if drug_code and 'Vehicle' in drug_code:  # if distributing Vehicle drug
        receiving_drugs_event.Broadcast_Event = "Received_Vehicle"

    expire_recent_drugs = None
    if drug_ineligibility_duration > 0:
        expire_recent_drugs = PropertyValueChanger(camp=campaign,
                                                   Target_Property_Key="DrugStatus",
                                                   Target_Property_Value="RecentDrug",
                                                   Revert=drug_ineligibility_duration)
    if start_days is None:
        start_days = [1]
    # set up drug campaign
    if campaign_type == 'MDA' or campaign_type == 'SMC':
        if treatment_delay:
            raise ValueError('"treatment_delay" parameter is not used in MDA or SMC')
        add_MDA(campaign, start_days=start_days, coverage=coverage, drug_configs=drug_configs,
                receiving_drugs_event=receiving_drugs_event, repetitions=repetitions,
                tsteps_btwn_repetitions=tsteps_btwn_repetitions, node_ids=node_ids,
                expire_recent_drugs=expire_recent_drugs,
                ind_property_restrictions=ind_property_restrictions, disqualifying_properties=disqualifying_properties,
                target_group=target_group, trigger_condition_list=trigger_condition_list,
                listening_duration=listening_duration, triggered_campaign_delay=triggered_campaign_delay,
                target_residents_only=target_residents_only, check_eligibility_at_trigger=check_eligibility_at_trigger)
    else:
        raise Exception('Warning: unrecognized campaign type\n')
        pass

    return {'drug_campaign.type': campaign_type,
            'drug_campaign.drugs': drug_code,
            'drug_campaign.trigger_coverage': trigger_coverage,
            'drug_campaign.coverage': coverage
            }


def drug_configs_from_code(campaign, drug_code: str = None):
    """  
    Add a single or multiple drug regimen to the configuration file based
    on its code and add the corresponding 
    :doc:`emod/parameter-campaign-individual-antimalarialdrug`
    intervention to the return dictionary. For example, passing the ``ALP`` drug
    code will add the drug configuration for artemether, lumefantrine, and
    primaquine to the configuration file and will return a dictionary containing a
    full treatment course for those three drugs. For more information, see
    **Malaria_Drug_Params** in :doc:`emod/parameter-configuration-drugs`.
      
    Args:
        campaign: The :py:obj:`emod_api:emod_api.campaign` object to which the intervention
            will be added. 
        drug_code: The code of the drug regimen. This must be listed in the ``drug_cfg`` 
            dictionary.

    Returns:
          A dictionary containing the intervention for the given drug regimen.
    """
    if not drug_code or drug_code not in drug_cfg:
        raise Exception("Please pass in a (valid) drug_code.\n"
                        "Available drug codes:\n"
                        "\"ALP\": Artemether, Lumefantrine, Primaquine.\n"
                        "\"AL\": Artemether, Lumefantrine. \n"
                        "\"ASAQ\": Artesunate, Amodiaquine.\n"
                        "\"DP\": DHA, Piperaquine.\n"
                        "\"DPP\": DHA, Piperaquine, Primaquine.\n"
                        "\"PPQ\": Piperaquine.\n"
                        "\"DHA_PQ\": DHA, Primaquine.\n"
                        "\"DHA\": DHA.\n"
                        "\"PMQ\": Primaquine.\n"
                        "\"DA\": DHA, Abstract.\n"
                        "\"CQ\": Chloroquine.\n"
                        "\"SP\": Sulfadoxine, Pyrimethamine.\n"
                        "\"SPP\": Sulfadoxine, Pyrimethamine, Primaquine.\n"
                        "\"SPA\": Sulfadoxine, Pyrimethamine, Amodiaquine.\n"
                        "\"Vehicle\": Vehicle.\n" 
                        "\"MDA_CUSTOM\": MDA_CUSTOM.\n")
    drug_array = drug_cfg[drug_code]

    drug_configs = []
    for drug in drug_array:
        drug_intervention = _antimalarial_drug(campaign, drug_type=drug, cost_to_consumer=1.5)
        drug_configs.append(drug_intervention)
    return drug_configs



def _antimalarial_drug(campaign,
                       drug_type: str = None,
                       cost_to_consumer: float = 0,
                       intervention_name: str = None):
    """
        Configures individual-targeted AntimalarialDrug intervention
    Args:
        campaign: campaign object to which the intervention will be added, and schema_path container
        drug_type: The name of the drug to distribute in a drug intervention. Possible values are
            contained in **Malaria_Drug_Params** in :doc:`emod/parameter-configuration-drugs`.
            Use :py:meth:`~emodpy_malaria.config.set_team_drug_params` to set those values
        cost_to_consumer: Per-unit cost when drug is distributed
        intervention_name: The optional name used to refer to this intervention as a means to differentiate it from
            others that use the same class. Default is AntimalarialDrug_<drug_type>.

    Returns:
        Configured individual-targeted AntimalarialDrug intervention
    """
    if not drug_type:
        raise ValueError("Please pass in 'drug_type', as defined in Malaria_Drug_Params.Name.\n")
    intervention = s2c.get_class_with_defaults("AntimalarialDrug", campaign.schema_path)
    intervention.Drug_Type = drug_type
    intervention.Cost_To_Consumer = cost_to_consumer
    intervention.Intervention_Name = intervention_name if intervention_name else "AntimalarialDrug_" + drug_type
    return intervention




def add_MDA(campaign, start_days: list = None, coverage: float = 1.0, drug_configs: list = None,
            receiving_drugs_event: BroadcastEvent = None, repetitions: int = 1, tsteps_btwn_repetitions: int = 60,
            node_ids: list = None, expire_recent_drugs: PropertyValueChanger = None,
            ind_property_restrictions: list = None, disqualifying_properties: list = None,
            target_group: any = 'Everyone',
            trigger_condition_list: list = None, listening_duration: int = -1, triggered_campaign_delay: int = 0,
            target_residents_only: int = 1, check_eligibility_at_trigger: bool = False):
    """
    Add an MDA (mass drug administration) drug intervention to your campaign. 
    See :py:func:`add_drug_campaign` for more information about each
    argument.

    Returns:
        None
    """

    if start_days is None:
        start_days = [1]
    if drug_configs is None:
        raise Exception("You have to pass in drug_configs (list of drug configurations) that can be generated with "
                        "malaria.interventions.malaria_drugs import drug_configs_from_code.\n")
    if disqualifying_properties is None:
        disqualifying_properties = []

    interventions = drug_configs
    if receiving_drugs_event:
        interventions.append(receiving_drugs_event)
    if expire_recent_drugs:
        interventions.append(expire_recent_drugs)

    target_sex = "All"
    target_age_min = 0
    target_age_max = 9.3228e+35
    if "agemin" in target_group:
        target_age_min = target_group["agemin"]
    if "agemax" in target_group:
        target_age_max = target_group["agemax"]
    if "gender" in target_group:
        target_sex = target_group["gender"]

    """
        raise KeyError("Unknown target_group parameter. Please pass in 'Everyone' or a dictionary of "
                       "{'agemin' : x, 'agemax' : y, 'gender': 'Female'} to target  to individuals between x and "
                       "y years of age, and (optional) gender.\n")
    """

    if trigger_condition_list:
        # if once triggered, you want the diagnostic survey to repeat or if there is a delay (or both)
        # this creates a series of broadcast events that once triggered send out broadcast_event
        # at pre-determined intervals
        if repetitions > 1 or triggered_campaign_delay > 0:
            # create a trigger for each of the delays.
            broadcast_event = "MDA_Now_{}".format(random.randint(1, 10000))
            trigger_ind_property_restrictions = []
            if check_eligibility_at_trigger:
                trigger_ind_property_restrictions = ind_property_restrictions
                ind_property_restrictions = []
            for x in range(repetitions):
                tcde = TriggeredCampaignEvent(
                    campaign,
                    Start_Day=start_days[0] + 1,
                    Event_Name="MDA_Delayed",
                    Node_Ids=node_ids,
                    Triggers=trigger_condition_list,
                    Duration=listening_duration,
                    Intervention_List=[BroadcastEvent(campaign, broadcast_event)],
                    Property_Restrictions=trigger_ind_property_restrictions,
                    Delay=triggered_campaign_delay + (x * tsteps_btwn_repetitions))
                campaign.add(tcde)
            trigger_condition_list = [broadcast_event]

        drug_event = TriggeredCampaignEvent(
            campaign,
            Start_Day=start_days[0],
            Event_Name="MDA_Now",
            Node_Ids=node_ids,
            Target_Age_Min=target_age_min,
            Target_Age_Max=target_age_max,
            Target_Gender=target_sex,
            Property_Restrictions=ind_property_restrictions,
            Demographic_Coverage=coverage,
            Disqualifying_Properties=disqualifying_properties,
            Triggers=trigger_condition_list,
            Duration=listening_duration,
            Target_Residents_Only=target_residents_only,
            Intervention_List=interventions)
        campaign.add(drug_event)

    else:
        for start_day in start_days:
            add_campaign_event(
                campaign=campaign,
                start_day=start_day,
                node_ids=node_ids,
                target_age_min=target_age_min,
                target_age_max=target_age_max,
                target_gender=target_sex,
                ind_property_restrictions=ind_property_restrictions,
                demographic_coverage=coverage,
                individual_intervention=interventions,
                repetitions=repetitions,
                timesteps_between_repetitions=tsteps_btwn_repetitions)

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