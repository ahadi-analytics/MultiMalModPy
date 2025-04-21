
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

  # Open a list to store the outputs in:
  simulation_outputs_list <- list()

  # Specify the min and max ages to render:
  min_ages <- exp$min_ages
  max_ages <- exp$max_ages
  timesteps <- (exp$burnin + exp$monitoring_years) * 365
  intervention_list <- exp$intervention_list

  # Run through each row of the input dataframe, parameterise the model, and run the simulation:
  for(i in 1:nrow(parameter_table)) {
    set.seed(seed = parameter_table[i,]$seed)
    
    exp$seasonality <- parameter_table[i,]$seasonality
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
    simparams[[i]] <- get_parameters(overrides = list(

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
    simparams[[i]] <- set_parameter_draw(parameters= simparams[[i]],
                                        draw = parameter_table[i,]$malariasimulation_pv)
    }

    # Append the parameters for artemether lumefantrine:
    simparams[[i]] <- set_drugs(parameters = simparams[[i]], drugs = list(AL_params, SP_AQ_params, DHA_PQP_params))

    if ("smc" %in% intervention_list){
      simparams[[i]] <- set_smc(parameters = simparams[[i]],
                                drug = 2,
                                timesteps = exp$smc_days[i,],
                                coverages = exp$smc_coverages[i,],
                                min_ages = exp$smc_min_ages[i,],
                                max_ages = exp$smc_max_ages[i,])
    }

    # Parameterise the clinical treatment
    simparams[[i]] <- set_clinical_treatment(parameters = simparams[[i]],
                                            drug = 1,
                                            timesteps = 1,
                                            coverages = parameter_table[i,]$cm_clinical)

    # Calibrate to the initial EIR:
    if ("ccstep" %in% intervention_list){ 
      simparams[[i]] <- carrying_capacity(parameters = simparams,
                                          parameter_table = parameter_table,
                                          index = i)
      } else{
      # Calibrate to the initial EIR (same across models):
      simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                      init_EIR = parameter_table[i,]$transmission_intensity_malariasimulation)
      }
    if ("infcl" %in% intervention_list){
      simparams[[i]] <- infectious_clearance(parameters = simparams,
                            parameter_table = parameter_table,
                            index = i)
    } else{
      simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                        init_EIR = parameter_table[i,]$transmission_intensity_malariasimulation)
    }


    #-------------------------
    # 2. Run simulations:
    #-------------------------
    simulation_outputs_list[[i]] <- run_simulation(timesteps = timesteps, parameters = simparams[[i]])

    # Add simulation identifiers to the output data frame:
    simulation_outputs_list[[i]]$index <- parameter_table[i,]$index
    simulation_outputs_list[[i]]$cm_clinical <- parameter_table[i,]$cm_clinical
    simulation_outputs_list[[i]]$seasonality  <- parameter_table[i,]$seasonality
    simulation_outputs_list[[i]]$seed <- parameter_table[i,]$seed

    if ("smc" %in% intervention_list){
      simulation_outputs_list[[i]]$smc_coverage <- parameter_table[i,]$smc_coverage
      simulation_outputs_list[[i]]$input_target <- parameter_table[i,]$input_target
    }
    
    if ("ccstep" %in% intervention_list) {
      simulation_outputs_list[[i]]$transmission_intensity_malariasimulation <- parameter_table[i,]$transmission_intensity_malariasimulation
      simulation_outputs_list[[i]]$cc_factor_malariasimulation <- parameter_table[i,]$cc_factor_malariasimulation
      simulation_outputs_list[[i]]$cc_timestep_malariasimulation <- parameter_table[i,]$cc_timestep_malariasimulation
      simulation_outputs_list[[i]]$cc_title <- parameter_table[i,]$cc_title
      } else{
        simulation_outputs_list[[i]]$input_target <- parameter_table[i,]$input_target
      }
    if ("infcl" %in% intervention_list) {
      simulation_outputs_list[[i]]$transmission_intensity_malariasimulation <- parameter_table[i,]$transmission_intensity_malariasimulation
      simulation_outputs_list[[i]]$infcl_coverage <- parameter_table[i,]$infcl_coverage
      simulation_outputs_list[[i]]$infcl_timestep_malariasimulation <- parameter_table[i,]$infcl_timestep_malariasimulation
    }

    # When running simulation scenarios in parallel as on HPC, those always need to be saved, part of the framework
    # If run as a standalone and all simulations scenarios as part of the for loop, this would not be needed.
    write_csv(simulation_outputs_list[[i]], file.path(exp$job_directory, 'malariasimulation_jobs', paste0(parameter_table[i,]$index, '_out.csv')))

    # Print the function progress:
    print(paste0("Simulation ", parameter_table[i,]$index, " complete (", round(x = i / nrow(parameter_table) * 100, digits = 3), "% complete)"))

  } 

  # Create a list of the simulation parameters and simulation outputs to return:
  sim.out <- list(simparams, simulation_outputs_list)

  # Return the list:
  return(sim.out)

}
