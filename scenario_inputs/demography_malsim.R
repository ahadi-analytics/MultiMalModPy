# Load the requisite packages:
library(malariasimulation)
# Set colour palette:
cols <- c("#E69F00", "#56B4E9", "#009E73", "#CC79A7", "#F0E442", "#0072B2", "#D55E00")


# Set the timespan over which to simulate
year <- 365; years <- 5; sim_length <- year * years

# Set an initial human population and initial entomological inoculation rate (EIR)
human_population <- 1000
starting_EIR <- 5

#dem_output <- convert_to_long(ages[1:length(ages)-1], ages[2:length(ages)], dem_output)

ages <- round(c(0.083333, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45,
                50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 200) * year)

# Set the age ranges (in days)
age_min <- ages[1:length(ages) - 1]
age_max <- ages[2:length(ages)]

# Use the get_parameters() function to establish the default simulation parameters, specifying
# age categories from 0-85 in 5 year intervals.
simparams <- get_parameters(
  list(
    human_population = human_population,
    age_group_rendering_min_ages = age_min,
    age_group_rendering_max_ages = age_max
  )
)

# Use set_equilibrium to tune the human and mosquito populations to those required for the
# defined EIR
simparams <- set_equilibrium(simparams, starting_EIR)


# Copy the simulation parameters as demography parameters:
dem_params <- simparams

# We can set our own custom demography:
ages <- round(c(0.083333, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45,
                50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 200) * year)

# Set deathrates for each age group (divide annual values by 365:
deathrates <- c(
  .4014834, .0583379, .0380348, .0395061, .0347255, .0240849, .0300902,
  .0357914, .0443123, .0604932, .0466799, .0426199, .0268332, .049361,
  .0234852, .0988317, .046755, .1638875, .1148753, .3409079, .2239224,
  .8338688) / 365

# Update the parameter list with the custom ages and death rates through the in-built
# set_demography() function, instructing the custom demography to be implemented at the
# beginning of the model run (timestep = 0):
dem_params <- set_demography(
  dem_params,
  agegroups = ages,
  timesteps = 0,
  deathrates = matrix(deathrates, nrow = 1)
)

# Confirm that the custom demography has been set:
dem_params$custom_demography
#> [1] TRUE


# Run the simulation with the default demographic set-up:
exp_output <- run_simulation(sim_length, simparams)
exp_output$run <- 'exponential'

# Run the simulation for the custom demographic set-up:
custom_output <- run_simulation(sim_length, dem_params)
custom_output$run <- 'custom'


# Combine the two dataframes:
dem_output <- rbind(exp_output, custom_output)

# Subset the final day of the simulation for each of the two demography runs:
dem_output <- dem_output[dem_output$timestep == 5 * 365,]

# Extract the age variables and convert the dataframe to long format:
convert_to_long <- function(age_min, age_max, output) {
  output <- lapply(
    seq_along(age_min),
    function(i) {
      data.frame(
        age_lower = age_min[[i]],
        age_upper = age_max[[i]],
        n = output[, paste0('n_age_', age_min[[i]], '_', age_max[[i]])],
        age_plot = age_min[[i]] / 365,
        run = output$run,
        timestep = output$timestep)
    }
  )
  output <- do.call("rbind", output)
}

# Convert the output for plotting:
dem_output <- convert_to_long(age_min, age_max, dem_output)

# Define the plotting window
par(mfrow = c(1, 2), mar = c(4, 4, 1, 1))

# a) Default/Exponentially-distributed demography
plot.new(); grid(lty = 2, col = "grey80", lwd = 0.5, ny = 5, nx = 6); par(new = TRUE)
barplot(height = dem_output[dem_output$run == "exponential", c("n", "age_plot")]$n,
        names = c(paste0(seq(0, 75, by = 5), "-", seq(0, 75, by = 5) + 4), "80+"),
        axes = TRUE, space = 0, ylim = c(0, 250), xaxs = "i", yaxs = "i",
        main = "Default", xlab = "Age Group", ylab = "Individuals",
        cex.axis = 0.8, cex.names = 0.8, cex.lab = 1, cex.main = 1, las = 2,
        col = cols[2]); box()

# b) Custom demography
plot.new()
grid(lty = 2, col = "grey80", lwd = 0.5, ny = 5, nx = 6)
par(new = TRUE)
barplot(height = dem_output[dem_output$run == "custom", c("n", "age_plot")]$n,
        names = c(paste0(seq(0, 75, by = 5), "-", seq(0, 75, by = 5) + 4), "80+"),
        axes = TRUE, space = 0, ylim = c(0, 250), xaxs = "i", yaxs = "i",
        main = "Custom", xlab = "Age Group",
        cex.axis = 0.8, cex.names = 0.8, cex.lab = 1, cex.main = 1, las = 2,
        col = cols[1]); box()


dem_output[dem_output$run == "custom", c("n", "age_plot")]$n
c(paste0(seq(0, 75, by = 5), "-", seq(0, 75, by = 5) + 4), "80+")

distr_n <- dem_output[dem_output$run == "custom", c("n", "age_plot")]$n
sum_n <- sum(distr_n)
distr_perc <- distr_n / sum_n

plot(distr_perc)
#####################


ages <- round(c(0.083333, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45,
                50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 200) * year)

# Hypothetical initial mortality rates
initial_mortality_rates <- deathrates

# Hypothetical initial age distribution
initial_age_distribution <- distr_perc

# Hypothetical number of births
births <- sum(initial_age_distribution)

# Hypothetical target age distribution
target_age_distribution <- c(0.03474714994, 0.13262988006, 0.14010559, 0.11721637,
                             0.09817686, 0.0821803, 0.06878903, 0.05755154, 0.04820319,
                             0.04034897, 0.03377461, 0.02825664, 0.02366712, 0.01981063, 0.01658272,
                             0.01387365, 0.01162009, 0.00972677, 0.00814181, 0.00681173, 0.00778533)


diffs <- target_age_distribution / initial_age_distribution
diffs <- ifelse(diffs == Inf, 1, diffs)
target_mortality_rates <- initial_mortality_rates * diffs


# Update the parameter list with the custom ages and death rates through the in-built
# set_demography() function, instructing the custom demography to be implemented at the
# beginning of the model run (timestep = 0):
dem_params2 <- set_demography(
  dem_params,
  agegroups = ages,
  timesteps = 0,
  deathrates = matrix(target_mortality_rates, nrow = 1)
)

# Confirm that the custom demography has been set:
dem_params2$custom_demography
#> [1] TRUE

# Run the simulation for the custom demographic set-up:
custom_output2 <- run_simulation(sim_length, dem_params2)
custom_output2$run <- 'custom2'
custom_output2 <- custom_output2[custom_output2$timestep == 5 * 365,]
dem_output2 <- convert_to_long(age_min, age_max, custom_output2)
distr_n2 <- dem_output2[dem_output2$run == "custom2", c("n", "age_plot")]$n
sum_n2 <- sum(distr_n2)
distr_perc2 <- distr_n2 / sum_n2

cbind(target_age_distribution, distr_perc2, deathrates, target_mortality_rates)

plot(target_age_distribution)
plot(distr_perc2)

