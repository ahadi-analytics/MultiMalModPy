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

  # FIXME for now custom age deography is hardcoded here
  demog_ages <- round(c(0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100) * 365)
  demog_age_distr <- c(0, 0.03474714994, 0.1276004028, 0.1452151394, 0.1275565434, 0.1083632373, 0.08393312454, 0.07001421452,
                       0.05800587654, 0.05102136612, 0.04182561874, 0.03339409351, 0.02986112356, 0.02555766582, 0.02332763433,
                       0.0177400255, 0.01008525491, 0.0074167341, 0.00271863401, 0.00161614642, 0)
  demog_deathrates <- c(1.041508e-06, 2.67249310936942e-05, 5.64575638098077e-05, 8.43861293688273e-05, 8.04462041187678e-05,
                        4.11082280836301e-05, 5.99345962817755e-05, 7.82474934107922e-05, 8.63178867406882e-05, 0.000183112406134931,
                        0.000119826997140995, 0.000115143595605931, 5.0933200098081e-05, 0.000132079859380879, 6.09432150860699e-05,
                        0.000390068518708017, 0.000419628839514507, 0.00072113681513871, 0.000833775339384449, 0.00107004264783245, 0.00107004264783245)


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

      # Define custom deaths rates to modify demography in alignment across models
      simparams[[i]] <- set_demography(
        parameters = simparams[[i]],
        agegroups = demog_ages,
        timesteps = 0,
        deathrates = matrix(demog_deathrates, nrow = 1)
      )

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

      if ("cc_step" %in% intervention_list){ 
        # Calibrate to the initial EIR (eirs unique to each model, based on which eir creates the high,
        # medium and low prevalences required):
        simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                        init_EIR = parameter_table[i,]$model_input_ms)
        # Get the mosquito carrying capacity:
        mosquito_carrying_capacity <- get_init_carrying_capacity(parameters = simparams[[i]])
        
        # Parameterise the changes in mosquito population carrying capacity (for EIR step change):
        simparams[[i]] <- set_carrying_capacity(parameters = simparams[[i]], 
                                                timesteps = parameter_table[i,]$cc_timestep_ms, 
                                                carrying_capacity = matrix(mosquito_carrying_capacity * 
                                                parameter_table[i,]$cc_factor_ms, ncol = 1))}
      else{
        # Calibrate to the initial EIR (same across models):
        simparams[[i]] <- set_equilibrium(parameters = simparams[[i]],
                                        init_EIR = parameter_table[i,]$model_input_ms)
      }
      
      # Run the simulations:
      simulation_outputs_list[[i]] <- run_simulation(timesteps = timesteps, parameters = simparams[[i]])

      # Add simulation identifiers to the output data frame:
      simulation_outputs_list[[i]]$index <- parameter_table[i,]$index
      simulation_outputs_list[[i]]$cm_clinical <- parameter_table[i,]$cm_clinical
      simulation_outputs_list[[i]]$seasonality  <- parameter_table[i,]$seasonality
      simulation_outputs_list[[i]]$seed <- parameter_table[i,]$seed

      if ("smc" %in% intervention_list){
        simulation_outputs_list[[i]]$input_target <- parameter_table[i,]$input_target
        simulation_outputs_list[[i]]$smc_coverage <- parameter_table[i,]$smc_coverage
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

      # Define custom deaths rates to modify demography in alignment across models
      simparams[[i]] <- set_demography(
        parameters = simparams[[i]],
        agegroups = demog_ages,
        timesteps = 0,
        deathrates = matrix(demog_deathrates, nrow = 1)
      )

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
                                                timesteps = parameter_table[i,]$cc_timestep_ms, 
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
