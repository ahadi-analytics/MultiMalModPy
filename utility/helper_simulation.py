import argparse
import os
import sys
import subprocess
import itertools
import pickle
from datetime import datetime
from datetime import datetime as dt
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d
#from idmtools.entities.experiment import Experiment


def get_intervention_params(exp):
    """
    Retrieve intervention parameters for a specific experiment.

    Parameters:
    - exp: Experiment object.

    Returns:
    Intervention parameters based on the specified experiment.
    """
    from utility.helper_interventions import exp_params_to_update
    return exp_params_to_update(exp)


def get_simulation_time_params(exp):
    """
    Calculates simulation time parameters for EMOD, malariasimulation and OpenMalaria based on the provided arguments.

    Args:
        exp (Experiment): Experiment object containing experiment specifications.
            - start_year (int): Monitoring start year (required by OpenMalaria utils).
            - end_year (int): Monitoring and simulation end year (required by OpenMalaria utils).
            - burnin (int): Duration of pre-monitoring years to run.
            - emod_step (str): Whether EMOD runs in one or two steps ('None' (one run), 'burnin', or 'pickup' (two separate runs)).

    Returns:
        exp (Experiment): Experiment object with updated simulation time parameters.
            - sim_start_year: Simulation start year
            - monitoring_years: Number of years to monitor (requried in EMOD analyzer)
            - sim_dur_years: Total simulation duration years
    """

    start_year = exp.start_year
    end_year = exp.end_year
    models = exp.models
    emod_step = exp.emod_step

    # Calculate the number of years to monitor
    monitoring_years = end_year - start_year

    if emod_step is None:
        if 'EMOD' in models:
            print(" --------| Running EMOD burnin + pickup time in one simulation run |--------")
        burnin_start_year = start_year - exp.emod_burnin
        sim_dur_years = end_year - burnin_start_year
        sim_start_year = burnin_start_year
    elif emod_step == 'burnin':
        if 'EMOD' in models:
            print(" --------| Running EMOD burnin (step 1) |--------")
        sim_dur_years = exp.emod_burnin
        burnin_start_year = start_year - exp.emod_burnin
        sim_start_year = burnin_start_year
    elif emod_step == 'pickup':
        if 'EMOD' in models:
            print(" --------| Running EMOD pickup from serialized burnin (step 2) |--------")
        sim_dur_years = end_year - start_year
        sim_start_year = start_year
    else:
        raise ValueError(f'Please specify valid emod_step, {emod_step} is not valid')

    # Update experiment object with simulation start year and duration
    exp.sim_start_year_emod = sim_start_year
    exp.sim_start_year_openmalaria = start_year - exp.openmalaria_burnin
    exp.sim_start_year_malariasimulation = start_year - exp.malariasimulation_burnin
    exp.monitoring_years = monitoring_years
    exp.sim_dur_years = sim_dur_years
    return exp


def param_variation(df, exp):
    """
    Perform parameter variation for malariasimulation simulations.

    Parameters:
    - df: DataFrame containing data from scenarios.csv.
    - exp: Experiment object.

    Returns:
    DataFrame with added column 'malariasimulation_pv' representing malariasimulation parameter variation values.
    """
    if exp.malariasimulation_parameter_variation and 'malariasimulation' in exp.models:
        from random import sample
        if exp.num_seeds > 1000:
            print("Warning: num_seeds > 1000, therefore malariasimulation parameter variation will have repeat values")
            par_var = [(i % 1000) + 1 for i in sample(range(1, exp.num_seeds + 1), exp.num_seeds)]
            for i, row in df.iterrows():
                df.loc[i, 'malariasimulation_pv'] = int(par_var[df.loc[i, 'seed'] - 1])
        else:
            par_var = sample(range(1, 1001), exp.num_seeds)
            for i, row in df.iterrows():
                df.loc[i, 'malariasimulation_pv'] = int(par_var[df.loc[i, 'seed'] - 1])
    return df


