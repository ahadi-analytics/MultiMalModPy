# Carrying Capacity step change (cc_step)

def cc_step_params(exp):
    """
    This function sets up the exp object so that the carrying capacity perterbation can occur.

    Parameters:
        exp: Experiment object.

    Returns:
        Experiment object
            An object with updated experiment parameters.
    """

    # Required fixed parameters for cc_step
    exp.step_in_years = 5
    exp.openmalaria_scaffold = "R0000GA_CC_STEP"
    exp.openmalaria_survey_step = '5d'

    # Flexible parameters depending on type of run and user-specifications
    if exp.run_mode == 'production':
        print('Warning: Running cc_step in production mode with pre-defined not user-defined parameters')
        exp.mem_increase_factor = 6.0  # scaling factor on default memory requested
        exp.pop_size = 50000
        exp.num_seeds_burnin = 1
        exp.num_seeds = 20
        exp.start_year = 1995
        exp.end_year = 2050
        exp.burnin = 80
        exp.output_type = 'prevalence_2to10'
        exp.output_target = [0.1, 0.25, 0.5]
        exp.cc_change = exp.output_target
    else:
        ## Keep parameters as defined by user in helper.py
        exp.cc_change = exp.output_target

    # Add cc_change to the list of sweep parameters
    exp.sweep_list = exp.sweep_list + ['cc_change']

    # 5 Years in to the pickup time OpenMalaria
    exp.cc_timestep_openmalaria = int((73 * (exp.burnin + exp.step_in_years)))

    if exp.emod_step is None:
        ## if None, no serialization done, hence burnin period is added to the step_in_years
        exp.cc_timestep_emod = int((exp.burnin + exp.step_in_years) * 365)
    else:
        # 5 years in to the pickup time EMOD and malariasimulation, this parameter can already be defined in burnin for the respective pickup run
        exp.cc_timestep_emod = int(exp.step_in_years * 365)
    exp.cc_timestep_malariasimulation = int((exp.burnin + exp.step_in_years) * 365)

    # Fixed parameters for cc_step
    exp.openmalaria_scaffold = "R0000GA_CC_STEP"  # defining which OpenMalaria XML scaffold to use
    exp.plots_to_run = ['ccstep']
    exp.analyzer_list = ['surveyallage', 'cc_step']
    return exp


def cc_step_factor_calculator(exp, df, model):
    """
    Calculates scaling factors for the `cc_step` intervention.
    This function computes adjustment factors for the `cc_step` intervention by interpolating
    values from a model-specific dataset. It takes input from a DataFrame `df`, an experiment
    object `exp`, and a model name `model`. The function performs the calculations using
    interpolation of prevalence or population size values and adjusts the output based on the
    simulated population size.

    Args:
        df (pd.DataFrame): A DataFrame containing data for calculations, with columns including:
            - `cm_clinical`
            - `seasonality`
            - `output_target`
            - `cc_change`
        exp (object): An object representing the experiment, which should include:
            - `interp_path` (str): Path to the folder containing interpolation data.
            - `interp_csv` (str): Name of the CSV file for interpolation.
            - `pop_size` (int): Population size for scaling factors.
        model (str): Name of the model used for interpolation. Supported values are `EMOD`
            and `OpenMalaria`.

    Returns:
        list[float]: A list of correction factors calculated for each row in the input DataFrame.

    Raises:
        ValueError: If the interpolation file (`interp_csv`) is not found in the specified path.

    Notes:
        - The function expects the interpolation file to contain columns:
          `cm_clinical`, `seasonality`, `modelname`, `pop_size`, `prevalence_2to10`, and
          either `input_target` or `n_total_mos_pop` depending on the model.
        - Population size scaling is applied to ensure compatibility with model fitting.

    """

    interp_path = os.path.join(exp.interp_path, model, exp.interp_csv)
    if not os.path.exists(interp_path):
        raise ValueError(f'interp_file not found: {interp_path}')
    data = pd.read_csv(interp_path)
    output = []
    for i, row in df.iterrows():
        idata = data[((data['cm_clinical'] == row['cm_clinical'])
                      & (data['seasonality'] == row['seasonality'])
                      & (data['modelname'] == model)
                      & (data['pop_size'] == exp.pop_size))]
        if model == 'EMOD':
            xt = idata['prevalence_2to10']
            yp = idata['input_target']
            xold = row['output_target']
            xnew = row['cc_change']
            interpolated_old = np.interp(xold, xt, yp)
        else:
            xt = idata['prevalence_2to10']
            yp = idata['n_total_mos_pop']
            xold = row['output_target']
            xnew = row['cc_change']
            interpolated_old = np.interp(xold, xt, yp)
        interpolated_new = np.interp(xnew, xt, yp)

        if exp.pop_size == 10000 or exp.pop_size == 50000:
            pop_fitting_was_run = exp.pop_size
        else:
            pop_fitting_was_run = 50000
        interpolated_old = interpolated_old / (pop_fitting_was_run / exp.pop_size)
        interpolated_new = interpolated_new / (pop_fitting_was_run / exp.pop_size)

        if model == 'OpenMalaria':
            interpolated_value = 1 - (interpolated_new / interpolated_old)
        else:
            interpolated_value = interpolated_new / interpolated_old
        output.append(interpolated_value)
    return output


def cc_title_function(df):
    """
    Generates a list of formatted strings representing percentage change titles
    based on the values in the provided DataFrame.

    Each row in the DataFrame contributes one title, formatted as:
    "<output_target>% - <cc_change>%", where:
    - `output_target` and `cc_change` are multiplied by 100 and converted to integers
      to represent percentage values.

    Args:
        df (pandas.DataFrame): A DataFrame containing the following columns:
            - `output_target` (float): The starting value for the percentage change.
            - `cc_change` (float): The change value for the percentage change.

    Returns:
        list[str]: A list of strings, where each string is a formatted title
                   representing the percentage change for a row.
    """
    output = []
    for i, row in df.iterrows():
        first_percent = int(float(row['output_target']) * 100)
        to_percent = int(float(row['cc_change']) * 100)
        title = f'{first_percent}%-{to_percent}%'
        output.append(title)
    return output


def cc_step_columns(exp, df):
    """
    Adds columns for CC steps if present.

    Args:
        exp (Experiment): The experiment object.
        df (pandas.DataFrame): The DataFrame.

    Returns:
        pandas.DataFrame: Updated DataFrame.
    """

    for model in ['EMOD', 'malariasimulation', 'OpenMalaria']:
        if model in exp.models_to_run or model in exp.models_to_run_pickup:
            df[f'cc_factor_{model.lower()}'] = cc_step_factor_calculator(df, exp, model=model)
            df[f'cc_timestep_{model.lower()}'] = getattr(exp, f'cc_timestep_{model.lower()}')
    df['cc_title'] = cc_title_function(df)
    return df  # FIXME can be moved to postprocessing



def cc_step_input_check(exp):

    if exp.entomology_mode != "dynamic":
        raise ValueError(f'Invalid entomology_mode for cc_step {exp.entomology_mode} specified, "dynamic" required')

    if exp.output_type != 'prevalence_2to10':
        raise ValueError("cc_step requires the output_type to be prevalence_2to10")

    if exp.end_year - exp.start_year < exp.step_in_years:
        raise ValueError(f"step_in_years ({exp.step_in_years} years) falls outside of the range of {exp.start_year} and {exp.end_year}")

