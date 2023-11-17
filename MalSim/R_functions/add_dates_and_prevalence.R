add_dates_and_prevalence <- function(combined_output, days_per_month) {
  
  # Add month, dates, and prevalence columns to the data frame:
  combined_output %>%
    
    # Add a column with the month for each of the 365 days per year (from a non-leap year)
    add_column(month = rep(rep(rep(x = 1:12, days_per_month), max(combined_output$timestep)/365))) %>%
    # Add a column for the year of the simulation for each timestep - use floor with start year 0, to align with EMOD and OpenMalaria
    mutate(year = floor(timestep / 365)) %>%
    
    # Calculate the prevalences for each age-group and timestep
    mutate(prev_0_182 = n_detect_0_182/n_0_182,
           prev_183_365 = n_detect_183_365/n_183_365,
           prev_366_730 = n_detect_366_730/n_366_730,
           prev_731_1825 = n_detect_731_1825/n_731_1825,
           prev_1826_3650 = n_detect_1826_3650/n_1826_3650,
           prev_3651_5475 = n_detect_3651_5475/n_3651_5475,
           prev_5476_7300 = n_detect_5476_7300/n_5476_7300,
           prev_7301_36500 = n_detect_7301_36500/n_7301_36500,
           prev_730_3650 = n_detect_730_3650/n_730_3650) -> combined_output_dated
  # Return the modified data frame:
  return(combined_output_dated)
  
}