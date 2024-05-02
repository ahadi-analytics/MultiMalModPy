convert_malsim_to_long <- function(age_min, age_max, output) {
  
  # Convert the dataframe to long form for the desired columns:
  output <- lapply(
    seq_along(age_min),
    function(i) {
      data.frame(
        
        # Add columns containing the index, seed, initial EIR, case management coverage and
        # seasonality inputs/settings:
        index = output$index, # unique identifier across seeds & parameter sweep combinations
        seed = output$seed,
        smc_coverage = output$smc_coverage,

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
        # n: number of humans between an inclusive age range at this timestep.
        n = output[,paste0('n_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the prevalence per age group
        prev = output[,paste0('prev_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the incidence per age group:
        # n_inc: number of new infections for humans between an inclusive age range at this timestep.
        n_inc = output[,paste0('n_inc_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the clinical incidence per age group:
        # n_inc_clinical: number of new clinical infections for humans between an inclusive age range at this timestep.
        n_inc_clinical = output[,paste0('n_inc_clinical_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the severe incidence per age group:
        # n_inc_severe: number of new severe infections for humans between an inclusive age range at this timestep.
        n_inc_severe = output[,paste0('n_inc_severe_', age_min[[i]], '_',age_max[[i]])],
        
        # Add column for the prevalence in age groups 2-10 years old:
        prevalence_2to10 = output$prev_730_3650,

         # Add column for the amount of Infectious vectors present per age group.
        n_infectious_mos = output$Im_gamb_count,

        # Add column for the total amount of adult female mosquitos present per age group.
        n_total_mos_pop = output$Sm_gamb_count + output$Pm_gamb_count + output$Im_gamb_count, 

        # Add column for the EIR:
        EIR_gamb = output$EIR_gamb)  #FIXME when running with multiple or other vectors, will need to be adapted, perhaps add to exp object?

    }
  )
  
  # Bind the rows together:
  output <- do.call("rbind", output)
  
  # Return the long-form output:
  return(output)
}
