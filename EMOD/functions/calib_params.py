# This is primarily seperate from MultiMalModPy's general function. This will allow  to vary NU's EMOD parameters associated with our within-host calibration efforts.
import os
import pandas as pd
from functools import partial
from EMOD.utils import set_param


def get_emod_calib_params(exp, scen_df):
    calib_config_df = pd.read_csv(
        os.path.join(exp.emod_input_path, 'emod_calibration_parameters', exp.emod_calib_type) + '.csv')
    if exp.emod_step == 'burnin':
        seeds = exp.num_seeds_burnin
    else:
        seeds = exp.num_seeds
    if exp.emod_calib_type == 'emod_best':
        calib_params = [[
            partial(set_param, param='Antigen_Switch_Rate',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Antigen_Switch_Rate'])),
            partial(set_param, param='Base_Gametocyte_Fraction_Male',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Base_Gametocyte_Fraction_Male'])),
            partial(set_param, param='Base_Gametocyte_Mosquito_Survival_Rate', value=float(
                calib_config_df.loc[int(row.calib_config_pointer), 'Base_Gametocyte_Mosquito_Survival_Rate'])),
            partial(set_param, param='Base_Gametocyte_Production_Rate',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Base_Gametocyte_Production_Rate'])),
            partial(set_param, param='Falciparum_MSP_Variants',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Falciparum_MSP_Variants'])),
            partial(set_param, param='Falciparum_Nonspecific_Types',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Falciparum_Nonspecific_Types'])),
            partial(set_param, param='Falciparum_PfEMP1_Variants',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Falciparum_PfEMP1_Variants'])),
            partial(set_param, param='Fever_IRBC_Kill_Rate',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Fever_IRBC_Kill_Rate'])),
            partial(set_param, param='Gametocyte_Stage_Survival_Rate',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Gametocyte_Stage_Survival_Rate'])),
            partial(set_param, param='MSP1_Merozoite_Kill_Fraction',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'MSP1_Merozoite_Kill_Fraction'])),
            partial(set_param, param='Nonspecific_Antibody_Growth_Rate_Factor', value=float(
                calib_config_df.loc[int(row.calib_config_pointer), 'Nonspecific_Antibody_Growth_Rate_Factor'])),
            partial(set_param, param='Nonspecific_Antigenicity_Factor',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Nonspecific_Antigenicity_Factor'])),
            partial(set_param, param='Pyrogenic_Threshold',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Pyrogenic_Threshold'])),
            partial(set_param, param='Max_Individual_Infections',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Max_Individual_Infections'])),
            partial(set_param, param='Erythropoiesis_Anemia_Effect',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Erythropoiesis_Anemia_Effect'])),
            partial(set_param, param='RBC_Destruction_Multiplier',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'RBC_Destruction_Multiplier'])),
            partial(set_param, param='Max_Individual_Infections',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Max_Individual_Infections'])),
            partial(set_param, param='Cytokine_Gametocyte_Inactivation', value=float(
                calib_config_df.loc[int(row.calib_config_pointer), 'Cytokine_Gametocyte_Inactivation'])),
            partial(set_param, param='Innate_Immune_Variation_Type',
                    value=str(calib_config_df.loc[int(row.calib_config_pointer), 'Innate_Immune_Variation_Type']))]
            for i, row in scen_df.iterrows()
            for s in range(seeds)]
    elif exp.emod_calib_type == 'emod_severe':
        calib_params = [[
            partial(set_param, param='Anemia_Severe_Inverse_Width',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Anemia_Severe_Inverse_Width'])),
            partial(set_param, param='Anemia_Severe_Threshold',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Anemia_Severe_Threshold'])),
            partial(set_param, param='Fever_Severe_Inverse_Width',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Fever_Severe_Inverse_Width'])),
            partial(set_param, param='Fever_Severe_Threshold',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Fever_Severe_Threshold'])),
            partial(set_param, param='Parasite_Severe_Inverse_Width',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Parasite_Severe_Inverse_Width'])),
            partial(set_param, param='Parasite_Severe_Threshold',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Parasite_Severe_Threshold'])),
            partial(set_param, param='RBC_Destruction_Multiplier',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'RBC_Destruction_Multiplier'])),
            partial(set_param, param='Maternal_Antibody_Protection',
                    value=float(calib_config_df.loc[int(row.calib_config_pointer), 'Maternal_Antibody_Protection'])),
        ]
            for i, row in scen_df.iterrows()
            for s in range(seeds)]
    else:
        calib_params = None
    return calib_params
