library(jsonlite)
library(dplyr)
library(stringr)
library(readr)
library(malariasimulation)
library(ggplot2)
library(ggpubr) # ggarrange with shared legend

## -------- Define colors
models <- c('EMOD', 'malariasimulation', 'OpenMalaria')
custom_colors <- c('#1a9e77', '#7a5c9f', '#e97926')
model_cols <- setNames(custom_colors, models)


## -------- Define custom functions to extract age demographics per model
get_openmalaria_demog_from_txt <- function(age_snippet = 'age_demography.txt') {

  file_path <- file.path(getwd(), 'OpenMalaria', 'snippets', age_snippet)
  lines <- read_lines(file_path)

  lower_age <- 0
  data <- list()

  for (line in lines) {

    match <- str_match(line, 'poppercent="([\\d\\.]+)".*?upperbound="([\\d\\.]+)"')

    if (!is.na(match[1, 2])) {
      pop_percent <- as.numeric(match[1, 2])
      upper_bound <- as.numeric(match[1, 3])

      data[[length(data) + 1]] <- data.frame(lower_age = lower_age,
                                             upper_age = upper_bound,
                                             age_range = paste0(as.character(lower_age), "-", as.character(upper_bound)),
                                             population_percent = pop_percent)
      lower_age <- upper_bound
    }
  }

  df_om <- bind_rows(data)
  df_om <- df_om %>%
    mutate(cumulative_percent = cumsum(population_percent))

  return(df_om)

}

get_emod_demog_from_json <- function(json_file = 'demographics.json') {

  file_path <- file.path(getwd(), 'EMOD', 'inputs', json_file)
  data <- fromJSON(file_path)

  dist <- data$
    Defaults$
    IndividualAttributes$
    AgeDistribution
  ages <- unlist(dist$ResultValues)
  cum_probs <- unlist(dist$DistributionValues)
  age_specific_probs <- c(cum_probs[1], diff(cum_probs))

  df_emod <- data.frame(
    age_days = ages,
    cumulative_probability = cum_probs,
    age_specific_probability = age_specific_probs) %>%
    mutate(age_years = age_days / 365)

  return(df_emod)

}

get_malariasimulation_demog_from_sim <- function(pop_size = 50000, average_age = 26, years = 100, starting_EIR = 5, agebins = NULL) {

  if (is.null(agebins))agebins <- c(0.5, 1, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100.0)
  agebins <- sort(agebins)
  year <- 365
  timesteps <- year * years

  min_ages <- unique(c(0, agebins[1:length(agebins) - 1]) * 365)
  max_ages <- unique(agebins[1:length(agebins)] * 365)

  simparams_default <- get_parameters(overrides = list(
    age_group_rendering_min_ages = min_ages,
    age_group_rendering_max_ages = max_ages
  ))

  simparams_simple <- get_parameters(overrides = list(
    human_population = pop_size,
    average_age = average_age,
    age_group_rendering_min_ages = min_ages,
    age_group_rendering_max_ages = max_ages
  ))

  simparams_default <- set_equilibrium(simparams_default, starting_EIR)
  out_default <- run_simulation(timesteps, parameters = simparams_default)
  out_default$run <- 'default'

  simparams_simple <- set_equilibrium(simparams_simple, starting_EIR)
  out_raw <- run_simulation(timesteps = timesteps, parameters = simparams_simple)
  out_raw$run <- 'MMMPy'

  dem_output <- rbind(out_default, out_raw)
  dem_output <- dem_output[dem_output$timestep == years * 365,]

  # Requires 2 rows in a dataframe
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
  out <- convert_to_long(min_ages, max_ages, dem_output)

  df_malariasimulation <- out %>%
    filter(run == 'default') %>%
    mutate(ntotal = sum(n),
           perc = n / ntotal,
           age_years = age_upper / 365,
           cum_perc = cumsum(perc)) %>%
    select(age_upper, age_years, perc, cum_perc)

  return(df_malariasimulation)

}

