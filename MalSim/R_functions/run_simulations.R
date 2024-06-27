run_simulations <- function(exp, parameter_table, write_raw_output = TRUE) {

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
    # For rows with seasonal malaria:
    if(parameter_table[i,]$seasonality == "seasonal") {

      # Set "seasonal" seasonality profile 
      simparams[[i]] <- get_parameters(overrides = list(

        # Set the human population size
        human_population = exp$pop_size,

        # Turn seasonality on and parameterise a seasonal rainfall pattern:
        model_seasonality = TRUE,
        g0 = exp$g0, 
        g = exp$g,
        h = exp$h,
        rainfall_floor = exp$floor,

        # Average age of human population (affects demographic make-up)
        average_age = 21 * 365,

        # Render prevalence in age groups 0-5, 5-10, 10-15, and 15-20, and 2-10 (for PfPR_2-10)
        prevalence_rendering_min_ages = c(min_ages, (2*365)),
        prevalence_rendering_max_ages = c(max_ages, (10*365)),

        # Render incidence (n_inc) in age groups 0-5, 5-10, 10-15, and 15-20:
        incidence_rendering_min_ages = min_ages,
        incidence_rendering_max_ages = max_ages,

        # Render clinical incidence (n_inc_clinical) in age groups 0-5, 5-10, 10-15, and 15-20:
        clinical_incidence_rendering_min_ages = min_ages,
        clinical_incidence_rendering_max_ages = max_ages,

        # Render severe incidence (n_inc_severe) in age groups 0-5, 5-10, 10-15, and 15-20:
        severe_incidence_rendering_min_ages = min_ages,
        severe_incidence_rendering_max_ages = max_ages
      ))

      #Parameter Sweeping
      simparams[[i]] <- set_parameter_draw(parameters= simparams[[i]],
                                          draw = parameter_table[i,]$ms_pv)


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


      if ("cm" %in% intervention_list) {
        # Parameterise the clinical treatment
        simparams[[i]] <- set_clinical_treatment(parameters = simparams[[i]],
                                               drug = 1,
                                               timesteps = 1,
                                               coverages = parameter_table[i,]$cm_clinical)
      }

      if ("cc_step" %in% intervention_list){ 
        # Calibrate to the initial EIR (eirs unique to each model, based on which eir creates the high,
        # medium and low prevalences required):
        simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                        init_EIR = parameter_table[i,]$eir_malsim)
        # Get the mosquito carrying capacity:
        mosquito_carrying_capacity <- get_init_carrying_capacity(parameters = simparams[[i]])
        
        # Parameterise the changes in mosquito population carrying capacity (for EIR step change):
        simparams[[i]] <- set_carrying_capacity(parameters = simparams[[i]], 
                                                timesteps = parameter_table[i,]$eir_scalar_timestep_daily, 
                                                carrying_capacity = matrix(mosquito_carrying_capacity * 
                                                parameter_table[i,]$eir_scalar_malsim, ncol = 1))}
      else{
        # Calibrate to the initial EIR (same across models):
        simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                        init_EIR = parameter_table[i,]$eir)
      }
      
      # Run the simulations:
      simulation_outputs_list[[i]] <- run_simulation(timesteps = timesteps, parameters = simparams[[i]])

      # Add simulation identifiers to the output data frame:
      simulation_outputs_list[[i]]$index <- parameter_table[i,]$index
      simulation_outputs_list[[i]]$cm_clinical <- parameter_table[i,]$cm_clinical
      simulation_outputs_list[[i]]$seasonality  <- parameter_table[i,]$seasonality
      simulation_outputs_list[[i]]$seed <- parameter_table[i,]$seed

      if ("smc" %in% intervention_list){
        simulation_outputs_list[[i]]$eir <- parameter_table[i,]$eir
        simulation_outputs_list[[i]]$smc_coverage <- parameter_table[i,]$smc_coverage
      }

      if ("cc_step" %in% intervention_list) {
        simulation_outputs_list[[i]]$eir_malsim <- parameter_table[i,]$eir_malsim
        simulation_outputs_list[[i]]$eir_scalar_malsim <- parameter_table[i,]$eir_scalar_malsim
        simulation_outputs_list[[i]]$eir_scalar_timestep_daily <- parameter_table[i,]$eir_scalar_timestep_daily
        simulation_outputs_list[[i]]$carrying_capacity_step <- parameter_table[i,]$carrying_capacity_step}
      else{
        simulation_outputs_list[[i]]$eir <- parameter_table[i,]$eir
      }

      if (write_raw_output) {
        write_csv(simulation_outputs_list[[i]], file.path(exp$job_directory, 'malsim_jobs', paste0(parameter_table[i,]$index, '_out.csv')))
      }

      # Print the function progress:
      print(paste0("Simulation ", parameter_table[i,]$index, " complete (", round(x = i / nrow(parameter_table) * 100, digits = 3), "% complete)"))

      # For rows with perennial malaria:  
    } else if (parameter_table[i,]$seasonality == "perennial") {

      # Assign "perennial" (default) seasonality:
      simparams[[i]] <- get_parameters(overrides = list(

        # Set the human population size
        human_population = exp$pop_size,

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
      simparams[[i]] <- set_parameter_draw(parameters= simparams[[i]],
                                          draw = parameter_table[i,]$ms_pv)

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

      if ("cm" %in% intervention_list){
        # Parameterise the clinical treatment
        simparams[[i]] <- set_clinical_treatment(parameters = simparams[[i]],
                                               drug = 1,
                                               timesteps = 1,
                                               coverages = parameter_table[i,]$cm_clinical)
      }

      # Calibrate to the initial EIR:
      if ("cc_step" %in% intervention_list){ 
        # Calibrate to the initial EIR (eirs unique to each model, based on which eir creates the high, medium and low prevalences required):
        simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                        init_EIR = parameter_table[i,]$eir_malsim)
        # Get the mosquito carrying capacity:
        mosquito_carrying_capacity <- get_init_carrying_capacity(parameters = simparams[[i]])
        
        # Parameterise the changes in mosquito population carrying capacity (for EIR step change):
        simparams[[i]] <- set_carrying_capacity(parameters = simparams[[i]], 
                                                timesteps = parameter_table[i,]$eir_scalar_timestep_daily, 
                                                carrying_capacity = matrix(mosquito_carrying_capacity * parameter_table[i,]$eir_scalar_malsim, ncol = 1))}
      else{
        # Calibrate to the initial EIR (same across models):
        simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                        init_EIR = parameter_table[i,]$eir)}
      # Run the simulations:
      simulation_outputs_list[[i]] <- run_simulation(timesteps = timesteps, parameters = simparams[[i]])

      # Add simulation identifiers to the output data frame:
      simulation_outputs_list[[i]]$index <- parameter_table[i,]$index
      simulation_outputs_list[[i]]$cm_clinical <- parameter_table[i,]$cm_clinical
      simulation_outputs_list[[i]]$seasonality  <- parameter_table[i,]$seasonality
      simulation_outputs_list[[i]]$seed <- parameter_table[i,]$seed

      if ("smc" %in% intervention_list){
        simulation_outputs_list[[i]]$smc_coverage <- parameter_table[i,]$smc_coverage
        simulation_outputs_list[[i]]$eir <- parameter_table[i,]$eir
      }
      
      if ("cc_step" %in% intervention_list) {
        simulation_outputs_list[[i]]$eir_malsim <- parameter_table[i,]$eir_malsim
        simulation_outputs_list[[i]]$eir_scalar_malsim <- parameter_table[i,]$eir_scalar_malsim
        simulation_outputs_list[[i]]$eir_scalar_timestep_daily <- parameter_table[i,]$eir_scalar_timestep_daily
        simulation_outputs_list[[i]]$carrying_capacity_step <- parameter_table[i,]$carrying_capacity_step}
      else{
        simulation_outputs_list[[i]]$eir <- parameter_table[i,]$eir
      }
      
      if (write_raw_output) {
        write_csv(simulation_outputs_list[[i]], file.path(exp$job_directory, 'malsim_jobs', paste0(parameter_table[i,]$index, '_out.csv')))
      }

      # Print the function progress:
      print(paste0("Simulation ", parameter_table[i,]$index, " complete (", round(x = i / nrow(parameter_table) * 100, digits = 3), "% complete)"))

    } else {

      # Stop and return error if $seasonality input neither "perennial" or "seasonal":
      stop("Seasonal profile input not recognised, check scenarios input")

    }
  }

  # Create a list of the simulation parameters and simulation outputs to return:
  sim.out <- list(simparams, simulation_outputs_list)

  # Return the list:
  return(sim.out)

}
