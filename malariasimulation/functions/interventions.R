### Interventions

# SMC currently not supported

#' Define SMC Parameters for malariasimulation
#'
#' This function defines and assigns parameters related to seasonal malaria chemoprevention (SMC)
#' campaigns for malariasimulation. The function calculates the SMC distribution
#' days, coverage levels, and target age groups based on the provided experimental setup and
#' scenarios to run.
#'
#' @param exp A list representing the experimental setup, where SMC-related parameters
#'            (e.g., distribution days, coverages, age ranges) will be added or modified.
#' @param scenarios_to_run A data frame containing scenario-specific variables, including:
#'        \itemize{
#'          \item \code{eir} (int): The entomological inoculation rate, which determines the timing
#'                and frequency of SMC distributions.
#'          \item \code{smc_coverage} (numeric): The coverage level for SMC interventions.
#'        }
#'
#' @return The modified \code{exp} object with the following new fields:
#'         \itemize{
#'           \item \code{smc_days}: A matrix of SMC distribution days for each scenario.
#'           \item \code{smc_coverages}: A matrix of SMC coverage levels for each distribution day.
#'           \item \code{smc_min_ages}: A matrix of minimum ages (in days) for targeted individuals.
#'           \item \code{smc_max_ages}: A matrix of maximum ages (in days) for targeted individuals.
#'         }
#'
#' @export
define_smc_param <- function(exp, scenarios_to_run) {

  # Find the seasonal peak (found manually using the peak_season_offset() function):
  #peak <- 59
  if (scenarios_to_run$eir == 4) {
    peak <- 32
    start <- 1
  }
  if (scenarios_to_run$eir == 8) {
    peak <- 335
    start <- 0
  }
  if (scenarios_to_run$eir == 32) {
    peak <- 335
    start <- 0
  }
  # Assign some admin days around the peak
  admin_days <- c(-28, 0, 28, 56)

  # Create the distribution days for the SMC campagin (in this case - 4 times per year starting in the 5th year)
  smc_distribution_days <- rep((365 * seq(start, start + 4, by = 1)), each = length(admin_days)) + peak + rep(admin_days)

  # Create matrices of the SMC distribution days, coverages, and minimum and maximum ages of individuals targeted:
  exp$smc_days <- matrix(data = smc_distribution_days,
                         nrow = nrow(scenarios_to_run),
                         ncol = length(smc_distribution_days),
                         byrow = TRUE)
  exp$smc_coverages <- matrix(data = rep(unique(scenarios_to_run$smc_coverage), 2),
                              nrow = nrow(exp$smc_days),
                              ncol = ncol(exp$smc_days),
                              byrow = F)
  exp$smc_min_ages <- matrix(data = 3 * 30,
                             nrow = nrow(exp$smc_days),
                             ncol = ncol(exp$smc_days),
                             byrow = F)
  exp$smc_max_ages <- matrix(data = 59 * 30,
                             nrow = nrow(exp$smc_days),
                             ncol = ncol(exp$smc_days),
                             byrow = F)

  return(exp)

}


carrying_capacity <- function(parameters, parameter_table, index){
      simparams <- list()
      # Calibrate to the initial EIR (eirs unique to each model, based on which eir creates the high, medium and low prevalences required):
      simparams[[i]] <- set_equilibrium(parameters = parameters[[index]],
                                        init_EIR = parameter_table[index,]$transmission_intensity_malariasimulation)
      
      # Get the mosquito carrying capacity:
      mosquito_carrying_capacity <- get_init_carrying_capacity(parameters = simparams[[i]])
      
      # Parameterise the changes in mosquito population carrying capacity (for EIR step change):
      simparams[[i]] <- set_carrying_capacity(parameters = simparams[[i]], 
                                              timesteps = parameter_table[index,]$cc_timestep_malariasimulation, 
                                              carrying_capacity = matrix(parameter_table[index,]$cc_factor_malariasimulation, ncol = 1))
  return(simparams[[i]])
  }

infectious_clearance <- function(parameters, parameter_table, index) {
  assignInNamespace(x = "update_mass_drug_admin",
                    value = update_infectious_clearance,
                    pos = "package:malariasimulation")
  simparams <- list()
  simparams[[i]] <- set_equilibrium(parameters = parameters[[index]],
                                        init_EIR = parameter_table[index,]$transmission_intensity_malariasimulation)
  infectious_clearance_drug <- c(1, 0.051, 11.3, 0.1)
  simparams[[i]] <- set_drugs(simparams[[i]], drugs = list(infectious_clearance_drug))
  infcl_events <- parameter_table[index,]$infcl_timestep_malariasimulation
  infcl_coverage <- parameter_table[index,]$infcl_coverage
  simparams[[i]] <- set_mda(simparams[[i]], 
                           drug=4,
                           timesteps = infcl_events,
                           coverages = infcl_coverage,
                           min_ages = ((1/12)*365),
                           max_ages = 100*365)
  return(simparams[[i]])
}

update_infectious_clearance <- function(
    target,
    variables,
    parameters,
    timestep,
    drug
    )
{
  # If the target population is greater than 0:
  if (target$successfully_treated$size() > 0) {
    
    # Move clinical and detectable asymptomatic into treated
    clinical <- variables$state$get_index_of('D')
    asymptomatic <- variables$state$get_index_of('A')
    detectable <- malariasimulation:::calculate_asymptomatic_detectable(
      variables$state,
      variables$birth,
      variables$id,
      parameters,
      timestep
    )
    to_treated <- clinical$or(asymptomatic$and(detectable))$and(target$successfully_treated)
    
    # If antimalarial resistance is switched on, generate the vector of dts to update:
    if(parameters$antimalarial_resistance) {
      dt_update_vector <- target$dt_spc_combined[
        target$successfully_treated$copy()$and(to_treated)$to_vector()
      ]
    } else {
      dt_update_vector <- parameters$dt
    }
    
    # TODO: Alter this to make these individuals move to S
    # Move individuals who were clinical and asymptomatic detected to Treated
    malariasimulation:::update_infection(
      variables$state,
      'S',
      variables$infectivity,
      0,
      variables$progression_rates,
      0,
      to_treated
    )
    
    # Move everyone else (susceptible, subpatent, non-detected asymptomatic and treated) to susceptible
    other <- target$successfully_treated$copy()$and(to_treated$not(TRUE))
    if (other$size() > 0) {
      malariasimulation:::update_infection(
        variables$state,
        "S",
        variables$infectivity,
        0,
        variables$progression_rates,
        0,
        other
      )
    }
    
    # Update drug
    variables$drug$queue_update(drug, target$successfully_treated)
    variables$drug_time$queue_update(timestep, target$successfully_treated)
    
  }
  
  # Update liver stage drug effects
  if(any(parameters$drug_hypnozoite_efficacy > 0)){
    if(target$successfully_treated_hypnozoites$size() > 0){
      variables$hypnozoites$queue_update(0, target$successfully_treated_hypnozoites)
      variables$ls_drug$queue_update(drug, target$successfully_treated_hypnozoites)
      variables$ls_drug_time$queue_update(timestep, target$successfully_treated_hypnozoites)
    }
  }
}


