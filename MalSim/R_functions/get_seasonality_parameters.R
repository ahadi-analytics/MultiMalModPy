get_seasonality_parameters <- function(monthly_eirs, midpoint_setting = "default") {
  
  if (midpoint_setting == "default") {
    
    # Generate the monthly midpoints:
    monthly_midpoints <- (0:11 * 30) + 15
    
    # Generate the Fourier coefficients:
    seasonality_parameters <- umbrella::fit_fourier(rainfall = monthly_eirs, t = monthly_midpoints)
    
    # Return the Fourier coefficients:
    return(seasonality_parameters)
    
  } else if (midpoint_setting == "calendar") {
    
    # Generate a vector of the days per calendar month in a non-leap year: 
    days_per_month <- as.numeric(days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months")))
    
    # Get the midpoint of each month by subtracting half the number of days from the cumulative sum of days:
    monthly_midpoints <- cumsum(days_per_month) - ceiling(days_per_month/2)
    
    # Generate the Fourier coefficients:
    seasonality_parameters <- umbrella::fit_fourier(rainfall = monthly_eirs, t = monthly_midpoints)
    
    # Return the Fourier coefficients:
    return(seasonality_parameters)
    
  } else {
    
    # Stop and return an error informing user that the seasonal parameter setting was not recognised
    stop("Error: seasonal parameter setting not recognised")
    
  }
}
