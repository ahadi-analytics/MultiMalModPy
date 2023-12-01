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

arguments <- commandArgs(trailingOnly= TRUE)
# Change the working directory:
setwd(arguments[1])

# Load the functions required:
for(i in 1:length(list.files(".", pattern = ".R"))) {
  source(list.files(".", pattern = ".R")[i])
}

# Get the number of days in each month (non leap year: 2023):
days_per_month <- days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months"))

# Load in the .csv of parameters as a data frame:
scenarios_to_run <- read.csv(file.path(arguments[2], paste0(arguments[3],'.csv')))
exp_setup_df <- read.csv(file.path(arguments[2], 'exp_setup_df.csv'))

exp <- list()
exp$job_directory <- exp_setup_df[exp_setup_df$parameter == 'job_directory', 'Value']
exp$sim_out_dir <- exp_setup_df[exp_setup_df$parameter == 'sim_out_dir', 'Value']
exp$pop_size <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'pop_size', 'Value'])
exp$burnin <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'burnin', 'Value'])
exp$monitoring_years <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'monitoring_years', 'Value'])
exp$start_year <- as.numeric(exp_setup_df[exp_setup_df$parameter == 'start_year', 'Value'])
exp$sim_start_year_ms <- exp$start_year# as.numeric(exp_setup_df[exp_setup_df$parameter == 'sim_start_year_ms', 'Value'])
exp$agebins <- exp_setup_df[exp_setup_df$parameter == 'agebins', 'Value']
exp$agebins <- as.numeric(unlist(strsplit(gsub("\\[|\\]", "", exp$agebins), ", ")))
exp$min_ages <- (round(c(0,exp$agebins[1:length(exp$agebins)-1])*365))+1
exp$min_ages[1] <- 0
exp$max_ages <- (round(exp$agebins *365))

# Store the min/max ages (days):
min_ages <- exp$min_ages 
max_ages <- exp$max_ages 

# Load the monthly seasonal EIRs to map seasonal rainfall to:
seasonal_eirs <- read_csv(arguments[5])

# Generate the approximate seasonal parameters required to generate similar seasonal rainfall profile
malsim_seasonal_coefficients <- get_seasonality_parameters(monthly_eirs = seasonal_eirs$EIR, midpoint_setting = "calendar")
# Store the seasonality coefficients in the malariasimulation experimental setup parameters list:
exp$g0 <- as.numeric(malsim_seasonal_coefficients$coefficients[1])
exp$g <- as.numeric(malsim_seasonal_coefficients$coefficients[2:4])
exp$h <- as.numeric(malsim_seasonal_coefficients$coefficients[5:7])
exp$floor <- as.numeric(malsim_seasonal_coefficients$floor)

# Run the simulations or load example:
simulation_outputs_raw <- run_simulations(exp = exp, parameter_table = scenarios_to_run)



# Run the post-processing function to create a list of monthly and annually aggregated outputs:
processed_malsim_outputs <- malsim_post_processing(simulation_outputs_raw = simulation_outputs_raw,
                                                   days_per_month = days_per_month,
                                                   exp=exp)

# Write the outputs to .csv's:
write_csv(x = processed_malsim_outputs, file = file.path(exp$job_directory, 'malsim_jobs', paste0("daily_",arguments[4],".csv")))