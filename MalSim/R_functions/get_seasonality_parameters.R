get_seasonality_parameters <- function(monthly_eirs) {
  
  # Generate the monthly midpoints:
  monthly_midpoints <- (0:11 * 30) + 15
  
  # Generate the Fourier coefficients:
  seasonality_parameters <- umbrella::fit_fourier(rainfall = monthly_eirs, t = monthly_midpoints)
  
  # Return the Fourier coefficients:
  return()
  
}
