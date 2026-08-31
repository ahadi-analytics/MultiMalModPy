import os
import numpy as np
import pandas as pd


def get_calib_range():

    eir_range = [1.00000000e-01, 1.37382380e-01, 1.88739182e-01, 2.59294380e-01, 3.56224789e-01, 4.89390092e-01,
                 6.72335754e-01, 9.23670857e-01, 1.26896100e+00, 1.74332882e+00, 2.39502662e+00, 3.29034456e+00,
                 4.52035366e+00, 6.21016942e+00, 8.53167852e+00, 1.17210230e+01, 1.61026203e+01, 2.21221629e+01,
                 3.03919538e+01, 4.17531894e+01, 5.73615251e+01, 7.88046282e+01, 1.08263673e+02, 1.48735211e+02,
                 2.04335972e+02, 2.80721620e+02, 3.85662042e+02, 5.29831691e+02, 7.27895384e+02, 1.00000000e+03]


    x_temp_range = [3.00000000e-01, 3.89896984e-01, 5.06732193e-01, 6.58577845e-01, 8.55925050e-01, 1.11240865e+00,
                    1.44574926e+00, 1.87897758e+00, 2.44202564e+00, 3.17379477e+00, 4.12484335e+00, 5.36087994e+00,
                    6.96730305e+00, 9.05510148e+00, 1.17685225e+01, 1.52950381e+01, 1.98782974e+01, 2.58349606e+01, 
                    3.35765774e+01, 4.36380208e+01, 5.67144423e+01, 7.37092999e+01, 9.57967789e+01, 1.24502917e+02,
                    1.61811039e+02, 2.10298787e+02, 2.73316209e+02, 3.55217219e+02, 4.61660407e+02, 6.00000000e+02]
    return eir_range, x_temp_range



def output_target_to_xTemp(df, exp, model):
    df['transmission_intensity_EMOD'] = 2
    return df['transmission_intensity_EMOD']


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

        if exp.entomology_mode == 'forced' and 'forced' not in exp.interp_csv:
            interp_csv_forced = exp.interp_csv.replace('.csv', '_forced.csv')
            print(
                f'Warning: entomology_mode is {exp.entomology_mode}, however, interp_csv ({exp.interp_csv}) does not specify forced in filename. Changing to {interp_csv_forced}')
            exp.interp_csv = interp_csv_forced

        interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
        if not os.path.exists(interp_path):
            raise ValueError(f'interp_file not found: {interp_path}')

        data = pd.read_csv(interp_path)

        popsize_options = list(data.loc[data['models'] == model, 'pop_size'].unique())
        if popsize not in popsize_options:
            if exp.test:
                print(f'Warning: the popsize specified for {model} ({popsize}) is not in the interpolation dataset, since running simulation as test. Using interpolation data with lowest popsize ({min(popsize_options)})')
            else:
                raise ValueError(f"Selected popsize {popsize} not availabe, options for {model} are  {', '.join([str(x) for x in popsize_options])}")

    # Check whether parameters align with current setup in calibruns - "interpolation data"
    # NOTE: skipped for EMOD while the x_temp lookup is disabled (see helper_calibration.py) —
    # EMOD case management is no longer validated against interp_csv, since it's not being used to derive x_temp.
    if 'EMOD' not in exp.models:
        if any(value not in data['cm_clinical'].unique().tolist() for value in exp.cm_clinical):
            raise ValueError(f"Invalid cm_clinical values. Only allowed values are {data['cm_clinical'].unique().tolist()}. - requires new calibrun")

        if any(value not in data['cm_severe'].unique().tolist() for value in exp.cm_severe):
            raise ValueError(f"Invalid cm_severe values. Only allowed values are {data['cm_severe'].unique().tolist()}. - requires new calibrun")

        valid_cm_combinations = set(zip(data['cm_clinical'], data['cm_severe']))
        invalid_cm_values = set(exp.case_management) - valid_cm_combinations
        if invalid_cm_values:
            raise ValueError(
                f"Invalid cm_case_management values found: {invalid_cm_values}. "
                f"Only allowed values are {valid_cm_combinations}. Requires new calibrun.")

    if any(value not in data['seasonality'].unique().tolist() for value in exp.seasonality):
        raise ValueError(f"Invalid seasonality values. Only allowed values are {data['seasonality'].unique().tolist()}. - requires new calibrun")

    if exp.target_output_name not in ['eir', 'prevalence_2to10', 'clinical_incidence_U5']:
        raise ValueError(f"Invalid output type: {exp.target_output_name}")