def get_seasonal_eir(exp=None):
    """
    Generates seasonal EIR (Entomological Inoculation Rate) values.

    Examples:
        season_daily, season_month, seasonal, perennial = get_seasonal_eir()
        exp = get_seasonal_eir(exp)

    Args:
        exp (Experiment, optional): Experiment object containing experiment specifications.

    Returns:
        tuple or Experiment: A tuple containing the daily, monthly, seasonal, and perennial EIR values if exp is None.
        If exp is provided, the Experiment object with updated seasonal EIR attributes is returned.

        If exp is None:
        - season_daily (list): Defined seasonal shape of daily EIR values.
        - season_month (list): Monthly EIR values calculated from the seasonal pattern.
        - seasonal (list): Seasonal EIR values rescaled within 0 to 1.
        - perennial (list): Perennial EIR values per month.

        If exp is provided:
        -  exp (Experiment): Experiment object with updated seasonality attributes.
    """

    # Define the seasonal setting
    # Seasonal Profile is based off of EMOD CM = 0, seasonal setting, EIR normalized to = 20
    seasonal = [0.030638115, 0.026802098, 0.03002848, 0.032621403, 0.04599955, 0.078275953,
                0.174936987,0.255347912,0.165683896,0.080265012,0.044885087,0.034515506]


    eir_sum = sum(seasonal)
    seasonal = [(x / eir_sum) for x in seasonal] # rescale to sum =1
    season_daily = [0.0010011279684418,0.0010097239518582,0.0010481215726008,0.0010117110659603,0.0010472720559485,0.0010259816266117,0.0010124444254704,
                    0.0009951089068391,0.0010161866795166,0.0010341233073265,0.0010101894239829,0.0010103311910211,0.0009861601960574,0.0010307201970606,0.0009664644065396,
                    0.0009700036420953,0.0009770508995089,0.0009752025342938,0.0009645113346624,0.0009759514951399,0.0009480705524473,0.0009542777335411,0.0009849594238979,
                    0.000937709271831,0.0009789015050021,0.0010012861448476,0.0009508447584766,0.0009721650972328,0.0009382419075254,0.0009173748490867,0.0009858970803781,
                    0.0009414325291445,0.0009748869816066,0.0009437870752048,0.0009493735712912,0.0009650650392662,0.0009641733935173,0.0009474925223476,0.0009622459912342,
                    0.0009613588922105,0.0009427228841248,0.0009597496162883,0.0009700990953764,0.0009558659207433,0.0009741947223473,0.0009627931999893,0.0009677345670456,
                    0.0009595099235733,0.0009769230512186,0.000909894401103,0.0009634409838153,0.000952420913784,0.0009670526645302,0.0009340348469847,0.000960042258452,
                    0.0009486182008147,0.0009320577556161,0.0009880737397372,0.0009670531187744,0.0009847033113578,0.0009839525458403,0.000967291635856,0.0009685981226799,
                    0.0009626083038823,0.0009142134353558,0.0009582121061202,0.0009811410364987,0.0009625908983273,0.0009587107031712,0.0009815184270997,0.000978205799492,
                    0.0009444663178197,0.000968069086661,0.0009722343982368,0.0009326292757058,0.0009845097713347,0.0009808633612159,0.0009433687992699,0.0009507712312346,
                    0.001009816277332,0.0009786226994658,0.0009813475391374,0.0010058573744826,0.000948743963072,0.0009803956764835,0.0009628378149034,0.0009420809973315,
                    0.0009833380138878,0.0009713988156153,0.0009853826780707,0.0010009047773921,0.0009745006278563,0.0009920225754285,0.0010036528524945,0.000990705727681,
                    0.0010237441221168,0.0010509718668002,0.0010102683727097,0.0010166777230352,0.0010561498153822,0.0010452190834911,0.0010572449427263,0.0010442806099238,
                    0.001068590231223,0.0010555007901103,0.0010836493452115,0.0010716313248767,0.0010894627996999,0.0011048292626664,0.001146803683872,0.001108033572987,
                    0.0011113226431011,0.0011519321744598,0.0011355089629293,0.0011841224639413,0.001192127607121,0.0012072712199611,0.0012081393735797,0.0011990899846458,
                    0.0012370445145551,0.0011730605166316,0.00127031169754,0.0013137780472436,0.0012616748548255,0.001260212147991,0.0012988917326767,0.0012923881427569,
                    0.0013084438802861,0.0013592233674383,0.0013819222778827,0.0013573458186064,0.0013860834225428,0.0013923087228067,0.0014120730112371,0.0014282951575128,
                    0.0014549959680126,0.001410907842516,0.001523452209337,0.0015116460483858,0.0015043352286507,0.0015829894845397,0.0015435967305851,0.0016251019610762,
                    0.0016361954665668,0.0016469100777352,0.0016916864836014,0.0017167175322687,0.0017599554997392,0.0017954912835483,0.001799297588126,0.0019002572985201,
                    0.001873027504588,0.0018969760075086,0.0020169839880532,0.0019969526228992,0.001995572137831,0.0021097860073291,0.0020594294685203,0.0022089092651733,
                    0.0022402350143862,0.0021664127986855,0.0023223808580212,0.0024387087227106,0.0023065407700781,0.0024517383012306,0.0025048847568997,0.0024872128728964,
                    0.0026411183510296,0.0026845918676105,0.0027264854262456,0.0028365662745588,0.0028701729652451,0.0029204943489142,0.0030422818205007,0.0030889163929009,
                    0.0030985233977793,0.0032949022560727,0.003401139348801,0.0034059864913354,0.0035516313209642,0.0036373921045176,0.0036420671937908,0.0038122649688841,
                    0.0038847979239251,0.0039534579963141,0.0040954732202762,0.0042480942331838,0.0042925462436074,0.0044711344513184,0.004555825805079,0.0046723888831023,
                    0.0049036161394977,0.0049860671656247,0.0050646912153437,0.0053719587103209,0.0054312017266227,0.005560049205392,0.0057087107324599,0.0059920794613795,
                    0.0059052416890218,0.0061516806639828,0.0064553909549573,0.0064406649767237,0.0066305506090795,0.0068948744063498,0.0069574574836651,0.0070060462025058,
                    0.0072765360346711,0.007479112202142,0.0074692440232993,0.007680667451719,0.0079430952802138,0.0078759542175893,0.0081400767460325,0.0082130695287754,
                    0.0083771209534805,0.0084372846936512,0.0084190417461321,0.0085706851113705,0.0086005282740665,0.0087090977204866,0.0087418076387228,0.0087410650650925,
                    0.0086552088068943,0.0087110423308143,0.0085518105527121,0.0085683600059913,0.0085067843653363,0.0084412575579592,0.0084667781282962,0.0084898129798839,
                    0.0083022291705794,0.0082409419792755,0.0081281049091449,0.0080568765589254,0.007975373106021,0.0078859642349834,0.007860485651143,0.0077375433255539,
                    0.0075713620843777,0.0076763702849824,0.0073657303597595,0.0073301440953107,0.0073426671987602,0.0071038691265189,0.0069089236621998,0.0069872284056192,
                    0.0067615792271557,0.006524383268767,0.0067066756265394,0.0064977471190577,0.0062106457718192,0.006294183402232,0.0060890541828527,0.0058579794391602,
                    0.0058156813704243,0.0056416588386496,0.0055249882564795,0.0054542612543156,0.0052714037461666,0.0051495983925125,0.0051620513296875,0.0049777812868176,
                    0.0048153608096845,0.0048083749757134,0.0046231205248771,0.0044593245368046,0.0044077926759585,0.004300200403993,0.0041065168498643,0.0040987410641891,
                    0.0040156808988875,0.0037664226623159,0.0037799178347636,0.0036676743679602,0.0034931843478639,0.003404928052903,0.0033486904620845,0.0031277968774647,
                    0.003149817705574,0.0030959960400595,0.0029370706542166,0.0028885731713675,0.002902020252816,0.0027053279672109,0.0026964859897506,0.0026402353183617,
                    0.0024677691527124,0.0024703910627307,0.0024979398150699,0.0022971570171794,0.0023553597134185,0.0023161497455823,0.0021654423109912,0.0021783422676835,
                    0.0021644289359255,0.0020506262334241,0.0020249050288153,0.0019872449271947,0.0019106608523562,0.0019409156926523,0.0018882829364377,0.0018531986500228,
                    0.0018584783932724,0.0017660945023049,0.0017494179190032,0.0017648816746019,0.0017551345501172,0.001676462843939,0.0016785856275826,0.0016455955405385,
                    0.0016100668503427,0.0016132257297348,0.0016093905004575,0.0015838614133083,0.001518693231978,0.0015661400832351,0.0014998515074621,0.001461636913716,
                    0.0014720776874356,0.0014444757975991,0.0013917387565898,0.0014447232946295,0.0014370920494508,0.001352299129255,0.0014052107653626,0.0013634140916965,
                    0.0013173989224128,0.001354208384182,0.0013060537127084,0.0012567549223943,0.0013405265842337,0.0012674568710982,0.0012326170083404,0.0012557062251447,
                    0.0012229124221244,0.0012131505483567,0.0012176975144742,0.0011850391125589,0.001180808527278,0.0011962249725742,0.0011296154621586,0.0011521065193204,
                    0.0011787719447177,0.0011265109080625,0.0011002279472852,0.0011538100317558,0.0011017779912842,0.0011120215637859,0.0010710788439209,0.0010862332643064,
                    0.0010803144279166,0.0010932244550952,0.0010789493187777,0.0010796367665829,0.00107719995965,0.0010381434597605,0.0010333940947955,0.0010722162794906,
                    0.0010537134919561,0.0010438091533953,0.0010577828507721,0.0010277643932679,0.0010534345944251,0.0010422290668547]

    perennial = [x / 12 for x in [1] * 12]
    perennial_daily = [x/365 for x in [1]*365]

    if exp is not None:
        exp.seasonal = seasonal
        exp.season_daily = season_daily
        exp.perennial = perennial
        exp.perennial_daily = perennial_daily
        return exp
    else:
        return season_daily


