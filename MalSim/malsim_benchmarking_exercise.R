#--------------------------------------------------------------------------------------------------#
#----- malsimulation benchmarking workflow  -----#
#------------------------------------------------#

#--- README ---#
#--------------#

##' 
##' This script combines the input processing, simulation running and output processing steps
##' required to integrate malariasimulation into the ensemble modelling project benchmarking
##' exercise. The current iteration of the work flow allows us to run simulations from a .csv
##' input and convert the outputs into 2 data frames, stored in a single list, that contain 
##' summary metrics of interest in monthly and annual aggregations.
##' 

# Load in the requisite packages:
library(malariasimulation); library(malariaEquilibrium); library(lubridate)
library(dplyr); library(tibble); library(readr); library(umbrella)

arguments <- commandArgs(trailingOnly = TRUE)
# Change the working directory:
setwd(arguments[1])
job_directory = arguments[2]
scen_id = arguments[3]

# Load the functions required:
for (i in 1:length(list.files(".", pattern = ".R"))) {
  source(list.files(".", pattern = ".R")[i])
}

# Get the number of days in each month (non leap year: 2023):
days_per_month <- days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months"))

# Load in the .csv of parameters as a data frame:
scenarios_to_run <- read.csv(file.path(job_directory, 'scenarios_wseeds.csv'))
scenarios_to_run <- scenarios_to_run[scen_id,]
exp_setup_df <- read.csv(file.path(job_directory, 'exp_setup_df.csv'))

exp <- list()
exp$job_directory <- exp_setup_df[exp_setup_df$parameter == 'job_directory', 'Value']
exp$sim_out_dir <- exp_setup_df[exp_setup_df$parameter == 'sim_out_dir', 'Value']
exp$pop_size <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'pop_size', 'Value'])
exp$burnin <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'burnin', 'Value'])
exp$monitoring_years <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'monitoring_years', 'Value'])
exp$agebins <- exp_setup_df[exp_setup_df$parameter == 'agebins', 'Value']
exp$agebins <- as.numeric(unlist(strsplit(gsub("\\[|\\]", "", exp$agebins), ", ")))
exp$min_ages <- (round(c(0, exp$agebins[1:length(exp$agebins) - 1]) * 365)) + 1
exp$min_ages[1] <- 0
exp$max_ages <- (round(exp$agebins * 365))
exp$seasonality <- exp_setup_df[exp_setup_df$parameter == 'seasonality', 'Value'][1]
exp$monthly_eirs <- exp_setup_df[exp_setup_df$parameter == exp$seasonality, 'Value']
exp$monthly_eirs <- as.numeric(strsplit(exp$monthly_eirs, ';')[[1]])
#monthly <- exp$monthly_eirs[2:12] # we would want to do this if we want to match peak simulated EIR via inputs, not post processing
#monthly[[length(monthly)+1]] = exp$monthly_eirs[1]
#exp$monthly_eirs <- monthly
exp$intervention_list <- exp_setup_df[exp_setup_df$parameter =='intervention_list','Value']
exp$intervention_list <- data.frame(interventions = unlist(strsplit(gsub("\\[|\\]|\\'",'',exp$intervention_list),','))) #This helps make the python list readable in R
exp$intervention_list <- exp$intervention_list$interventions


# Store the min/max ages (days):
min_ages <- exp$min_ages
max_ages <- exp$max_ages

# Generate the approximate seasonal parameters required to generate similar seasonal rainfall profile
malsim_seasonal_coefficients <- get_seasonality_parameters(monthly_eirs = exp$monthly_eirs, midpoint_setting = "calendar")
# Store the seasonality coefficients in the malariasimulation experimental setup parameters list:
exp$g0 <- as.numeric(malsim_seasonal_coefficients$coefficients[1])
exp$g <- as.numeric(malsim_seasonal_coefficients$coefficients[2:4])
exp$h <- as.numeric(malsim_seasonal_coefficients$coefficients[5:7])
exp$floor <- as.numeric(malsim_seasonal_coefficients$floor)


if( length(exp$intervention_list)>0){
  print("Adding interventions to simulations...")
  source(file.path('define_interventions.R'))
  if ('smc' %in% exp$intervention_list){
    exp <- define_smc_param(exp, scenarios_to_run)
  }
  ## to be expanded with other interventions
}

# Run the simulations or load example:
print("Running the simulations...")
simulation_outputs_raw <- run_simulations(exp = exp, parameter_table = scenarios_to_run, write_raw_output = TRUE)
simulation_outputs_df <- simulation_outputs_raw[[2]][[1]]