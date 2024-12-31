from emod_api.demographics.DemographicsTemplates import CrudeRate
import emodpy_malaria.demographics.MalariaDemographics as Demographics

def build_demog():
    """
    Builds the demographic structure for the EMOD simulation.
    This was used to generate the demographics.json which all future demographics will be based on.
    """
    # Create a Demographics object and set location and population size
    demog = Demographics.from_template_node(lat=1, lon=2, pop=1000, name="Example_Site")
    #demog.SetEquilibriumVitalDynamics(crude_birth_rate = CrudeRate(float(34.95)))
    demog.SetBirthRate(CrudeRate(float(34.95)*1000))
    demog.SetMortalityRate(CrudeRate(float(34.95)))
    demog.SetEquilibriumAgeDistFromBirthAndMortRates(CrudeRate(float(34.95)),
                                                    CrudeRate(float(34.95)))
       # Set the age distribution for the population
    #age_distribution = Distributions.AgeDistribution_SSAfrica  ## Keep this for production run
    ## Define custom deaths rates to modify demography in alignment across models
    from emod_api.demographics.PreDefinedDistributions import ConstantDistribution
    from emod_api.demographics.PropertiesAndAttributes import IndividualAttributes
    age_distribution = ConstantDistribution(IndividualAttributes.AgeDistribution(distribution_values=[ 
        0, 0.03474715,0.162347553,0.307562692,0.435119236,0.543482473,0.627415598,
        0.697429812,0.755435689,0.806457055,0.848282673,0.881676767,0.911537891,0.937095556,
        0.960423191,0.978163216,0.988248471,0.995665205,0.998383839,0.999999986],
        result_scale_factor=1,
        result_values=[0, 365, 1825, 3650, 5475, 7300, 9125,
                       10950, 12775, 14600, 16425, 18250, 20075, 21900,
                       23725, 25550, 27375, 29200, 31025, 32850]))
    mortality_distribution = ConstantDistribution(IndividualAttributes.MortalityDistribution(
        axis_names = ["gender", "age"],
        axis_scale_factors = [1,365],
        axis_units=["male=0,female=1","years"],
        population_groups=[[0,1],[0,100]],
        result_scale_factor=1,
        result_units="daily probability of dying",
        result_values=[[9.575800930934081e-05,0.99],[9.575800930934081e-05,0.99]]
    ))
    demog.SetAgeDistribution(age_distribution)
    demog.SetMortalityDistribution(mortality_distribution)
    return demog