combine_age_demogs <- function(df_om, df_emod, df_malariasimulation, agebins) {

  find_age_bin <- function(age_years, upper_bounds, include_upper_age = TRUE) {
    upper_bounds <- sort(unique(upper_bounds))
    lower_bounds <- c(0, head(upper_bounds, -1))
    labels <- paste0(lower_bounds, "-", upper_bounds)

    cut(age_years,
        breaks = c(lower_bounds, Inf),
        labels = labels,
        right = include_upper_age,
        include.lowest = TRUE)
  }

  df_emod$age_group <- find_age_bin(df_emod$age_years, agebins)
  df_malariasimulation$age_group <- find_age_bin(df_malariasimulation$age_years, agebins)

  df_om$age_group <- find_age_bin(df_om$upper_age, agebins)

  df_emod_grouped <- df_emod %>%
    group_by(age_group) %>%
    summarise(value_age_specific = sum(age_specific_probability),
              value_cumulative = max(cumulative_probability), .groups = "drop") %>%
    mutate(model = "EMOD")

  df_malariasimulation_grouped <- df_malariasimulation %>%
    group_by(age_group) %>%
    summarise(value_age_specific = sum(perc),
              value_cumulative = max(cum_perc), .groups = "drop") %>%
    mutate(model = "malariasimulation")

  df_om_grouped <- df_om %>%
    group_by(age_group) %>%
    summarise(value_age_specific = sum(population_percent / 100),
              value_cumulative = max(cumulative_percent / 100), .groups = "drop") %>%
    mutate(model = "OpenMalaria")


  df_plot <- bind_rows(df_emod_grouped, df_om_grouped, df_malariasimulation_grouped) %>%
    tidyr::separate(age_group, into = c("lower_age", "upper_age"), sep = "-", convert = TRUE, remove = FALSE)


  return(df_plot)
}


## -------- Run script
fine_agebins <- c(5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 100.0)
#simple_agebins <- c(5, 10, 15, 20, 100)

df_om <- get_openmalaria_demog_from_txt()
df_emod <- get_emod_demog_from_json()
df_malariasimulation <- get_malariasimulation_demog_from_sim()
#data.table::fwrite(df_malariasimulation,file.path(getwd(), 'plotter', "df_malariasimulation.csv"))

df_plot <- combine_age_demogs(df_om, df_emod, df_malariasimulation, agebins = fine_agebins)
#data.table::fwrite(df_plot,file.path(getwd(), 'plotter', "df_age_demographies.csv"))

pA <- ggplot(df_plot, aes(x = as.factor(upper_age), y = value_age_specific, fill = model)) +
  geom_col(position = position_dodge(width = (0.8)), width = 0.75) +
  scale_y_continuous(breaks = seq(0, 0.25, 0.05), expand = expansion(c(0, 0.1))) +
  labs(fill = '', y = "Proportion by age\n", x = 'Age group (upper age)') +
  scale_fill_manual(values = model_cols) +
  theme_bw()

pB <- ggplot(df_plot, aes(x = as.factor(upper_age), y = value_cumulative, fill = model, group = model)) +
  geom_col(position = position_dodge(width = (0.8)), width = 0.75) +
  scale_y_continuous(breaks = seq(0, 1, 0.1), expand = expansion(c(0, 0.05))) +
  scale_fill_manual(values = model_cols) +
  labs(fill = '', y = "Proportion by age\n(cumulative)", x = 'Age group (upper age)') +
  theme_bw()

pp <- ggarrange(pA, pB, ncol = 1, common.legend = TRUE, legend = 'bottom', labels = c('A', 'B')) +
  theme(plot.background = element_rect(fill = "white", color = NA),
        plot.margin = unit(c(0.5, 0.8, 0.3, 0.5), "cm"))

print(pp)

outdir <- file.path(getwd(), 'plotter', 'custom', 'generated_plots')
if (!dir.exists(outdir))dir.create(outdir)

ggsave(plot = pp, filename = file.path(outdir, 'age_dempgraphy.png'), width = 8, height = 6)
