import os
import numpy as np
import pandas as pd


def get_calib_range():

    eir_range = [1.00000000e-01, 1.37382380e-01, 1.88739182e-01, 2.59294380e-01, 3.56224789e-01, 4.89390092e-01,
                 6.72335754e-01, 9.23670857e-01, 1.26896100e+00, 1.74332882e+00, 2.39502662e+00, 3.29034456e+00,
                 4.52035366e+00, 6.21016942e+00, 8.53167852e+00, 1.17210230e+01, 1.61026203e+01, 2.21221629e+01,
                 3.03919538e+01, 4.17531894e+01, 5.73615251e+01, 7.88046282e+01, 1.08263673e+02, 1.48735211e+02,
                 2.04335972e+02, 2.80721620e+02, 3.85662042e+02, 5.29831691e+02, 7.27895384e+02, 1.00000000e+03]

    x_temp_range = [0.1, 0.12344971, 0.15239832, 0.18813529, 0.23225247,
                    0.28671501, 0.35394886, 0.43694886, 0.53941211, 0.66590271,
                    0.82205498, 1.01482452, 1.25279797, 1.5465755, 1.90924303,
                    2.35695505, 2.90965426, 3.59195985, 4.43426415, 5.47408639,
                    6.75774397, 8.34241558, 10.29868813, 12.71370101, 15.69502748,
                    19.37546647, 23.91895786, 29.52788498, 36.45208943, 45.]

    return eir_range, x_temp_range



def output_target_to_xTemp(df, exp, model):
    """
    Interpolates and adjusts the output target to the `x_Temporary_Larval_Habitat` parameter based on input data
    for different models and experimental conditions.

    Args:
        df (pd.DataFrame): DataFrame containing simulation job data, with each row representing a specific condition
            (e.g., `output_target`, `cm_clinical`, `seasonality`).
        exp (Experiment): Experiment object that contains attributes such as `interp_path`, `output_type`, `pop_size`,
            and others required for interpolation.
        model (str): The model name used in the interpolation (e.g., 'malariasimulation', 'OpenMalaria').

    Returns:
        list: A list of interpolated `x_Temporary_Larval_Habitat` values corresponding to each row of the input DataFrame.

    Raises:
        ValueError: If the interpolation file is not found at the specified path.
        ValueError: If the `output_type` specified in the experiment object is not valid.

    Notes:
        - The function performs interpolation based on the specified output type (`eir`, `prevalence_2to10`, or
          `clinical_incidenceU5`).
        - It applies scaling adjustments for population sizes, ensuring that the values are consistent with the
          `pop_size` defined in the experiment.
        - Warnings are issued if the interpolated values are outside the valid range (`<= 0` or `>= 10000`), with
          adjustments made to these values accordingly.
    """
    interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
    if not os.path.exists(interp_path):
        raise ValueError(f'interp_file not found: {interp_path}')

    data = pd.read_csv(interp_path)
    output = []

    if exp.output_type == 'eir':
        output_type_col = 'simulatedEIR'
    elif exp.output_type == 'prevalence_2to10':
        output_type_col = 'prevalence_2to10'
    elif exp.output_type == 'clinical_incidenceU5':  ## FIXME tbd later on how to add
        output_type_col = 'clinical_cases'  # name including age group?
    else:
        raise ValueError(f'Specified input_type is not valid {exp.output_type}')

    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['modelname'] == model)
                      & (data['pop_size'] == exp.emod_pop_size))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['output_target']
        interpolated_value = np.interp(xnew, xt, yp)

        if interpolated_value <= 0:
            interpolated_value = 0.01
            print("Warning: EMOD's x_Temporary_Larval_Habitat < 0, value set to 0.01 "
                  "(this will likely cause elimination in the simulations)")
        if interpolated_value >= 10000:
            interpolated_value = 10000
            print("Warning: EMOD's x_Temporary_Larval_Habitat > 10000, value set to 10000 "
                  "(higher values cannot be reasonably simulated)")
        output.append(interpolated_value)
    return output


def output_target_to_eir(df, exp, model):
    """
    Interpolates and adjusts the output target to the expected EIR (Entomological Inoculation Rate) values
    based on input data for different models and experimental conditions.

    Args:
        df (pd.DataFrame): DataFrame containing simulation job data, where each row represents a specific condition
            (e.g., `output_target`, `cm_clinical`, `seasonality`).
        exp (Experiment): Experiment object that contains attributes such as `interp_path`, `output_type`, `pop_size`,
            and others required for interpolation.
        model (str): The model name used in the interpolation (e.g., 'malariasimulation', 'OpenMalaria').

    Returns:
        list: A list of interpolated EIR values corresponding to each row of the input DataFrame.

    Raises:
        ValueError: If the interpolation file is not found at the specified path.
        ValueError: If the `output_type` specified in the experiment object is not valid.

    Notes:
        - The function performs interpolation based on the specified output type (`eir`, `prevalence_2to10`, or
          `clinical_incidenceU5`).
        - It applies scaling adjustments for population sizes, ensuring that the values are consistent with the
          `pop_size` defined in the experiment.
        - Warnings are issued if the interpolated values are outside the valid range (`<= 0` or `>= 1000`), with
          adjustments made to these values accordingly.
    """
    interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
    if not os.path.exists(interp_path):
        raise ValueError(f'interp_file not found: {interp_path}')

    data = pd.read_csv(interp_path)
    output = []
    if exp.output_type == 'eir':
        output_type_col = 'simulatedEIR'
    elif exp.output_type == 'prevalence_2to10':
        output_type_col = 'prevalence_2to10'
    elif exp.output_type == 'clinical_incidenceU5':
        output_type_col = 'clinical_incidenceU5'
    else:
        raise ValueError(f'Specified input_type is not valid {exp.output_type}')
    if model == 'EMOD':
        popsize = exp.emod_pop_size
    elif model == 'malariasimulation':
        popsize = exp.malariasimulation_pop_size
    elif model == 'OpenMalaria':
        popsize = exp.openmalaria_pop_size
    else:
        raise ValueError(f'Specified model is not valid {model}')

    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['modelname'] == model)
                      & (data['pop_size'] == popsize))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['output_target']
        interpolated_value = np.interp(xnew, xt, yp)
        if interpolated_value <= 0:
            interpolated_value = 0.01
            print("Warning: eir < 0, value set to 0.01 (this will likely cause elimination in the simulations)")
        if interpolated_value >= 1000:
            interpolated_value = 1000
            print("Warning:  eir > 1000, value set to 1000 (higher values cannot be reasonably simulated)")
        output.append(interpolated_value)
    return output


def check_transmission_targets_input(exp):

    # Check whether parameters align with current setup in calibruns - "interpolation data"
    if any(value[0] not in [0, 0.15, 0.45] for value in exp.case_management) and (exp.entomology_mode == 'dynamic') and (
            'EMOD' in exp.models_to_run):
        raise ValueError( 'EMOD is not set up to run dynamic EIR is not set up to run for CM values other than 0 and 0.45 - requires new calibrun')

    if any(value[0] not in [0, 0.15, 0.45] for value in exp.case_management) and exp.output_type == 'prevalence_2to10':
        raise ValueError('output_type prevalence_2to10 is not set up to run for CM values other than 0 and 0.45 - requires new calibrun')

    if exp.output_type not in ['eir', 'prevalence_2to10','clinical_incidenceU5']:
        raise ValueError(f"Invalid output type: {exp.output_type}")

