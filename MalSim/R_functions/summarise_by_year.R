summarise_by_year <- function(output_long) {
  
  # Group by index, seed, year and age group, and then sum the incidences:
  output_long %>%
    group_by(index, seed, seasonality, eir, cm_clinical, year, ageGroup) %>%
    summarise(incidence = sum(incidence),
              clinical_incidence = sum(clinical_incidence),
              severe_incidence = sum(severe_incidence),
              prevalence_2to10 = mean(prevalence_2to10)) -> data_long_annual
  
  # Return the long-format data summarised by month
  data_long_annual
  
}