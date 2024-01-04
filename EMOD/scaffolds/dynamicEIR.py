import numpy as np


def eir_to_lhs_regr(df=None, population=1000):
    """
    Estimates Larval habitat scalar (LHS) value using a regression model based on
    Entomological Inoculation Rate (EIR),  clinical case management (cm) and seasonality.

    Parameters:
    - eir (float): The Entomological Inoculation Rate.
    - cm_clinical (float): The clinical case management.
    - seasonality (str): The seasonality type, either 'perennial' or 'seasonal'.
    - population (float): Population size of simulation.
    Returns:
    - lhs (float): The estimated larval habitat scalar.
    """
    # model coefficients, preliminary
    # there is certainly a better more efficient and robust way of determining lhs from eir and cm by seasonality
    # Regression model coefficients based on cm_clinical and seasonality
    output = []
    for index, row in df.iterrows():
        seasonality = row['seasonality']
        eir = float(row['eir'])
        if eir >= 100:
            eir_range = 100
        elif eir >= 30:
            eir_range = 30
        elif eir >= 5:
            eir_range = 5
        else: 
            eir_range = 0
        if seasonality == 'perennial':
            ## these were run for a population of 5000 people
            glm_byeir = {0: [1.409,4.056], 5: [-1.310,4.494], 30: [-7.675,5.304], 100: [-26.841,5.261]}

        elif seasonality == 'seasonal':
            ## these were run for a population of 5000 people
            glm_byeir = {0: [3.456, 3.286], 5: [1.616,3.956], 30: [-10.247, 4.843], 100: [-11.277, 4.957]} 
            
        else:
            raise ValueError(f'{seasonality} is not a valid seasonality')
            
        # Calculate LHS using regression model
        lhs = glm_byeir[eir_range][0] + float(eir) * glm_byeir[eir_range][1]
        lhs = lhs / (5000 / population)
        if lhs <= 0:
            lhs = 0.5 #this is a precaution, however we don't expect lhs values to be less than 0.5, we just don't want them to be 0.
        output.append(lhs)
    return output


def eir_to_lhs(eir=None, cm_clinical=None, population=None, seasonality='perennial', df=None):
    """
    Converts EIR (Entomological Inoculation Rate) and clinical malaria prevalence (cm) values to a corresponding LHS (Liver Hepatic Stage) value.

    Parameters:
    - eir (float): The Entomological Inoculation Rate.
    - cm_clinical (float): The clinical malaria prevalence.
    - df (DataFrame, optional): If provided, a pandas DataFrame containing EIR and cm_clinical columns. Used for batch calculations.
    - seasonality (str): The seasonality type, either 'perennial' or 'seasonal'. Determines which set of LHS values to use.
    - population (float): Population size of simulation.
    Returns:
    - lhs (float or list): The corresponding Liver Hepatic Stage value(s). If df is provided, a list of LHS values for each row in the DataFrame.
    """

    # Dictionary of LHS values for perennial and seasonal seasonality
    lhs_dict_perennial = {'eir': [0.1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024],
                          'cm0': [0.676, 1.160, 1.700, 2.780, 5.830, 12.180, 25.880, 55.440, 117.000, 245.000, 500.000,1010.000],
                          'cm0.2': [0.806, 1.340, 1.930, 3.110, 6.060, 13.040, 28.160, 60.340, 129.000, 266.000, 540.000, 1088.000],
                          'cm0.4': [1.14, 1.67, 2.25, 3.42, 6.53, 14.18, 29.12, 64.62, 132.00, 286.00, 595.00, 1212.00],
                          'cm0.6': [1.61, 2.16, 2.77, 3.99, 7.83, 16.18, 32.98, 72.08, 154.00, 326.00, 672.00, 1364.00],
                          'cm0.8': [3.31, 3.76, 4.26, 5.26, 9.34, 18.73, 39.37, 86.05, 170.00, 380.00, 802.00, 1646.00],
                          'cm1': [None, None, None, None, 10.76, 26.40, 55.41, 112.00, 242.00, 514.00, 1059.00,  2147.00]}

    lhs_dict_seasonal = {'eir': [0.1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024],
                         'cm0': [3.89, 6.89, 10.2, 16.9, 30.5, 69.0, 130, 326, 697, 1369, 2713, None],
                         'cm0.2': [5.26, 8.04, 11.1, 17.3, 34.7, 75.6, 145, 364, 760, 1485, 2935, None],
                         'cm0.4': [6.25, 9.56, 13.2, 20.6, 37.4, 81.0, 153, 382, 798, 1594, 3186, None],
                         'cm0.6': [10.2, 13.9, 17.9, 26.0, 43.8, 87.1, 171, 438, 890, 1826, 3697, None],
                         'cm0.8': [13.8, 23.8, 34.8, 56.9, 50.9, 107, 208, 502, 1008, 2164, 4476, None],
                         'cm1': [68.2, 74.4, 81.4, 95.3, 134, 193, 301, 655, 1321, 2812, 5795, None]}

    if seasonality == 'perennial':
        lhs_dict = lhs_dict_perennial
    elif seasonality == 'seasonal':
        lhs_dict = lhs_dict_seasonal
    else:
        print(f'Warning: seasonality is currently set to {seasonality}. Please set it to either perennial or seasonal')
        
    # Choose the appropriate LHS dictionary based on seasonality
    if eir is not None and cm_clinical is not None and seasonality is not None:
        # Calculate based on eir and cm_clinical
        lhs = calculate_from_eir_cm(eir, cm_clinical, lhs_dict)

    elif df is not None:
        # Calculate based on scen_df
        if df['seasonality'][0] == 'seasonal':
            lhs_dict = lhs_dict_seasonal
        lhs = calculate_from_df(df, lhs_dict)

    else:
        raise ValueError("Either eir, cm_clinical, and seasonality, or scen_df must be provided.")

    ## these were run for a population of 5000 people
    lhs = [l / (5000 / population) for l in lhs]

    return lhs


