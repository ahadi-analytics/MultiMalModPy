#----------------------------------------------------------------------------------------------------#
#----- malariasimulation   test run                                                             -----#
#----------------------------------------------------------------------------------------------------#

# Load the requisite packages:
library(malariasimulation); library(malariaEquilibrium); library(lubridate)
library(dplyr); library(tibble); library(readr); library(umbrella)

wdir <- file.path(getwd(), 'malariasimulation')

print(" Load the functions required and load experiment objects...")
rfiles <- list.files(file.path(wdir, 'functions'), pattern = ".R", full.names = T)
for (i in c(1:length(rfiles))) {
  source(rfiles[i])
}

# Get the number of days in each month (non leap year: 2023):
days_per_month <- days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months"))

# Load the .csv of parameters as a data frame:
nseeds = 3
parameter_table <- data.table::data.table(
  index = c(1:(3 * nseeds)),
  scen_id = rep(c(1, 2, 3), each = 3),
  target_output_values = rep(c(0.05, 0.05, 0.1), each = 3),
  seasonality = rep(c("perennial", "perennial", "perennial"), each = 3),
  num_seeds = rep(c(3, 3, 3), each = 3),
  cm_clinical = rep(c(0.0, 0.15, 0.0), each = 3),
  cm_severe = rep(c(0.0, 0.5, 0.0), each = 3),
  cm_start = rep(c(1, 1, 1), each = 3),
  transmission_intensity_malariasimulation = c(rep(c(0.3509239313694926), each = 3),
                                               rep(c(0.3959525409785984), each = 3),
                                               rep(c(0.8364897434821952), each = 3)),
  seed = rep(c(1, 2, 3), each = 3),
  malariasimulation_pv = rep(c(861.0, 466.0, 32.0), each = 3)
)

perennial_daily <- paste(rep("0.0027397260273972603", 365), collapse = "; ")
exp_setup_df <- data.table::data.table(
  Value = c("custom", "['target_output_values', 'case_management', 'seasonality']","5", "3", "500", "[0.5, 1, 2, 5, 10, 15, 20, 100]", "['perennial']", perennial_daily),
  parameter = c("run_mode", "sweep_list","burnin_malariasimulation", "monitoring_years", "pop_size_malariasimulation", "agebins", "seasonality", "perennial_daily")
)


exp <- list()
exp$job_directory <- file.path(getwd(), 'tests')
exp$output_directory <- file.path(getwd(), 'tests')
exp$pop_size <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'pop_size_malariasimulation', 'Value'])
exp$burnin <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'burnin_malariasimulation', 'Value'])
exp$monitoring_years <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'monitoring_years', 'Value'])
exp$agebins <- exp_setup_df[exp_setup_df$parameter == 'agebins', 'Value']
exp$agebins <- as.numeric(unlist(strsplit(gsub("\\[|\\]", "", exp$agebins), ", ")))
exp$min_ages <- (round(c(0, exp$agebins[1:length(exp$agebins) - 1]) * 365)) + 1
exp$min_ages[1] <- 0
exp$max_ages <- (round(exp$agebins * 365))
exp$intervention_list <- exp_setup_df[exp_setup_df$parameter == 'intervention_list', 'Value']
exp$intervention_list <- data.frame(interventions = unlist(strsplit(gsub("\\[|\\]|\\'", '', exp$intervention_list), ','))) #This helps make the python list readable in R
exp$intervention_list <- exp$intervention_list$interventions
exp$monthly_or_daily_eirs <- 'daily' # This will change so we can toggle between daily and monthly later

# Store the min/max ages (days):
min_ages <- exp$min_ages
max_ages <- exp$max_ages

if (length(exp$intervention_list) > 0) {
  print("Adding interventions to simulations...")
  source(file.path(wdir, 'functions', 'interventions.R'))
  if ('smc' %in% exp$intervention_list) {
    exp <- define_smc_param(exp, parameter_table)
  }
  ## to be expanded with other interventions
}

# Run the simulations or load example:
print("Running the simulations...")
dir.create(file.path(exp$job_directory, "malariasimulation_jobs"), showWarnings = FALSE, recursive = TRUE)
simulation_outputs_raw <- run_simulations(exp = exp, exp_setup_df = exp_setup_df, parameter_table = parameter_table[1,]) # run single simulation for testing

if (!is.null(simulation_outputs_raw) && is.data.frame(simulation_outputs_raw)) {
  message("Simulation ran successfully and returned a data frame!")
} else {
  stop("Simulation failed or returned unexpected output.")
}

