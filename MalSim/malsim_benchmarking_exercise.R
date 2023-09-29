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
library(dplyr); library(tibble); library(readr)

arguments <- commandArgs(trailingOnly= TRUE)
# Change the working directory:
setwd(arguments[1])

# Load the functions required:
for(i in 1:length(list.files(".", pattern = ".R"))) {
  source(list.files(".", pattern = ".R")[i])
}

# Store the min/max ages (days):
  min_ages <- (round(c(0,0.5,1,2,5,10,15,20)*365))+1; min_ages[1] <- 0
  max_ages <- (round(c(0.5,1,2,5,10,15,20,100)*365))
# Get the number of days in each month (non leap year: 2023):
days_per_month <- days_in_month(seq(from = dmy("01-01-2023"), length.out = 12, by = "months"))


# Load in the .csv of parameters as a data frame:
scenarios_to_run <- read.csv(arguments[2])


# Store the number years to simulate:
years_to_simulate <- strtoi(arguments[3])



# Run the simulations or load example:
simulation_outputs_raw <- run_simulations(timesteps = (years_to_simulate * 365), parameter_table = scenarios_to_run)
#simulation_outputs_raw <- readRDS("../example/raw_run_simulations_outputs.rds")

# Run the post-processing function to create a list of monthly and annually aggregated outputs:
processed_malsim_outputs <- malsim_post_processing(simulation_outputs_raw = simulation_outputs_raw,
                                                   days_per_month = days_per_month,
                                                   min_ages = min_ages,
                                                   max_ages = max_ages)

# Write the outputs to .csv's:
write_csv(x = processed_malsim_outputs[[1]], file = sprintf("%s/daily.csv",arguments[4]))
write_csv(x = processed_malsim_outputs[[2]], file = sprintf("%s/mth.csv",arguments[4]))
write_csv(x = processed_malsim_outputs[[3]], file = sprintf("%s/yr.csv",arguments[4]))