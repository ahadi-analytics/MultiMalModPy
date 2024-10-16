def build_demog():
    """
    Builds the demographic structure for the EMOD simulation.
    This was used to generate the demographics.json which all future demographics will be based on.
    """
    # Create a Demographics object and set location and population size
    demog = Demographics.from_template_node(lat=1, lon=2, pop=1000, name="Example_Site")
    demog.SetEquilibriumVitalDynamics(CrudeRate(float(34.95)))
    demog.SetEquilibriumAgeDistFromBirthAndMortRates(CrudeRate(float(34.95)),
                                                    CrudeRate(float(34.95)))
    demog.SetBirthRate(CrudeRate(float(34.95)*10000))
    #demog.SetEquilibriumVitalDynamics()
    # Set the age distribution for the population
    age_distribution = Distributions.AgeDistribution_SSAfrica  ## Keep this for production run
    ## Define custom deaths rates to modify demography in alignment across models
    # from emod_api.demographics.PreDefinedDistributions import ConstantDistribution
    # from emod_api.demographics.PropertiesAndAttributes import IndividualAttributes
    # age_distribution = ConstantDistribution(IndividualAttributes.AgeDistribution(distribution_values=[
    #     [0, 0.034823157, 0.148672054, 0.279369812, 0.407205378, 0.525827528, 0.615957375, 0.686124742, 0.744257503,
    #      0.799399225, 0.841316335, 0.874783476, 0.904810137, 0.930423709, 0.959214183, 0.977995201, 0.988102517,
    #      0.995635694, 0.998360275, 1, 1]],
    #     result_scale_factor=1,
    #     result_values=[[0, 365, 1825, 3650, 5475, 7300, 9125, 10950, 12775, 14600, 16425, 18250, 20075, 21900, 23725,
    #                     25550, 27375, 29200, 31025, 32850, 34675, 36500]]))
    #
    demog.SetAgeDistribution(age_distribution)
    return demog