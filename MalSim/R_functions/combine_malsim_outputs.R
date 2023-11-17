combine_malsim_outputs <- function(raw_malsim_outputs) {
  
  # Open a new data frame to store the combined malariasimulation outputs in:
  combined_malsim_outputs <- data.frame()
  # Loop through the raw outputs and append them to the combined data frame:
  for(i in seq(raw_malsim_outputs[[2]])) {
    combined_malsim_outputs <- bind_rows(combined_malsim_outputs, raw_malsim_outputs[[2]][[i]])
  }
  
  # Return the combined data frame as an output
  return(combined_malsim_outputs)
}