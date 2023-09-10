import numpy as np
from emodpy_malaria.interventions.inputeir import add_scheduled_input_eir
from scipy.interpolate import interp1d
from helper import get_seasonal_eir


def mAb_vs_EIR(EIR):
    # Rough cut at function from eyeballing a few BinnedReport outputs parsed into antibody fractions
    mAb = 0.9 * (1e-4 * EIR * EIR + 0.7 * EIR) / (0.7 * EIR + 2)
    return min(mAb, 1.0)


def update_mab(simulation, value):
    simulation.task.config.parameters.Maternal_Antibody_Protection *= value
    return None



def set_inputEIR_seasonality(camp, EIR_scale_factor=1, seasonality='perennial'):
    season_daily, season_month, seasonal, perennial = get_seasonal_eir() 
    if seasonality == 'perennial':
        daily_EIR = [x / 365 for x in [1] * 365]
    elif seasonality == 'seasonal':
        daily_EIR = season_daily
        eir_sum = sum([x for x in daily_EIR])
        daily_EIR = [(x / eir_sum) for x in daily_EIR]  # rescale to sum = 1
    else:
        raise ValueError("Please specify valid seasonality")


    add_scheduled_input_eir(campaign=camp, start_day=1, daily_eir=daily_EIR, age_dependence="SURFACE_AREA_DEPENDENT",
                            node_ids=None, scaling_factor=EIR_scale_factor)

    return {'EIR_scale_factor': EIR_scale_factor,'seasonality': seasonality}

def monthly_to_daily_EIR(monthly_EIR):
    '''
    takes monthly EIR list and converts to daily using cubic spline interpolation
    :param monthly_EIR: list of monthly EIRs
    :type monthly_EIR: list of floats
    :return: list of daily EIRs
    :rtype: list of floats
    '''
    if len(monthly_EIR) == 12:
        monthly_EIR.append((monthly_EIR[0] + monthly_EIR[-1]) / 2)
    elif len(monthly_EIR) != 13:
        raise Exception('Monthly EIR should have 12 or 13 values')
    x_monthly = np.linspace(0, 364, num=13, endpoint=True)
    x_daily = np.linspace(0, 364, num=365, endpoint=True)
    EIR = interp1d(x_monthly, monthly_EIR, kind='cubic')
    daily_EIR = EIR(x_daily)
    daily_EIR /= 30
    daily_EIR = daily_EIR.tolist()
    daily_EIR = [max(x, 0) for x in daily_EIR]

    return daily_EIR