def monthly_to_daily_EIR(monthly_EIR):
    """
    Convert monthly EIR values to daily using cubic spline interpolation.

    Args:
        monthly_EIR (list of floats): List of monthly EIRs.

    Returns:
        list of floats: List of daily EIRs.
    """
    x_monthly = np.linspace(0, 364, num=12, endpoint=True)
    x_daily = np.linspace(0, 364, num=365, endpoint=True)
    EIR = interp1d(x_monthly, monthly_EIR, kind='linear')
    daily_EIR = EIR(x_daily)
    daily_EIR /= 30
    daily_EIR = daily_EIR.tolist()
    daily_EIR = [max(x, 0) for x in daily_EIR]

    return daily_EIR


def submit_run_plotters(exp):
    """
    Submits a plotter job for execution, either locally or via SLURM based on the HPC configuration:
    - If running locally, it generates and submits the plotter job using a local submission script.
    - If using SLURM, it delegates the submission to the SLURM-specific plotter submission function.

    Args:
        exp (object): An experiment object containing the necessary attributes, such as 'hpc',
                      to determine the appropriate submission method.
    """
    if exp.hpc == 'LOCAL':
        from utility.helper_local import submit_run_plotters_local
        submit_run_plotters_local(exp)
    else:
        from utility.helper_slurm import submit_run_plotters_slurm
        submit_run_plotters_slurm(exp)

