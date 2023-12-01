malsim_post_processing <- function(simulation_outputs_raw, days_per_month, exp, timeout = 'daily', write_test_outputs=FALSE) {

  min_ages <- exp$min_ages
  max_ages <- exp$max_ages
  # Combine the malariasimulation data frames from the raw outputs into a single data frame:
  combined_malsim_outputs <- combine_malsim_outputs(raw_malsim_outputs = simulation_outputs_raw)

  # Append columns for month, date, and prevalence (by age group):
  combined_malsim_outputs_modified <- add_dates_and_prevalence(combined_output = combined_malsim_outputs, days_per_month = days_per_month)

  # Create a long-form data frame with (some of - work in progress) the columns required aggregated
  # by age group:
  malsim_output_long_daily <- convert_malsim_to_long(age_min = min_ages, age_max = max_ages, output = combined_malsim_outputs_modified)
  malsim_output_long_daily$sim_year <- malsim_output_long_daily$year # years of simulation, starting at 0
  malsim_output_long_daily$year <- malsim_output_long_daily$sim_year + exp$sim_start_year # year in calendar time
  malsim_output_long_daily <- malsim_output_long_daily[malsim_output_long_daily$sim_year < exp$monitoring_years, ] # remove last year

  # Aggregate (some of) the outputs by month:
  if(timeout=='mth')malsim_output_long <- summarise_by_month(output_long = malsim_output_long_daily)

  # Aggregate (some of) the outputs by year:
  if(timeout=='yr')malsim_output_long <- summarise_by_year(output_long = malsim_output_long_daily)

  # Create a list containing the monthly and annually aggregated outputs
  if(timeout=='daily')malsim_output_long <- malsim_output_long_daily
  
  # Write .csv's to the current directory:
  if(write_test_outputs){
    write_csv(x = post_processing_outputs[[1]], file = "malsim_processed_outputs_daily_test.csv")
    write_csv(x = post_processing_outputs[[2]], file = "malsim_processed_outputs_monthly_test.csv")
    write_csv(x = post_processing_outputs[[3]], file = "malsim_processed_outputs_annually_test.csv")
  }

  # Return the output:
  return(malsim_output_long)

}




