### Interventions

include_interventions <- function(exp, parameters, parameter_table, intervention_list){
  #Include Carrying Capacity Perturbation
  simparams <- parameters
  if ("ccstep" %in% intervention_list){ 
    simparams <- carrying_capacity(parameters = simparams,
                                        parameter_table = parameter_table)
  } 

  #Include SMC - Currently not supported
  if ("smc" %in% intervention_list){
    exp <- define_smc_param(exp, parameter_table)
    simparams <- set_smc(parameters = simparams,
                              drug = 2,
                              timesteps = exp$smc_days,
                              coverages = exp$smc_coverages,
                              min_ages = exp$smc_min_ages,
                              max_ages = exp$smc_max_ages)
  }
  return(simparams)
}

include_intervention_outputs <- function(output_list, intervention_list, parameter_table){
  simulation_output <- output_list
  if ("smc" %in% intervention_list){
    simulation_output$smc_coverage <- parameter_table$smc_coverage
  }
  if ("ccstep" %in% intervention_list) {
    simulation_output$cc_factor_malariasimulation <- parameter_table$cc_factor_malariasimulation
    simulation_output$cc_timestep_malariasimulation <- parameter_table$cc_timestep_malariasimulation
    simulation_output$cc_title <- parameter_table$cc_title
  } 

  return(simulation_output)
}

carrying_capacity <- function(parameters, parameter_table){
  simparams <- parameters
  # Calibrate to the initial EIR (eirs unique to each model, based on which eir creates the high, medium and low prevalences required):
  simparams <- set_equilibrium(parameters = simparams,
                                    init_EIR = parameter_table$transmission_intensity_malariasimulation)
  
  # Get the mosquito carrying capacity:
  mosquito_carrying_capacity <- get_init_carrying_capacity(parameters = simparams)
  
  # Parameterise the changes in mosquito population carrying capacity (for EIR step change):
  simparams <- set_carrying_capacity(parameters = simparams, 
                                          timesteps = parameter_table$cc_timestep_malariasimulation, 
                                          carrying_capacity = matrix(parameter_table$cc_factor_malariasimulation, ncol = 1))
  return(simparams)
}


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
define_smc_param <- function(exp, parameter_table) {
  
  # Find the seasonal peak (found manually using the peak_season_offset() function):
  #peak <- 59
  if (parameter_table$transmission_intensity_malariasimulation == 4) {
    peak <- 32
    start <- 1
  }
  if (parameter_table$transmission_intensity_malariasimulation == 8) {
    peak <- 335
    start <- 0
  }
  if (scenarios_to_run$transmission_intensity_malariasimulation == 32) {
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
