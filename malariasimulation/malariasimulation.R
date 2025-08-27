#----------------------------------------------------------------------------------------------------#
#----- malariasimulation                                                                        -----#
#----------------------------------------------------------------------------------------------------#
##'
##' This script combines the input processing, simulation running and output processing steps
##' required to integrate malariasimulation into the MultiMalModPy framework. 
##' The current iteration of the work flow allows us to run simulations from a .csv
##' input and convert the outputs into 2 data frames, stored in a single list, that contain 
##' summary metrics of interest in monthly and annual aggregations.
##' 

# Load the requisite packages:
library(malariasimulation); library(malariaEquilibrium); library(lubridate)
library(dplyr); library(tibble); library(readr); library(umbrella)


# Parse arguments
arguments <- commandArgs(trailingOnly = TRUE)
wdir <- arguments[1]  # getwd()
job_directory <- arguments[2]
scen_id <- arguments[3]  


print(" Load the functions required and load experiment objects...")
rfiles <- list.files(file.path(wdir,'functions'),  pattern = ".R", full.names = T)
for (i in c(1:length(rfiles))) {
  source(rfiles[i])
}

# Get the number of days in each month (non leap year: 2023):
days_per_month <- days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months"))


# Load the .csv of parameters as a data frame:
parameter_table <- read.csv(file.path(job_directory, 'scenarios_wseeds_mpv.csv'))
parameter_table <- parameter_table[scen_id,]
exp_setup_df <- read.csv(file.path(job_directory, 'exp_setup_df.csv'))


exp <- list()
exp$malariasimulation_parameter_variation <- tolower(exp_setup_df[exp_setup_df$parameter == 'malariasimulation_parameter_variation', 'Value'])
exp$job_directory <- exp_setup_df[exp_setup_df$parameter == 'job_directory', 'Value']
exp$output_directory <- exp_setup_df[exp_setup_df$parameter == 'output_directory', 'Value']
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

if (length(exp$intervention_list) > 0) {
  print("Adding interventions to simulations...")
  source(file.path(wdir, 'functions', 'interventions.R'))



# Run the simulations:
print("Running the simulations...")
run_simulations(exp = exp, exp_setup_df = exp_setup_df, parameter_table = parameter_table)
