run_simulations <- function(timesteps, parameter_table) {
  
  # Open a list to store the simulation parameter lists in:
  simparams <- list()
  
  # Open a list to store the outputs in:
  simulation_outputs_list <- list()
  
  # Specify the min and max ages to render:
  #min_ages <- (seq(0, 15, by = 5) * 365) + 1; min_ages[1] <- 0
  #max_ages <- seq(5, 20, by = 5) * 365
  
  min_ages <- (round(c(0,0.5,1,2,5,10,15,20)*365))+1; min_ages[1] <- 0
  max_ages <- (round(c(0.5,1,2,5,10,15,20,100)*365))
  # Run through each row of the input dataframe, parameterise the model, and run the simulation:
  for(i in 1:nrow(parameter_table)) {
    
    # For rows with seasonal malaria:
    if(parameter_table[i,]$seasonality == "seasonal") {
      
      # Set "seasonal" seasonality profile 
      simparams[[i]] <- get_parameters(overrides = list(
        
        # Set the human population size (static)
        human_population = 10000,
        
        # Turn seasonality on and parameterise a seasonal rainfall pattern:
        model_seasonality = TRUE,
        g0 =  0.284596,
        g = c(-0.317878,-0.0017527,0.116455),
        h = c(-0.331361,0.293128,-0.0617547),
        
        # Average age of human population (affects demographic make-up)
        average_age = 23 * 365,
        
        # Render prevalence in age groups 0-5, 5-10, 10-15, and 15-20, and 2-10 (for PfPR_2-10)
        prevalence_rendering_min_ages = c(min_ages, (2*365)),    
        prevalence_rendering_max_ages = c(max_ages, (10*365)),
        
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
      
      # Append the parameters for artemether lumefantrine:
      simparams[[i]] <- set_drugs(parameters = simparams[[i]], drugs = list(AL_params))
      
      # Parameterise the clinical treatment
      simparams[[i]] <- set_clinical_treatment(parameters = simparams[[i]],
                                               drug = 1,
                                               timesteps = 1,
                                               coverages = parameter_table[i,]$cm_clinical)
      
      # Calibrate to the initial EIR:
      simparams[[i]] <- set_equilibrium(parameters = simparams[[i]], 
                                        init_EIR = parameter_table[i,]$eir)
      
      # Run the simulations:
      simulation_outputs_list[[i]] <- run_simulation(timesteps = timesteps, parameters = simparams[[i]])
      
      # Add simulation identifiers to the output data frame:
      simulation_outputs_list[[i]]$index <- parameter_table[i,]$index
      simulation_outputs_list[[i]]$eir <- parameter_table[i,]$eir
      simulation_outputs_list[[i]]$cm_clinical <- parameter_table[i,]$cm_clinical
      simulation_outputs_list[[i]]$seasonality  <- parameter_table[i,]$seasonality
      simulation_outputs_list[[i]]$seed <- parameter_table[i,]$seed
      
      # Print the function progress:
      print(paste0("Simulation ", i, " complete (", round(x = i/nrow(parameter_table)*100, digits = 3), "% complete)"))
      
      # For rows with perennial malaria:  
    } else if (parameter_table[i,]$seasonality == "perennial") {
      
      # Assign "perennial" (default) seasonality:
      simparams[[i]] <- get_parameters(overrides = list(
        
        # Set the human population size (static)
        human_population = 10000,
        
        # Average age of human population (affects demographic make-up)
        average_age = 23 * 365,
        
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
      
      # Append the parameters for artemether lumefantrine:
      simparams[[i]] <- set_drugs(parameters = simparams[[i]], drugs = list(AL_params))
      
      # Parameterise the clinical treatment
      simparams[[i]] <- set_clinical_treatment(parameters = simparams[[i]],
                                               drug = 1,
                                               timesteps = 1,
                                               coverages = parameter_table[i,]$cm_clinical)
      
      # Calibrate to the initial EIR:
      simparams[[i]] <- set_equilibrium(parameters = simparams[[i]], 
                                        init_EIR = parameter_table[i,]$eir)
      
      # Run the simulations:
      simulation_outputs_list[[i]] <- run_simulation(timesteps = timesteps, parameters = simparams[[i]])
      
      # Add simulation identifiers to the output data frame:
      simulation_outputs_list[[i]]$index <- parameter_table[i,]$index
      simulation_outputs_list[[i]]$eir_EIR <- parameter_table[i,]$eir
      simulation_outputs_list[[i]]$cm_clinical <- parameter_table[i,]$cm_clinical
      simulation_outputs_list[[i]]$seasonality  <- parameter_table[i,]$seasonality
      simulation_outputs_list[[i]]$seed <- parameter_table[i,]$seed
      
      # Print the function progress:
      print(paste0("Simulation ", i, " complete (", round(x = i/nrow(parameter_table)*100, digits = 3), "% complete)"))
      
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