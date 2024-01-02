summarise_by_month <- function(output_long) {

  # Group by index, seed, month and age group, and then sum the incidences:
  output_long %>%
    group_by(index, seed,year, month, ageGroup) %>%
    summarise(n_inc = sum(n_inc),
              n_inc_clinical = sum(n_inc_clinical),
              n_inc_severe = sum(n_inc_severe),
              prevalence_2to10 = mean(prevalence_2to10)) -> data_long_monthly

  # Return the long-format data summarised by month
  data_long_monthly
  
}