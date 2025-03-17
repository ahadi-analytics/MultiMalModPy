import argparse
import os
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
    models_to_run = exp.models_to_run
    emod_step = exp.emod_step

    # Calculate the number of years to monitor
    monitoring_years = end_year - start_year

    if emod_step is None:
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD burnin + pickup time in one simulation run |--------")
        burnin_start_year = start_year - exp.emod_burnin
        sim_dur_years = end_year - burnin_start_year
        sim_start_year = burnin_start_year
    elif emod_step == 'burnin':
        if 'EMOD' in models_to_run:
            print(" --------| Running EMOD burnin (step 1) |--------")
        sim_dur_years = exp.emod_burnin
        burnin_start_year = start_year - exp.emod_burnin
        sim_start_year = burnin_start_year
    elif emod_step == 'pickup':
        if 'EMOD' in models_to_run:
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
    if exp.malariasimulation_parameter_variation and 'malariasimulation' in exp.models_to_run:
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
    seasonal = [0.607137,0.5238911,0.5817383,0.6275442,0.8990297,1.5398529,
                    3.4620514,5.1668769,3.3351646,1.658007,0.9030859,0.6956209]    

    eir_sum = sum(seasonal)
    seasonal = [(x / eir_sum) for x in seasonal] # rescale to sum =1
    season_daily = [0.00100238202198747,0.00102977223630533,0.00102595721890364,0.00100802285805917,0.00102928943679262,0.000998688710517587,0.00102003782952794,0.000999136152453492,0.000944827778530301,0.00100422407146037,0.00101038044574546,0.000979077402674988,0.00100223084750598,0.00101035480887168,
                    0.000972473,0.000978282309780449,0.00100535398737523,0.000908053113733819,0.000953369041906478,0.000981006781024945,0.000949950325798485,0.000896842092375265,0.000968072806145555,0.000929077313685222,0.000950160602508582,0.000985442563194907,0.000938200858629029,0.000944050311259253,
                    0.000993825,0.000947580812308943,0.000990727246557707,0.000953251163163572,0.000919549218282055,0.000937792611548349,0.000940000552520609,0.000930781210411033,0.000927755273599831,0.000958196646381529,0.000917296166295533,0.000947019461137957,0.000918766312890415,0.000929346316595595,
                    0.000928449,0.000946681711190832,0.000959770397918777,0.000932824174901812,0.000938048393443288,0.000946388125578074,0.000949709016282131,0.00094359048033077,0.000933046912590322,0.000954527341643992,0.000939378026474852,0.000927535000115649,0.000940161085603465,0.000899550017929904,
                    0.000918376,0.000922397655998902,0.000934364591165861,0.000922181386804228,0.000920725206614825,0.000912243279119453,0.000955724110449094,0.000939582719148368,0.000943103286790046,0.000931526041180125,0.000958018544367592,0.000935081570770152,0.000930164324803639,0.000929352076952756,
                    0.000935909,0.000974134609579933,0.000959003330446872,0.000949851564897533,0.000964312855000298,0.000933767176078603,0.000922176852008057,0.000911411021927712,0.000949709713286183,0.000928393505359738,0.000907867681372879,0.000916430508009687,0.000939941696750946,0.000893271316118801,
                    0.000956382,0.000940013664267709,0.000931327717153942,0.000984434991091862,0.000971645833468732,0.000939227381277458,0.000971250607026811,0.000979874922608155,0.000945881336568484,0.00100281464687565,0.000988562716515227,0.000985054425133414,0.00102138223641581,0.000980393540223058,
                    0.000979499,0.00100359822435732,0.00100213838429839,0.00101078540948364,0.000976730818941203,0.00101797501867597,0.00102729146626039,0.000990089424606626,0.0010605723519052,0.00107702133731448,0.00103239407324604,0.0010555452806872,0.0010670938336374,0.00107583117945625,
                    0.001074021,0.00117668082672787,0.00111028108920404,0.00113114923168043,0.00114863532699642,0.00117504596172031,0.00116207579173108,0.00114754227238978,0.00122085261191875,0.00122380448396179,0.00117146293950049,0.00125544641359456,0.00127580062773859,0.0012260293529565,
                    0.001297304,0.00125831335643504,0.00128795335317946,0.0013371678121399,0.00134166770729147,0.00137798432181084,0.00138950737496109,0.00133646260473883,0.00143639242141824,0.00143834807697762,0.00146953350562367,0.0015091133274061,0.00144978560907131,0.00145019686514596,
                    0.001492831,0.00153183840286639,0.00155297948801262,0.001645781035907,0.0016300909178666,0.00163788032351947,0.00169596877839229,0.0016772350557329,0.001704198190533,0.00180963239010168,0.00181992414811504,0.00182966159623013,0.0018275161224877,0.00193693384751718,
                    0.001915004,0.0020202489767587,0.00202516285647409,0.00201919300615422,0.00216937001945548,0.00218041465616934,0.00217519065838872,0.00227028439578722,0.00232056824146529,0.00237483642127863,0.00246050659252497,0.00245599586415915,0.00250196404645796,0.00258661524948638,
                    0.002649622,0.00269941985435578,0.00277635918517946,0.00284216754119376,0.00290527494343554,0.00295358059942932,0.0030467538526692,0.0031679670584472,0.00319762006198824,0.00325314025851526,0.00346391209808884,0.00342026032069332,0.00354710137203881,0.00374328401356222,
                    0.003675,0.0037883069271638,0.00392862075217164,0.00402552823456798,0.00412862087165303,0.00427607653335133,0.0043317341041034,0.00446656069020947,0.00461095486433342,0.00478322015253347,0.00491316493283982,0.00509955122087697,0.00516615281194516,0.00533970573300236,
                    0.005525266,0.00559816431776059,0.00576921604737071,0.00599667695541619,0.00611693416776816,0.00629792612511173,0.00638719472795442,0.0065337766992724,0.00678389377538787,0.00696906414117245,0.00700806713349497,0.00721698783067922,0.00753753081090987,0.00749850619786195,
                    0.007650194,0.00793669216306927,0.0079961271079793,0.00806871401236168,0.00839072433502433,0.00856009285758015,0.00847467278375018,0.00860373827593957,0.00874539382745762,0.00859853319954582,0.00878105615397345,0.00887024406506029,0.00874813686542761,0.00870870354088987,
                    0.008883806,0.00876557226763686,0.0087226573911728,0.00873302851974204,0.00853887818783316,0.00854418834300665,0.0085340655681387,0.00841499509372685,0.00818343976559207,0.00815736342758664,0.0082122612756329,0.00803219524807086,0.00806654439272804,0.0080027143257398,
                    0.007693557,0.00772340577282385,0.00779903835067206,0.00743372073328824,0.00735627889667173,0.00731604344614741,0.00711166887815457,0.00690792596354083,0.00704538774338571,0.00674081227978311,0.00665514405962949,0.0066703291732657,0.00640130499469591,0.00624743394636341,
                    0.006350399,0.00607172309548793,0.00589997186205538,0.00595699451147499,0.0057800691246896,0.00560896095946803,0.00559662177782142,0.00539683487557271,0.00520746506494388,0.00520057943438146,0.00497746528393584,0.00481945873611796,0.00480933395402962,0.00461929508742525,
                    0.004496884,0.00448749300990178,0.00429058054783501,0.00414158019233638,0.00416673773577814,0.00397531723767791,0.00380841351157844,0.00382420317690682,0.00366569355238122,0.00356022796801018,0.00353467181929674,0.00343572943232461,0.00328098215287913,0.00330724718900059,
                    0.003232004,0.00305436127571112,0.00301175282631836,0.00292553083704241,0.00282607899773242,0.00279468629871196,0.00278736405849096,0.00262780747103618,0.0025599737564183,0.00260624344415064,0.0024548425789846,0.00240008714432307,0.00235741406051751,0.00230035552356048,
                    0.002264008,0.0021856345725963,0.00213973545262228,0.00206055611788738,0.00208530947432787,0.00198845201358427,0.00196154023261689,0.00195889143327701,0.0018909478614973,0.00181801568011108,0.00179288974139565,0.00180205815498349,0.00174338165333211,0.00177369591520879,
                    0.001715064,0.00170099320894899,0.00170952441867089,0.00164715890538313,0.00159790578488127,0.00158350026748714,0.00155884526453195,0.00153215186877374,0.00153946685537771,0.00149480182421235,0.00148656634877575,0.00149053031899776,0.00147025071114144,0.00141390986611353,
                    0.001399568,0.00137921935456106,0.00139742391022499,0.00138078893019666,0.00139052414749716,0.00133215682546082,0.00132657196255238,0.00133387271183953,0.00130612167578715,0.00128182471665741,0.00127703275135066,0.001296495434834,0.00121516961029712,0.00124776098620731,
                    0.001260528,0.00122417159160657,0.00121039760302081,0.00122679488394831,0.00119247162337916,0.00115711629473432,0.00115830433719592,0.0011945415932153,0.00115289313551687,0.0011675154573737,0.00112077245097235,0.00111562491024167,0.00113607716542048,0.00114598012435736,
                    0.001081161,0.00110147071410833,0.0011078941898698,0.00107401650085877,0.00109360984647529,0.00106873167462957,0.00109107163363425,0.00105604345484677,0.00106493769411736,0.00104748938470701,0.00100798165122577,0.00103025481886224,0.0010096391592546,0.00101001346905831,0.00101060874131283]

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
                      'emod_burnin', 'emod_pop_size', and 'models_to_run'.

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
            ('EMOD' in exp.models_to_run and exp.emod_step != 'pickup') or
            'EMOD' not in exp.models_to_run ):
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


