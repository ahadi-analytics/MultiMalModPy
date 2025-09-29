#' Get Seasonality Parameters
#' Computes Fourier coefficients to model seasonality from entomological inoculation rate (EIR) data.
#' The function supports both daily and monthly EIR timeframes and allows for different midpoint settings.
#'
#' @param eirs A numeric vector representing EIR values.
#'             If \code{timeframe} is "monthly", this should contain one value per month.
#'             If \code{timeframe} is "daily", this should contain one value per day.
#' @param timeframe A string indicating the timeframe of the \code{eirs} data. Accepted values are:
#'        \itemize{
#'          \item \code{"daily"}: EIR data is provided for each day of the year.
#'          \item \code{"monthly"}: EIR data is provided for each month of the year.
#'        }
#' @param midpoint_setting A string specifying how to calculate midpoints for the monthly timeframe.
#'        Accepted values are:
#'        \itemize{
#'          \item \code{"default"}: Midpoints are set to the 15th day of each month.
#'          \item \code{"calendar"}: Midpoints are calculated based on the exact day distribution of each month.
#'        }
#'
#' @return A list of Fourier coefficients that model the seasonality based on the provided EIR data.
#'
#' @export
get_seasonality_parameters <- function(eirs, timeframe, midpoint_setting = "default") {
  if (!timeframe %in% c("daily", "monthly")) {
    stop("EIR timeframe not from accepted values (daily or monthly")
  }
  if (!midpoint_setting %in% c("default", "calendar")) {
    stop("EIR timeframe not from accepted values (default or calendar")
  }
  # If the EIRs provided are on a monthly timeframe:
  if (timeframe == "monthly") {
    # If the default midpoint setting has been selected:
    if (midpoint_setting == "default") {
      # Generate the monthly midpoints:
      monthly_midpoints <- (0:11 * 30) + 15
      # Generate the Fourier coefficients:
      seasonality_parameters <- umbrella::fit_fourier(rainfall = eirs, t = monthly_midpoints)
      # Return the Fourier coefficients:
      return(seasonality_parameters)
    } else if (midpoint_setting == "calendar") {
      # Generate a vector of the days per calendar month in a non-leap year:
      days_per_month <- as.numeric(days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months")))
      # Get the midpoint of each month by subtracting half the number of days from the cumulative sum of days:
      monthly_midpoints <- cumsum(days_per_month) - ceiling(days_per_month / 2)
      # Generate the Fourier coefficients:
      seasonality_parameters <- umbrella::fit_fourier(rainfall = eirs, t = monthly_midpoints)
      # Return the Fourier coefficients:
      return(seasonality_parameters)
    }
  }
  # If the EIRs are provided on the daily timeframe:
  if (timeframe == "daily") {
    # Generate the Fourier coefficients:
    seasonality_parameters <- umbrella::fit_fourier(rainfall = eirs, t = 1:365)
    # Return the Fourier coefficients
    return(seasonality_parameters)
  }
}