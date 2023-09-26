convert_malsim_to_long <- function(age_min, age_max, output) {
  
  # Convert the dataframe to long form for the desired columns:
  output <- lapply(
    seq_along(age_min),
    function(i) {
      data.frame(
        
        # Add columns containing the index, seed, initial EIR, case management coverage and
        # seasonality inputs/settings:
        index = output$index,
        seed = output$seed,
        initial_EIR = output$initial_EIR,
        cm_clinical = output$cm_clinical,
        seasonality = output$seasonality,
        
        # Add columns for the timesteps (day, month, year)
        timestep = output$timestep,
        month = output$month,
        year = output$year,
        
        # Add column for the age group and age group bounds
        #ageGroup = age_max[[i]]/365,
        #ageGroup = paste0(floor(age_min[[i]]/365), '-', floor(age_max[[i]]/365), ";"),
        ageGroup = paste0(floor(age_min[[i]]/365), '-', floor(age_max[[i]]/365)),
        age_lower = age_min[[i]],
        age_upper = age_max[[i]],
        
        # Add columns for the total human population
        nPopulation = output$S_count + output$A_count + output$U_count + output$Tr_count + output$D_count,
        
        # Add column for the number of people per age group:
        nHost = output[,paste0('n_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the prevalence per age group
        prevalence = output[,paste0('prev_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the incidence per age group:
        incidence = output[,paste0('n_inc_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the clinical incidence per age group:
        clinical_incidence = output[,paste0('n_inc_clinical_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the severe incidence per age group:
        severe_incidence = output[,paste0('n_inc_severe_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the prevalence in age groups 2-10 years old:
        pfpr210 = output$prev_730_3650)
    }
  )
  
  # Bind the rows together:
  output <- do.call("rbind", output)
  
  # Return the long-form output:
  return(output)
}
