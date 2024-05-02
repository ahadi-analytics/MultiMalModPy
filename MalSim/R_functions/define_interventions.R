### Interventions

define_smc_param <- function(exp, scenarios_to_run) {
  # Find the seasonal peak (found manually using the peak_season_offset() function):
  #peak <- 59
  if (scenarios_to_run$eir == 4) {
    peak <- 32
    start <- 1
  }
  if (scenarios_to_run$eir == 8) {
    peak <- 335
    start <- 0
  }
  if (scenarios_to_run$eir == 32) {
    peak <- 335
    start <- 0
  }
  # Assign some admin days around the peak
  admin_days <- c(-28, 0, 28, 56)

  # Create the distribution days for the SMC campagin (in this case - 4 times per year starting in the 5th year)
  smc_distribution_days <- rep((365 * seq(start, start + 4, by = 1)), each = length(admin_days)) + peak +    rep(admin_days)

  # Create matrices of the SMC distribution days, coverages, and minimum and maximum ages of individuals targeted:
  exp$smc_days <- matrix(data = smc_distribution_days,
                         nrow = nrow(scenarios_to_run),
                         ncol = length(smc_distribution_days),
                         byrow = TRUE)
  exp$smc_coverages <- matrix(data = rep(unique(scenarios_to_run$smc_coverage), 2),
                              nrow = nrow(exp$smc_days),
                              ncol = ncol(exp$smc_days),
                              byrow = F)
  exp$smc_min_ages <- matrix(data = 3 * 30,
                             nrow = nrow(exp$smc_days),
                             ncol = ncol(exp$smc_days),
                             byrow = F)
  exp$smc_max_ages <- matrix(data = 59 * 30,
                             nrow = nrow(exp$smc_days),
                             ncol = ncol(exp$smc_days),
                             byrow = F)

  return(exp)

}