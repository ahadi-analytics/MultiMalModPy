#----------------------------------------------------------------------------------------------------#
#----- malariasimulation  installation test                                                     -----#
#----------------------------------------------------------------------------------------------------#

message("Testing R installation and required malaria packages...")

# Load the requisite packages:
# Define required packages
required_packages <- c(
  "malariasimulation",
  "malariaEquilibrium",
  "lubridate",
  "dplyr",
  "tibble",
  "readr",
  "umbrella"
)

# Check and load each package
for (pkg in required_packages) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop(paste("Package not installed:", pkg))
  } else {
    library(pkg, character.only = TRUE)
    message(paste("Loaded:", pkg))
  }
}


# Try running a simple simulation
message("Running test simulation with malariasimulation...")

# Minimal test run
output <- run_simulation(100)

# Check output
if (!is.null(output) && is.data.frame(output)) {
  message("Simulation ran successfully and returned a data frame!")
} else {
  stop("Simulation failed or returned unexpected output.")
}

