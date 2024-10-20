
get_seasonality_parameters <- function(eirs, timeframe, midpoint_setting = "default") {
  if (!timeframe %in% c("daily", "monthly")) {
    stop("EIR timeframe not from accepted values (daily or monthly")
  }
  if (!midpoint_setting %in% c("default", "calendar")) {
    stop("EIR timeframe not from accepted values (default or calendar")
  }

  if (timeframe == "monthly") {

    if (midpoint_setting == "default") {
      monthly_midpoints <- (0:11 * 30) + 15
      seasonality_parameters <- umbrella::fit_fourier(rainfall = eirs, t = monthly_midpoints)
      return(seasonality_parameters)
    } else if (midpoint_setting == "calendar") {
      days_per_month <- as.numeric(days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months")))
      monthly_midpoints <- cumsum(days_per_month) - ceiling(days_per_month / 2)
      seasonality_parameters <- umbrella::fit_fourier(rainfall = eirs, t = monthly_midpoints)
      return(seasonality_parameters)
    }
  }
  if (timeframe == "daily") {
    seasonality_parameters <- umbrella::fit_fourier(rainfall = eirs, t = 1:365)
    return(seasonality_parameters)
  }
}