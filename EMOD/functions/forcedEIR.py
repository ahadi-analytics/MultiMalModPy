from emodpy_malaria.interventions.inputeir import add_scheduled_input_eir

from utility.helper import get_seasonal_eir


def mAb_vs_EIR(EIR):
    # Rough cut at function from eyeballing a few BinnedReport outputs parsed into antibody fractions
    eir = float(EIR)
    mAb = 0.9 * (1e-4 * eir * eir + 0.7 * eir) / (0.7 * eir + 2.0)
    return min(mAb, 1.0)


def update_mab(simulation, value):
    """
    Update the Maternal Antibody Protection parameter within the simulation.

    Parameters:
        simulation (object): The simulation object from EMOD.
        value (float): The value by which to multiply the Maternal Antibody Protection parameter.

    Returns:
        None. The function modifies the simulation object in place.
    """
    simulation.task.config.parameters.Maternal_Antibody_Protection *= value
    return None


def set_inputEIR_seasonality(camp, EIR_scale_factor=1, seasonality="perennial"):
    """
    Set input EIR (Entomological Inoculation Rate) based on seasonality.

    Parameters:
    - camp: Campaign object from EMOD.
    - EIR_scale_factor: Scaling factor for EIR (default is 1).
    - seasonality: Type of seasonality, either 'perennial' or 'seasonal' (default is 'perennial').

    Returns:
    A dictionary containing the EIR scale factor and the specified seasonality.
    """

    season_daily = get_seasonal_eir()
    if seasonality == "perennial":
        daily_EIR = [x / 365 for x in [1] * 365]
    elif seasonality == "seasonal":
        daily_EIR = season_daily
        eir_sum = sum([x for x in daily_EIR])
        daily_EIR = [(x / eir_sum) for x in daily_EIR]  # rescale to sum = 1
    else:
        raise ValueError("Please specify valid seasonality")

    add_scheduled_input_eir(
        campaign=camp,
        start_day=1,
        daily_eir=daily_EIR,
        age_dependence="SURFACE_AREA_DEPENDENT",
        node_ids=None,
        scaling_factor=EIR_scale_factor,
    )

    return {"EIR_scale_factor": EIR_scale_factor, "seasonality": seasonality}
