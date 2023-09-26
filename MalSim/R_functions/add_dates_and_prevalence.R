add_dates_and_prevalence <- function(combined_output, days_per_month) {
  
  # Add month, dates, and prevalence columns to the data frame:
  combined_output %>%
    
    # Add a column with the month for each of the 365 days per year (from a non-leap year)
    add_column(month = rep(rep(rep(x = 1:12, days_per_month), max(combined_output$timestep)/365), max(combined_output$index))) %>%
    
    # Add a column for the year of the simulation for each timestep
    mutate(year = ceiling(timestep / 365)) %>%
    
    # Calculate the prevalences for each age-group and timestep
    mutate(prev_0_1825 = n_detect_0_1825/n_0_1825,
           prev_1826_3650 = n_detect_1826_3650/n_1826_3650,
           prev_3651_5475 = n_detect_3651_5475/n_3651_5475,
           prev_5476_7300 = n_detect_5476_7300/n_5476_7300,
           prev_730_3650 = n_detect_730_3650/n_730_3650) -> combined_output_dated
  
  # Return the modified data frame:
  return(combined_output_dated)
  
}