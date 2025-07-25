#' Run malariasimulation
#'
#' Defines and runs malariasimulation for multiple parameter sets, parameterizes models, applies interventions,
#' and outputs results.
#'
#' @param exp A list containing experiment settings, including burn-in period, monitoring years,
#'        population size, intervention lists, and more.
#' @param exp_setup_df A data frame containing experimental setup details, such as EIR values
#'        associated with seasonality profiles.
#' @param parameter_table A data frame where each row specifies simulation parameters, including:
#'        \itemize{
#'          \item \code{seed}: Random seed for reproducibility.
#'          \item \code{seasonality}: Seasonality type (e.g., perennial, seasonal).
#'          \item \code{cm_clinical}: Clinical coverage values.
#'          \item \code{transmission_intensity_malariasimulation}: EIR input values for simulations.
#'          \item Additional columns depending on the interventions.
#'        }
#' @param write_raw_output Logical. If \code{TRUE}, writes raw output CSV files for each simulation
#'        to the specified directory.
#'
#' @return A list containing:
#' \itemize{
#'   \item Simulation parameter objects for each run.
#'   \item Simulation output data for each run.
#' }
#'
#' @export
run_simulations <- function(exp, exp_setup_df, parameter_table) {
  
  #-------------------------
  # 1. Define simulation
  #-------------------------
  # Open a list to store the simulation parameter lists in:
  simparams <- list()
  final_simulation_parameters <- list()
  # Open a list to store the outputs in:
  simulation_output <- list()
  
  # Specify the min and max ages to render:
  min_ages <- exp$min_ages
  max_ages <- exp$max_ages
  timesteps <- (exp$burnin + exp$monitoring_years) * 365
  intervention_list <- exp$intervention_list
  # Parameterise the model, and run the simulation:
  set.seed(seed = parameter_table$seed)
  exp$seasonality <- parameter_table$seasonality
  if (exp$seasonality != 'perennial'){
    exp$model_seasonality = TRUE
  } else {
    exp$model_seasonality = FALSE
  }
  if (exp$monthly_or_daily_eirs == "monthly"){
    exp$eirs <- exp_setup_df[exp_setup_df$parameter == paste(exp$seasonality,'_monthly',sep=""), 'Value']
    exp$eirs <- as.numeric(strsplit(exp$eirs, ';')[[1]])
    exp$eirs <- c(exp$eirs[2:12], exp$eirs[1])
  }
  if (exp$monthly_or_daily_eirs == "daily"){
    exp$eirs <- exp_setup_df[exp_setup_df$parameter == paste(exp$seasonality,'_','daily',sep=""), 'Value']
    exp$eirs <- as.numeric(strsplit(exp$eirs, ';')[[1]])
    exp$eirs <- c(exp$eirs[-(1:45)], exp$eirs[1:45])
  }
  # Generate the approximate seasonal parameters required to generate similar seasonal rainfall profile
  seasonal_coefficients <- get_seasonality_parameters(eirs = exp$eirs, timeframe = exp$monthly_or_daily_eirs)
  # Store the seasonality coefficients in the malariasimulation experimental setup parameters list:
  exp$g0 <- as.numeric(seasonal_coefficients$coefficients[1])
  exp$g <- as.numeric(seasonal_coefficients$coefficients[2:4])
  exp$h <- as.numeric(seasonal_coefficients$coefficients[5:7])
  exp$floor <- as.numeric(seasonal_coefficients$floor)
  
  # Assign seasonality:
  simparams <- get_parameters(overrides = list(
    # Set the human population size
    human_population = exp$pop_size,
    
    # Set the seasonal profile
    model_seasonality = exp$model_seasonality,
    g0 = exp$g0, 
    g = exp$g,
    h = exp$h,
    rainfall_floor = exp$floor,
    
    # Average age of human population (affects demographic make-up)
    #average_age = 23.32067006 * 365, #average age of OpenMalaria's input age demography
    average_age = 26 * 365, # average age that looked closer to OM's input age demography.
    # Render prevalence in age groups 0-5, 5-10, 10-15, and 15-20, and 2-10 (for PfPR_2-10)
    prevalence_rendering_min_ages = c(min_ages, (2 * 365)),
    prevalence_rendering_max_ages = c(max_ages, (10 * 365)),
    
    # Render incidence in age groups 0-5, 5-10, 10-15, and 15-20:
    incidence_rendering_min_ages = min_ages,
    incidence_rendering_max_ages = max_ages,
    
    # Render clinical incidence in age groups 0-5, 5-10, 10-15, and 15-20:
    clinical_incidence_rendering_min_ages = min_ages,
    clinical_incidence_rendering_max_ages = max_ages,
    
    # Render severe incidence in age groups 0-5, 5-10, 10-15, and 15-20:
    severe_incidence_rendering_min_ages = min_ages,
    severe_incidence_rendering_max_ages = max_ages
  ))
  
  # Parameter Sweeping
  if ("malariasimulation_pv" %in% colnames(parameter_table)){
    simparams <- set_parameter_draw(parameters = simparams,
                                    draw = parameter_table$malariasimulation_pv)
  }
  
  # Append the parameters for artemether lumefantrine:
  simparams <- set_drugs(parameters = simparams, drugs = list(AL_params, SP_AQ_params, DHA_PQP_params))

  # Parameterise the clinical treatment
  simparams <- set_clinical_treatment(parameters = simparams,
                                           drug = 1,
                                           timesteps = 1,
                                           coverages = parameter_table$cm_clinical)
  print(simparams)
  # Include interventions and calibrate to the initial EIR:
  if (length(intervention_list) > 0){
    simparams <- include_interventions(exp = exp,
                          parameters = simparams,
                          parameter_table = parameter_table,
                          intervention_list = intervention_list)
  } else{
    # Calibrate to the initial EIR (same across models):
    simparams <- set_equilibrium(parameters = simparams,
                                      init_EIR = parameter_table$transmission_intensity_malariasimulation)
  }
  
  
  #-------------------------
  # 2. Run simulations:
  #-------------------------
  final_simulation_parameters[[1]] <- simparams
  simulation_output <- run_simulation(timesteps = timesteps, parameters = final_simulation_parameters[[1]])
  
  # Add simulation identifiers to the output data frame:
  simulation_output$index <- parameter_table$index
  simulation_output$cm_clinical <- parameter_table$cm_clinical
  simulation_output$seasonality  <- parameter_table$seasonality
  simulation_output$seed <- parameter_table$seed
  simulation_output$transmission_intensity_malariasimulation <- parameter_table$transmission_intensity_malariasimulation
  if (length(intervention_list) > 0){
  simulation_output <- include_intervention_outputs(output_list = simulation_output,
                                                    intervention_list = intervention_list,
                                                    parameter_table = parameter_table)
  } 
  # When running simulation scenarios in parallel as on HPC, those always need to be saved, part of the framework
  # If run as a standalone and all simulations scenarios as part of the for loop, this would not be needed.
  write_csv(simulation_output, file.path(exp$job_directory, 'malariasimulation_jobs', paste0(parameter_table$index, '_out.csv')))
  
  # Print the function progress:
  print(paste0("Simulation ", parameter_table$index, " complete (", round(x = i / nrow(parameter_table) * 100, digits = 3), "% complete)"))
  
  
  
  # Create a list of the simulation parameters and simulation outputs to return:
  sim.out <- list(simparams, simulation_output)
  
  # Return the list:
  return(sim.out)
  
}
