
# Load standard R packages used
library(data.table)
library(dplyr)
library(glue)
library(wrapr)
library(scales)
library(ggplot2)


mmmpy_models <- c("EMOD", "malariasimulation", "OpenMalaria")
mmmpy_cols_list <- list('EMOD' = '#1b9e77ff', 'malariasimulation' = '#d95f02ff', 'OpenMalaria' = '#7570b3ff')
mmmpy_cols <- c('#1b9e77ff', '#7570b3ff', '#d95f02ff')


#' Load and combine data from model output files.
#'
#' This function loads and combines data from the standardized mmmpy output files.
#'
#' @param wdir Working directory where the data files are located.
#' @param models Name of models for which result CSVs should be loaded, case sensitive.
#' @param mth Set to TRUE if the data files have monthly data. Default is FALSE.
#' @param timeseries Set to TRUE if the unaggregated timeseries data should be read in. Default is FALSE.
#'
#' @return df
#'
#' @raises An error if invalid models value is specified.
#'
#' @import data.table
#'
#' @examples
#' wdir <- "path/to/data"
#' models <- c("EMOD","malariasimulation", "OpenMalaria")
#' result <- get_output_df(wdir, models, mth = TRUE)
#'
get_output_df <- function(wdir, models, yearly = FALSE, monthly = FALSE, fiveday = FALSE, daily = FALSE, mpv = FALSE) {
  cols_to_keep <- NULL
  fname <- 'mmmpy_timeavrg'

  if (yearly) {
    fname <- 'mmmpy_yr'
  }
  if (monthly) {
    fname <- 'mmmpy_mth'
  }
  if (daily) {
    fname <- 'mmmpy_daily'
  }
  if (fiveday) {
    fname <- 'mmmpy_5day'
  }

  if (file.exists(file.path(wdir, fname))) {
    df <- fread(file.path(wdir, fname), stringsAsFactors = FALSE)
  } else {
    if ('OpenMalaria' %in% models) {
      om_df <- fread(file.path(wdir, paste0('OpenMalaria/',fname, '.csv')), select = cols_to_keep)
      om_df$models <- 'OpenMalaria'
    }
    if ('EMOD' %in% models) {
      em_df <- fread(file.path(wdir, paste0('EMOD/', fname,'.csv')), select = cols_to_keep)
      em_df$models <- 'EMOD'
    }
    if ('malariasimulation' %in% models) {
      ms_df <- fread(file.path(wdir, paste0('malariasimulation/', fname,'.csv')), select = cols_to_keep)
      ms_df$models <- 'malariasimulation'
      if (mpv) {
        ms_df_pv <- fread(file.path(wdir, paste0('malariasimulation/', fname,'_pv.csv')), select=cols_to_keep)
        ms_df_pv$models <- 'malariasimulation - pv'
        ms_df <- rbind(ms_df, ms_df_pv, fill=TRUE)
      }
    }

    if ('EMOD' %in% models &
      'OpenMalaria' %in% models &
      'malariasimulation' %in% models) {
      df <- em_df %>% bind_rows(om_df) %>% bind_rows(ms_df)
    } else if ('OpenMalaria' %in% models &
      'EMOD' %in% models &
      !('malariasimulation' %in% models)) {
      df <- em_df %>% bind_rows(om_df)
    } else if ('OpenMalaria' %in% models &
      'malariasimulation' %in% models &
      !('EMOD' %in% models)) {
      df <- ms_df %>% bind_rows(om_df)
    } else if ('EMOD' %in% models &
      'malariasimulation' %in% models &
      !('OpenMalaria' %in% models)) {
      df <- ms_df %>% bind_rows(em_df)
    } else if ('OpenMalaria' %in% models &
      !('EMOD' %in% models) &
      !('malariasimulation' %in% models)) {
      wdir <- file.path(wdir, 'om')
      df <- om_df
    } else if ('EMOD' %in% models &
      !('OpenMalaria' %in% models) &
      !('malariasimulation' %in% models)) {
      wdir <- file.path(wdir, 'em')
      df <- em_df
    } else if ('malariasimulation' %in% models &
      !('OpenMalaria' %in% models) &
      !('EMOD' %in% models)) {
      wdir <- file.path(wdir, 'malariasimulation')
      df <- ms_df
    } else {
      stop(paste("Please specify models as some combination of EMOD, malariasimulation and OpenMalaria, (list), ", models, " not valid"))
    }

    if ('ageGroup' %in% colnames(df)) {
      df$ageGroup <- factor(df$ageGroup, levels = unique(df$ageGroup))
    }
  }
  return(df)
}

f_getCustomTheme <- function(fontscl = 1) {
  customTheme <- theme(
    strip.text.x = element_text(size = 12 * fontscl, face = "bold"),
    strip.text.y = element_text(size = 12 * fontscl, face = "bold"),
    strip.background = element_blank(),
    plot.title = element_text(size = 14 * fontscl, vjust = -1, hjust = 0),
    plot.subtitle = element_text(size = 12 * fontscl),
    plot.caption = element_text(size = 9 * fontscl),
    legend.title = element_text(size = 12 * fontscl),
    legend.text = element_text(size = 12 * fontscl),
    axis.title.x = element_text(size = 12 * fontscl),
    axis.text.x = element_text(size = 12 * fontscl),
    axis.title.y = element_text(size = 12 * fontscl),
    axis.text.y = element_text(size = 12 * fontscl),
    axis.ticks = element_line(),
    panel.grid.minor = element_blank(),
    panel.border = element_rect(colour = "black", fill = NA, linewidth = 0.5),
    plot.margin = unit(c(0.5, 0.5, 0.5, 0.5), "cm")
  )
  return(customTheme)
}

calculate_monthlyEIRs_seasonal <- function(wdir,note){
  df <- fread(file.path(wdir, 'EMOD', 'EIR_mth.csv'), stringsAsFactors = FALSE)
  df <- df %>%
    filter(year == max(year), cm_clinical == 0.0, seasonality == 'seasonal', target_output_values == 20) %>%
    group_by(target_output_values, cm_clinical, seasonality, Run_Number) %>%
    mutate(sumEIR = sum(`Monthly EIR`),
           simulatedEIR = (`Monthly EIR`/sumEIR))
  df <- df %>%
    group_by(month) %>%
    summarise(simulatedEIR = mean(simulatedEIR)) %>%
    ungroup()
  write.csv(df, paste0("monthly_seasonal_EIR_values_",note,".csv"), row.names=FALSE)
}

calculate_dailyEIRs_seasonal <- function(wdir,note){
  df <- fread(file.path(wdir, 'EMOD', 'EIR_daily.csv'), stringsAsFactors = FALSE)
  #dat_s$target_output_values <- dat_s$output_target
  df <- df %>%
    filter(scen_id == 1, year == max(year)) %>%
    group_by(scen_id, Run_Number) %>%
    mutate(sumEIR = sum(eir),
           simulatedEIR = (eir/sumEIR))
  df <- df %>%
    group_by(scen_id, day) %>%
    summarise(simulatedEIR = mean(simulatedEIR))
  write.csv(df, paste0("daily_seasonal_EIR_values_",note,".csv"), row.names=FALSE)
}
