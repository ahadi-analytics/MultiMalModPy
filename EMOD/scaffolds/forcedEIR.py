import numpy as np
from emodpy_malaria.interventions.inputeir import add_scheduled_input_eir
from scipy.interpolate import interp1d


def mAb_vs_EIR(EIR):
    # Rough cut at function from eyeballing a few BinnedReport outputs parsed into antibody fractions
    mAb = 0.9 * (1e-4 * EIR * EIR + 0.7 * EIR) / (0.7 * EIR + 2)
    return min(mAb, 1.0)


def update_mab(simulation, value):
    simulation.task.config.parameters.Maternal_Antibody_Protection *= value
    return None



def set_inputEIR_seasonality(camp, EIR_scale_factor=1, seasonality='constant'):
    if seasonality == 'constant':
        monthly_EIR = [x / 12 for x in [1] * 12]
    elif seasonality == 'unimodal':
        monthly_EIR = [1, 1, 1, 1, 1, 3, 10, 10, 15, 18, 10, 0.1]
        eir_sum = sum([x for x in monthly_EIR])
        monthly_EIR = [(x / eir_sum) for x in monthly_EIR]  # rescale to sum = 1
    else:
        raise ValueError("Please specify valid seasonality")

    daily_EIR = monthly_to_daily_EIR(monthly_EIR)
    add_scheduled_input_eir(campaign=camp, start_day=1, daily_eir=daily_EIR, age_dependence="SURFACE_AREA_DEPENDENT",
                            node_ids=None, scaling_factor=EIR_scale_factor)


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
