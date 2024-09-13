
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
#' @param modelname Name of models for which result CSVs should be loaded, case sensitive.
#' @param mth Set to TRUE if the data files have monthly data. Default is FALSE.
#' @param timeseries Set to TRUE if the unaggregated timeseries data should be read in. Default is FALSE.
#'
#' @return df
#'
#' @raises An error if invalid modelname value is specified.
#'
#' @import data.table
#'
#' @examples
#' wdir <- "path/to/data"
#' modelname <- c("EMOD","malariasimulation", "OpenMalaria")
#' result <- get_output_df(wdir, modelname, mth = TRUE)
#'
get_output_df <- function(wdir, modelname, mth = FALSE, fiveday = FALSE, daily = FALSE, timeseries = FALSE, ccstep = FALSE) {
  cols_to_keep <- NULL
  fname <- 'mmmpy_timeavrg.csv'

  if (timeseries) {
    fname <- 'mmmpy_yr.csv'
    if (mth) {
      fname <- 'mmmpy_mth.csv'
    }
    if (daily) {
      fname <- 'mmmpy_daily.csv'
      cols_to_keep <- c('index', 'timestep', 'ageGroup', 'simulatedEIR', 'prevalence_2to10', 'prevalence',
                        'clinical_incidence', 'severe_incidence', 'seed', 'carrying_capacity_step')
    }
    if (fiveday) {
      fname <- 'mmmpy_5day.csv'
      cols_to_keep <- c('seed', 'year', 'day', 'prevalence', 'clinical_incidence',
                        'severe_incidence', 'ageGroup', 'prevalence_2to10', 'index',
                        'output_target', 'model_input_openmalaria', 'model_input_malariasimulation', 'model_input_emod',
                        'cm_clinical', 'seasonality', 'simulatedEIR', 'n_total_mos_pop')
    }
  }
  if (ccstep) {
    fname <- 'mmmpy_ccstep_daily.csv'
    cols_to_keep <- c('scen_id', 'output_target', 'cc_change', 'seed', 'timestep',
                      'cm_clinical', 'seasonality', 'ageGroup', 'prevalence', 'prevalence_2to10', 'clinical_incidence',
                      'severe_incidence', 'simulatedEIR', 'n_total_mos_pop', 'n_infectious_mos', 'cc_title')
  }

  if (file.exists(file.path(wdir, fname))) {
    df <- fread(file.path(wdir, fname), stringsAsFactors = FALSE)
  } else {
    if ('OpenMalaria' %in% modelname) {
      om_df <- fread(file.path(wdir, paste('OpenMalaria', fname, sep = '/')), select = cols_to_keep)
      om_df$modelname <- 'OpenMalaria'
    }
    if ('EMOD' %in% modelname) {
      em_df <- fread(file.path(wdir, paste('EMOD', fname, sep = '/')), select = cols_to_keep)
      em_df$modelname <- 'EMOD'
      #em_df <- em_df[em_df$simulatedEIR >0,]
    }
    if ('/malariasimulation' %in% modelname) {
      ms_df <- fread(file.path(wdir, paste('malariasimulation', fname, sep = '/')), select = cols_to_keep)
      ms_df$modelname <- 'malariasimulation'
    }

    if ('EMOD' %in% modelname &
      'OpenMalaria' %in% modelname &
      'malariasimulation' %in% modelname) {
      df <- em_df %>% bind_rows(om_df) %>% bind_rows(ms_df)
    } else if ('OpenMalaria' %in% modelname &
      'EMOD' %in% modelname &
      !('malariasimulation' %in% modelname)) {
      df <- em_df %>% bind_rows(om_df)
    } else if ('OpenMalaria' %in% modelname &
      'malariasimulation' %in% modelname &
      !('EMOD' %in% modelname)) {
      df <- ms_df %>% bind_rows(om_df)
    } else if ('EMOD' %in% modelname &
      'malariasimulation' %in% modelname &
      !('OpenMalaria' %in% modelname)) {
      df <- ms_df %>% bind_rows(em_df)
    } else if ('OpenMalaria' %in% modelname &
      !('EMOD' %in% modelname) &
      !('malariasimulation' %in% modelname)) {
      wdir <- file.path(wdir, 'om')
      df <- om_df
    } else if ('EMOD' %in% modelname &
      !('OpenMalaria' %in% modelname) &
      !('malariasimulation' %in% modelname)) {
      wdir <- file.path(wdir, 'em')
      df <- em_df
    } else if ('malariasimulation' %in% modelname &
      !('OpenMalaria' %in% modelname) &
      !('EMOD' %in% modelname)) {
      wdir <- file.path(wdir, 'malariasimulation')
      df <- ms_df
    } else {
      stop(paste("Please specify modelname as some combination of EMOD, malariasimulation and OpenMalaria, (list), ", modelname, " not valid"))
    }

    if ('ageGroup' %in% colnames(df)) {
      df$ageGroup <- factor(df$ageGroup, levels = unique(df$ageGroup))
    }

  }
  return(df)
}

