summarise_by_month <- function(output_long) {
  
  # Group by index, seed, month and age group, and then sum the incidences:
  output_long %>%
    group_by(index, seed, seasonality, eir, cm_clinical, year, month, ageGroup) %>%
    summarise(incidence = sum(incidence),
              clinical_incidence = sum(clinical_incidence),
              severe_incidence = sum(severe_incidence),
              prevalence_2to10 = mean(prevalence_2to10)) -> data_long_monthly
  
  # Return the long-format data summarised by month
  data_long_monthly
  
}