def check_exp_input_parameters(exp):
    """
    Validates the input parameters and experiment configuration.

    This function performs the following checks:
    1. Verifies that the 'agebins' parameter contains all age groups referenced in 'age_groups_aggregates'.
    2. Ensures that 'agebins' includes both the values 2 and 10.
    3. Confirms that the 'seasonality' parameter contains no more than two seasonality patterns.

    Args:
        exp (object): An experiment object containing the attributes 'age_groups_aggregates', 'agebins', and 'seasonality'.

    Raises:
        ValueError: If any of the validation checks fail, an error is raised with a descriptive message indicating the issue.
    """

    # Check agebins against age_groups_aggregates
    missing_agebins  = {age for interval in exp.age_groups_aggregates for age in interval if age != 0 and age not in exp.agebins}
    if len(missing_agebins ) > 0:
        raise ValueError(
            f"The 'agebins' parameter is not granular enough to allow aggregation by 'age_groups_aggregates'. "
            f"The following age groups are missing from 'agebins': {missing_agebins}. Please ensure they are included."
        )

    # Ensure agebins contain required values
    if 2 not in exp.agebins or 10 not in exp.agebins:
        raise ValueError(
            f"The 'agebins' parameter must include both 2 and 10. Current 'agebins' values are {exp.agebins}. "
            "Please include both values to meet the framework's requirements."
        )

    # Check that only two seasonality patterns are specified
    if len(exp.seasonality) > 2:
        raise ValueError(
            f"Only two seasonality patterns are allowed, but {len(exp.seasonality)} were specified. "
            "Please limit the number of seasonality patterns to two."
        )
    
    for seasonal_name in exp.seasonality:
        if seasonal_name not in ['seasonal','perennial']:
            raise ValueError(
                f"Seasonality {seasonal_name} not in interpolation datasets."
                "Please indicate either seasonal or perennial instead."
            )
    
