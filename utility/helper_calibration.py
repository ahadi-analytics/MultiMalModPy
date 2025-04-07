import os
import numpy as np
import pandas as pd


def get_calib_range():

    eir_range = [1.00000000e-01, 1.37382380e-01, 1.88739182e-01, 2.59294380e-01, 3.56224789e-01, 4.89390092e-01,
                 6.72335754e-01, 9.23670857e-01, 1.26896100e+00, 1.74332882e+00, 2.39502662e+00, 3.29034456e+00,
                 4.52035366e+00, 6.21016942e+00, 8.53167852e+00, 1.17210230e+01, 1.61026203e+01, 2.21221629e+01,
                 3.03919538e+01, 4.17531894e+01, 5.73615251e+01, 7.88046282e+01, 1.08263673e+02, 1.48735211e+02,
                 2.04335972e+02, 2.80721620e+02, 3.85662042e+02, 5.29831691e+02, 7.27895384e+02, 1.00000000e+03]


    x_temp_range = [5.00000000e-01, 6.58977729e-01, 8.68503294e-01, 1.14464866e+00,1.50859594e+00, 1.98826226e+00, 
                    2.62044110e+00, 3.45362465e+00, 4.55172345e+00, 5.99896876e+00, 7.90637362e+00, 1.04202483e+01,
                    1.37334231e+01, 1.81000399e+01, 2.38550464e+01, 3.14398886e+01, 4.14363727e+01, 5.46112936e+01, 
                    7.19752525e+01, 9.48601768e+01, 1.25021488e+02, 1.64772752e+02, 2.17163148e+02, 2.86211356e+02,
                    3.77213819e+02, 4.97151012e+02, 6.55222889e+02, 8.63554583e+02, 1.13812648e+03, 1.50000000e+03]
    return eir_range, x_temp_range