def calculate_from_eir_cm(eir, cm_clinical, lhs_dict):

    if isinstance(eir, (float, int)):
        eir = [eir]
    if isinstance(cm_clinical, (float, int)):
        cm_clinical = [cm_clinical]

    cm_val = cm_clinical[0]  ## here we do not want to create all combinations of eir and cm( thats where on
    lhs = []
    eir_none_values = []

    for eir_val in eir:
        if eir_val not in lhs_dict['eir']:
            raise ValueError(f"EIR value {eir_val} not found in the dictionary.")

        cm_label = f'cm{cm_val}'
        if cm_label not in lhs_dict:
            raise ValueError(f"CM label '{cm_label}' not found in the dictionary.")

        eir_index = lhs_dict['eir'].index(eir_val)
        lhs_values = lhs_dict[cm_label]

        if lhs_values[eir_index] is None:
            eir_none_values.append(eir_val)
        else:
            lhs.append(lhs_values[eir_index])

    if len(eir_none_values) > 0:
        print(f'Warning: no lhs values returned for the following EIR values: {", ".join(map(str, eir_none_values))}')

    return lhs


def calculate_from_df(df, lhs_dict):

    lhs = []
    eir_none_values = []

    for _, row in df.iterrows():
        eir_val = float(row['eir'])
        if eir_val > 1:
            eir_val = int(eir_val)

        cm_label = f"cm{row['cm_clinical']}"

        if eir_val not in lhs_dict['eir']:
            raise ValueError(f"EIR value {eir_val} not found in the dictionary.")
        if cm_label not in lhs_dict:
            raise ValueError(f"CM label '{cm_label}' not found in the dictionary.")

        eir_index = lhs_dict['eir'].index(eir_val)
        lhs_values = lhs_dict[cm_label]

        if lhs_values[eir_index] is None:
            eir_none_values.append(eir_val)
        else:
            lhs.append(lhs_values[eir_index])

    if len(eir_none_values) > 0:
        print(f'Warning: no lhs values returned for the following EIR values: {", ".join(map(str, eir_none_values))}')

    return lhs
