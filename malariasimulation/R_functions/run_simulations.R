run_simulations <- function(exp, exp_setup_df, parameter_table, write_raw_output = TRUE) {

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
    }
    else {
      exp$model_seasonality = FALSE
    }
    exp$monthly_or_daily_eirs <- 'daily' # This will change so we can toggle between daily and monthly later
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
    seasonal_coefficients <- get_seasonality_parameters(eirs = exp$eirs, timeframe = 'daily')
    # Store the seasonality coefficients in the malariasimulation experimental setup parameters list:
    exp$g0 <- as.numeric(seasonal_coefficients$coefficients[1])
    exp$g <- as.numeric(seasonal_coefficients$coefficients[2:4])
    exp$h <- as.numeric(seasonal_coefficients$coefficients[5:7])
    exp$floor <- as.numeric(seasonal_coefficients$floor)

    # Assign "perennial" (default) seasonality:
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
      average_age = 21 * 365,

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

    #Parameter Sweeping
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
    if ("cc_step" %in% intervention_list){ 
      # Calibrate to the initial EIR (eirs unique to each model, based on which eir creates the high, medium and low prevalences required):
      simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                      init_EIR = parameter_table[i,]$model_input_malariasimulation)
      # Get the mosquito carrying capacity:
      mosquito_carrying_capacity <- get_init_carrying_capacity(parameters = simparams[[i]])
      
      # Parameterise the changes in mosquito population carrying capacity (for EIR step change):
      simparams[[i]] <- set_carrying_capacity(parameters = simparams[[i]], 
                                              timesteps = parameter_table[i,]$cc_timestep_malariasimulation, 
                                              carrying_capacity = matrix(mosquito_carrying_capacity * parameter_table[i,]$cc_factor_malariasimulation, ncol = 1))}
    else{
      # Calibrate to the initial EIR (same across models):
      simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                      init_EIR = parameter_table[i,]$model_input_malariasimulation)}
    # Run the simulations:
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
    
    if ("cc_step" %in% intervention_list) {
      simulation_outputs_list[[i]]$model_input_malariasimulation <- parameter_table[i,]$model_input_malariasimulation
      simulation_outputs_list[[i]]$cc_factor_malariasimulation <- parameter_table[i,]$cc_factor_malariasimulation
      simulation_outputs_list[[i]]$cc_timestep_malariasimulation <- parameter_table[i,]$cc_timestep_malariasimulation
      simulation_outputs_list[[i]]$cc_title <- parameter_table[i,]$cc_title}
    else{
      simulation_outputs_list[[i]]$input_target <- parameter_table[i,]$input_target
    }
    
    if (write_raw_output) {
      write_csv(simulation_outputs_list[[i]], file.path(exp$job_directory, 'malariasimulation_jobs', paste0(parameter_table[i,]$index, '_out.csv')))
    }

    # Print the function progress:
    print(paste0("Simulation ", parameter_table[i,]$index, " complete (", round(x = i / nrow(parameter_table) * 100, digits = 3), "% complete)"))

  } 

  # Create a list of the simulation parameters and simulation outputs to return:
  sim.out <- list(simparams, simulation_outputs_list)

  # Return the list:
  return(sim.out)

}