def output_target_to_xTemp(df, exp, model):
    """
    Interpolates and adjusts the output target to the `x_Temporary_Larval_Habitat` parameter based on input data
    for different models and experimental conditions.

    Args:
        df (pd.DataFrame): DataFrame containing simulation job data, with each row representing a specific condition
            (e.g., `target_output_values`, `cm_clinical`, `seasonality`).
        exp (Experiment): Experiment object that contains attributes such as `interp_path`, `target_output_name`, `pop_size`,
            and others required for interpolation.
        model (str): The model name used in the interpolation (e.g., 'malariasimulation', 'OpenMalaria').

    Returns:
        list: A list of interpolated `x_Temporary_Larval_Habitat` values corresponding to each row of the input DataFrame.

    Raises:
        ValueError: If the interpolation file is not found at the specified path.
        ValueError: If the `target_output_name` specified in the experiment object is not valid.

    Notes:
        - The function performs interpolation based on the specified output type (`eir`, `prevalence_2to10`, or
          `clinical_incidence_U5`).
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

    if exp.target_output_name == 'eir':
        output_type_col = 'eir'
    elif exp.target_output_name == 'prevalence_2to10':
        output_type_col = 'prevalence_2to10'
    elif exp.target_output_name == 'clinical_incidence_U5':
        output_type_col = 'clinical_incidence_U5'
    else:
        raise ValueError(f'Specified input_type is not valid {exp.target_output_name}')

    # NOTE: Workaround to allow smaller populations for test runs
    popsize = exp.emod_pop_size
    if exp.test and popsize not in data.loc[data['models'] == model, 'pop_size'].unique():
        popsize = int(data.loc[data['models'] == model, 'pop_size'].min())

    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['cm_severe'] == row['cm_severe'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['models'] == model)
                      & (data['pop_size'] == popsize))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['target_output_values']
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
            (e.g., `target_output_values`, `cm_clinical`, `seasonality`).
        exp (Experiment): Experiment object that contains attributes such as `interp_path`, `target_output_name`, `pop_size`,
            and others required for interpolation.
        model (str): The model name used in the interpolation (e.g., 'malariasimulation', 'OpenMalaria').

    Returns:
        list: A list of interpolated EIR values corresponding to each row of the input DataFrame.

    Raises:
        ValueError: If the interpolation file is not found at the specified path.
        ValueError: If the `target_output_name` specified in the experiment object is not valid.

    Notes:
        - The function performs interpolation based on the specified output type (`eir`, `prevalence_2to10`, or
          `clinical_incidence_U5`).
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
    if exp.target_output_name == 'eir':
        output_type_col = 'eir'
    elif exp.target_output_name == 'prevalence_2to10':
        output_type_col = 'prevalence_2to10'
    elif exp.target_output_name == 'clinical_incidence_U5':
        output_type_col = 'clinical_incidence_U5'
    else:
        raise ValueError(f'Specified input_type is not valid {exp.target_output_name}')
    if model == 'EMOD':
        popsize = exp.emod_pop_size
    elif model == 'malariasimulation':
        popsize = exp.malariasimulation_pop_size
    elif model == 'OpenMalaria':
        popsize = exp.openmalaria_pop_size
    else:
        raise ValueError(f'Specified model is not valid {model}')

    # NOTE: Workaround to allow smaller populations for test runs
    if exp.test and popsize not in data.loc[data['models'] == model, 'pop_size'].unique():
        popsize = data.loc[data['models'] == model, 'pop_size'].min()

    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['cm_severe'] == row['cm_severe'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['models'] == model)
                      & (data['pop_size'] == popsize))]
        xt = idata[output_type_col]
        yp = idata['input_target']
        xnew = row['target_output_values']
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

    for model in exp.models:
        if model == 'EMOD':
            popsize = exp.emod_pop_size
        elif model == 'malariasimulation':
            popsize = exp.malariasimulation_pop_size
        elif model == 'OpenMalaria':
            popsize = exp.openmalaria_pop_size
        else:
            raise ValueError(f'Specified model is not valid {model}')

        interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
        if not os.path.exists(interp_path):
            raise ValueError(f'interp_file not found: {interp_path}')
        data = pd.read_csv(interp_path)

        popsize_options = list( data.loc[data['models'] == model, 'pop_size'].unique())
        if  popsize not in popsize_options:
            if exp.test:
                print(f'Warning: the popsize specified for {model} ({popsize}) is not in the interpolation dataset, since running simulation as test. Using interpolation data with lowest popsize ({min(popsize_options)})') # see L140
            else:
                raise ValueError(f"Selected popsize {popsize} not availabe, options for {model} are  {', '.join([str(x) for x in popsize_options])}")

    # Check whether parameters align with current setup in calibruns - "interpolation data"
    if any(value not in data['cm_clinical'].unique().tolist() for value in exp.cm_clinical):
        raise ValueError(  f"Invalid cm_clinical values. Only allowed values are {data['cm_clinical'].unique().tolist()}. - requires new calibrun")

    if any(value not in data['cm_severe'].unique().tolist() for value in exp.cm_severe):
        raise ValueError( f"Invalid cm_severe values. Only allowed values are {data['cm_severe'].unique().tolist()}. - requires new calibrun")

    if any(value not in data['seasonality'].unique().tolist() for value in exp.seasonality):
        raise ValueError(  f"Invalid seasonality values. Only allowed values are {data['seasonality'].unique().tolist()}. - requires new calibrun")

    valid_cm_combinations = set(zip(data['cm_clinical'], data['cm_severe']))
    invalid_cm_values = set(exp.case_management) - valid_cm_combinations
    if invalid_cm_values:
        raise ValueError(
            f"Invalid cm_case_management values found: {invalid_cm_values}. "
            f"Only allowed values are {valid_cm_combinations}. Requires new calibrun.")

    if exp.target_output_name not in ['eir', 'prevalence_2to10', 'clinical_incidence_U5']:
        raise ValueError(f"Invalid output type: {exp.target_output_name}")