def check_exp_inputs_emod(exp):
    """
    Checks input parameter compatibility with the framework configurations for EMOD.

    This function performs the following checks:
    1. Ensures that only a single seed is specified for EMOD burn-in simulations.
    2. Issues a warning if the burn-in period is less than 100 years, which may lead to inaccurate results.
    3. Issues a warning if the population size is below 1000, which may lead to inaccurate results.
    4. Issues a warning if the population size exceeds 10000, which may cause computational or memory issues.

    Args:
        exp (object): An experiment object containing the attributes 'emod_step', 'num_seeds_burnin',
                      'emod_burnin', 'emod_pop_size', and 'models'.

    Raises:
        ValueError: If the 'num_seeds_burnin' is not set to 1 during an EMOD burn-in simulation.
    """

    if exp.hpc == 'LOCAL':
        raise ValueError("Local execution of the framework is not functional for EMOD.")


    if exp.emod_step:
        if exp.num_seeds_burnin != 1:
            raise ValueError(
                "The current framework supports only a single seed for EMOD burn-in simulations. "
                "Please set 'num_seeds_burnin' to 1 to proceed."
            )

    if exp.emod_burnin < 100 and (
            ('EMOD' in exp.models and exp.emod_step != 'pickup') or
            'EMOD' not in exp.models ):
        print(
            f"Warning: A burn-in period of at least 100 years is recommended for EMOD. "
            f"Currently, a shorter burn-in of {exp.emod_burnin} years has been configured, which may lead to inaccurate results."
        )

    if exp.emod_pop_size < 1000:
        print(
            f"Warning: A population of at least 1000 is recommended for EMOD. "
            f"Current pop_size {exp.emod_pop_size}  may lead to inaccurate results."
        )

    if exp.emod_pop_size > 10000:
        print(
            f"Warning: A high population of over 10000 is causing computational challenges for EMOD"
            f"Current pop_size {exp.emod_pop_size}  may lead to memory related issues."
        )



def check_exp_inputs_openmalaria(exp):
    """
    Checks input parameter compatibility with the framework configurations for OpenMalaria.

    This function performs the following checks:
    1. Issues a warning if OpenMalaria is configured with 30-day survey steps and a 5-day analyzer, as this configuration will cause errors during post-processing.
    2. Raises a ValueError if the 'ccstep' intervention is specified with 30-day survey steps, which is incompatible.
    3. Issues a warning if the burn-in period is less than 80 years, which may lead to inaccurate results.
    4. Issues a warning if the population size is below 10000, which may lead to inaccurate results.

    Args:
        exp (object): An experiment object containing the attributes 'openmalaria_survey_step', 'analyzer_list',
                      'intervention_list', 'openmalaria_burnin', and 'openmalaria_pop_size'.

    Raises:
        ValueError: If the 'ccstep' intervention is specified with a 30-day survey step in OpenMalaria.
    """

    # Check required files
    required_files = [
        os.path.join(exp.openmalaria_path, "densities.csv"),
        os.path.join(exp.openmalaria_path, f"scenario_{exp.openmalaria_version}.xsd")
    ]

    for file_path in required_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Required file not found: {file_path}")

    if exp.openmalaria_survey_step == '30d' and "5day" in exp.analyzer_list:
        print("Warning: OpenMalaria is configured with 30-day survey steps. Using a 5-day analyzer will cause errors during post-processing. Adjust your configuration to ensure compatibility.")

    if exp.openmalaria_survey_step == '30d' and "ccstep" in exp.intervention_list:
        raise ValueError("The 'ccstep' intervention requires 5-day survey steps in OpenMalaria. Please update the survey step configuration.")

    if exp.openmalaria_burnin < 80:
        print(
            f"Warning: A burn-in period of at least 80 years is recommended for OpenMalaria. "
            f"Currently, a shorter burn-in of {exp.openmalaria_burnin} years has been configured, which may lead to inaccurate results."
        )

    if exp.openmalaria_pop_size < 10000:
        print(
            f"Warning: A population of at least 10000 is recommended for OpenMalaria. "
            f"Current pop_size {exp.openmalaria_pop_size}  may lead to inaccurate results."
        )



def check_exp_inputs_malariasimulation(exp):
    """
    Checks input parameter compatibility with the framework configurations for malariasimulation

    This function performs the following checks:
    1. Raises a ValueError if the 'forced EIR' option is selected for entomology mode, as it is not supported.
    2. Issues a warning if the burn-in period is less than 80 years, which may lead to inaccurate results.
    3. Issues a warning if the population size is below 1000, which may lead to inaccurate results.

    Args:
        exp (object): An experiment object containing the attributes 'entomology_mode', 'malariasimulation_burnin',
                      and 'malariasimulation_pop_size'.

    Raises:
        ValueError: If the 'forced EIR' entomology mode is selected for MalariaSimulation.
    """

    if exp.entomology_mode == 'forced' :
        raise ValueError("The 'forced EIR' option is not supported in malariasimulation. Please select a valid entomology mode.")

    if exp.malariasimulation_burnin < 80:
        print(
            f"Warning: A burn-in period of at least 80 years is recommended for malariasimulation. "
            f"Currently, a shorter burn-in of {exp.malariasimulation_burnin} years has been configured, which may lead to inaccurate results."
        )

    if exp.malariasimulation_pop_size < 1000:
        print(
            f"Warning: A population of at least 1000 is recommended for malariasimulation. "
            f"Current pop_size {exp.malariasimulation_pop_size}  may lead to inaccurate results."
        )


