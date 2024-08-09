#Generic helper functions
# Also as gists on: https://gist.github.com/ManuelaRunge/9d50c86e21161188a6c17c7c9650ad5d


# Load standard R packages used
library(data.table)
library(dplyr)
library(glue)
library(wrapr)
library(scales)
library(ggplot2)
library(cowplot)

emodom_cols_list <-list('EMOD'='#1b9e77ff','OpenMalaria'='#7570b3ff','malariasimulation'='#d95f02ff')
emodom_cols <- c('#1b9e77ff','#7570b3ff','#d95f02ff')

#' Load and combine data from EMOD and/or OpenMalaria benchmark output files.
#'
#' This function loads and combines data from the specified EMOD and/or OpenMalaria
#' benchmark output files.
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
#' modelname <- c("OpenMalaria", "EMOD")
#' result <- get_output_df(wdir, modelname, mth = TRUE)
#'
get_output_df <- function(wdir, modelname, mth = FALSE, fiveday = FALSE, daily = FALSE, timeseries = FALSE, cc=FALSE) {
  cols_to_keep <- NULL
  fname <- 'Benchmark.csv'
  
  if (timeseries) {
    fname <- 'PfPR_ClinicalIncidence_yr.csv'
    if (mth) {
      fname <- 'PfPR_ClinicalIncidence_mth.csv'
    }
    if (daily) {
      fname <- 'PfPR_ClinicalIncidence_daily.csv'
      cols_to_keep <- c('index', 'timestep', 'ageGroup', 'simulatedEIR', 'prevalence_2to10', 'prevalence',
                        'clinical_incidence', 'severe_incidence', 'seed', 'carrying_capacity_step')
    }
	  if (fiveday){
	    fname <- 'PfPR_ClinicalIncidence_5day.csv'
	    cols_to_keep <- c('seed','year','day','prevalence','clinical_incidence',
	                      'severe_incidence','ageGroup','prevalence_2to10','index',
	                      'output_target', 'model_input_om', 'model_input_ms', 'model_input_em',
	                      'cm_clinical','seasonality','simulatedEIR','n_total_mos_pop',
	                      'days','month','date','modelname')
	  }
  }
  if (cc){
    fname <- 'CCstep_daily.csv'
    cols_to_keep <- c('scen_id', 'output_target', 'cc_change', 'seed','timestep', 
                      'cm_clinical','seasonality','ageGroup','prevalence','prevalence_2to10','clinical_incidence',
                      'severe_incidence','simulatedEIR','n_total_mos_pop','n_infectious_mos','cc_title')
  }

  if (file.exists(file.path(wdir, fname))) {
    df <- fread(file.path(wdir, fname), stringsAsFactors = FALSE)
  } else {
    if ('OpenMalaria' %in% modelname) {
      om_df <- fread(file.path(wdir, paste('om', fname, sep = '/')), select = cols_to_keep)
      om_df$modelname <- 'OpenMalaria'
    }
    if ('EMOD' %in% modelname) {
      em_df <- fread(file.path(wdir, paste('em', fname, sep = '/')), select = cols_to_keep)
      em_df$modelname <- 'EMOD'
      #em_df <- em_df[em_df$simulatedEIR >0,]
    }
    if ('MalSim' %in% modelname) {
      ms_df <- fread(file.path(wdir, paste('MalSim', fname, sep = '/')), select = cols_to_keep)
      ms_df$modelname <- 'MalSim'
    }

    if ('EMOD' %in% modelname &
      'OpenMalaria' %in% modelname &
      'MalSim' %in% modelname) {
      df <- em_df %>% bind_rows(om_df) %>% bind_rows(ms_df)
    } else if ('OpenMalaria' %in% modelname &
      'EMOD' %in% modelname &
      !('MalSim' %in% modelname)) {
      df <-  em_df %>% bind_rows(om_df)
    } else if ('OpenMalaria' %in% modelname &
      'MalSim' %in% modelname &
      !('EMOD' %in% modelname)) {
      df <- ms_df %>% bind_rows(om_df)
    } else if ('EMOD' %in% modelname &
      'MalSim' %in% modelname &
      !('OpenMalaria' %in% modelname)) {
      df <- ms_df %>% bind_rows(em_df)
    } else if ('OpenMalaria' %in% modelname &
      !('EMOD' %in% modelname) &
      !('MalSim' %in% modelname)) {
      wdir <- file.path(wdir, 'om')
      df <- om_df
    } else if ('EMOD' %in% modelname &
      !('OpenMalaria' %in% modelname) &
      !('MalSim' %in% modelname)) {
      wdir <- file.path(wdir, 'em')
      df <- em_df
    } else if ('MalSim' %in% modelname &
      !('OpenMalaria' %in% modelname) &
      !('EMOD' %in% modelname)) {
      wdir <- file.path(wdir, 'MalSim')
      df <- ms_df
    } else {
      stop(paste("Please specify modelname as some combination of EMOD, OpenMalaria, and MalSim (list), ", modelname, " not valid"))
    }

    if ('ageGroup' %in% colnames(df)) {
      df$ageGroup <- factor(df$ageGroup, levels = unique(df$ageGroup))
    }
    #warning_df <- df[df$simulatedEIR == 0,]
    #if (nrow(warning_df) > 0 & !daily) {
    #  print('Warning: some eirs had simulated EIRS of 0, and were removed')
    #  df <- df[df$simulatedEIR > 0,]
    #  df <- df[complete.cases(df$simulatedEIR),]
    #}
  }
  return(df)
}


#' Save Plot to File
#'
#' This function saves a plot to a file in the specified directory, supporting multiple file formats.
#'
#' @param pplot The plot object to be saved.
#' @param plot_name The name of the plot file (without file extension).
#' @param plot_dir The directory where the plot file will be saved.
#' @param width The width of the plot in inches. Default is 14.
#' @param height The height of the plot in inches. Default is 8.
#' @param units The units of width and height. Default is 'in' (inches).
#' @param device_format A character vector specifying the desired file formats for saving the plot. Possible values are 'pdf' and 'png'.
#' @return None
#'
#' @examples
#' # Save a plot as both PDF and PNG files
#' f_save_plot(my_plot, "my_plot", "/path/to/plots", device_format = c('pdf', 'png'))
#'
#' @importFrom ggsave ggsave
#' @importFrom dir.create dir.create
#'
f_save_plot <- function(pplot, plot_name, plot_dir, width = 14, height = 8, units = 'in', device_format = c('pdf', 'png')) {
  if ('png' %in% device_format) {
    ggsave(paste0(plot_name, ".png"), plot = pplot, path = plot_dir,
           width = width, height = height, units = units, device = "png")
  }
  if ('pdf' %in% device_format) {
    if (!dir.exists(file.path(plot_dir, "pdf"))) { dir.create(file.path(plot_dir, "pdf")) }
    ggsave(paste0(plot_name, ".pdf"), plot = pplot, path = file.path(plot_dir, "pdf"),
           width = width, height = height, units = units, device = "pdf", useDingbats = FALSE)
  }
}

#' Combine and Arrange Plots
#'
#' This function combines and arranges multiple plots into a single grid layout, with an optional legend.
#'
#' @param plist A list of plot objects to be combined.
#' @param ncol The number of columns in the grid layout. Default is 1.
#' @param legend_position The position of the legend. Possible values are 'right', 'left', 'bottom', 'top', and 'none'. Default is 'right'.
#' @param rel_dims Relative dimensions for each plot in the grid. Can be a single value or a vector of values. Default is 1.
#' @param leg_dim Relative dimension for the legend. Default is 0.25.
#' @param labels Labels for the plots. Should be a character vector of the same length as plist. Default is c('', '').
#' @return The combined and arranged plot.
#'
#' @examples
#' # Combine and arrange two plots with a legend on the right
#' combined_plot <- plot_combine(list(plot1, plot2), ncol = 2, legend_position = 'right')
#'
#' @importFrom cowplot plot_grid
#' @importFrom cowplot get_legend
#'
plot_combine <- function(plist, ncol = 1, legend_position = 'right', rel_dims = 1, leg_dim = 0.25, labels = c('', '')) {
  plegend <- get_legend(plist[[1]])

  for (i in c(1:length(plist))) {
    plist[[i]] <- plist[[i]] + theme(legend.position = 'None')
  }

  if (sum(lengths(rel_dims)) == 1)rel_dims <- rep(rel_dims, length(plist))
  pplot <- cowplot::plot_grid(plotlist = plist, ncol = ncol, labels = labels, rel_widths = rel_dims)
  if (tolower(legend_position) == 'right')pplot <- plot_grid(pplot, plegend, ncol = 2, rel_widths = c(1, leg_dim))
  if (tolower(legend_position) == 'left')pplot <- plot_grid(plegend, pplot, ncol = 1, rel_heights = c(leg_dim, 1))
  if (tolower(legend_position) == 'bottom')pplot <- plot_grid(pplot, plegend, ncol = 1, rel_heights = c(1, leg_dim))
  if (tolower(legend_position) == 'top')pplot <- plot_grid(plegend, pplot, ncol = 1, rel_heights = c(leg_dim, 1))
  if (tolower(legend_position) == 'none')pplot <- pplot
  return(pplot)
}

#' Compare Two Lists of Strings
#'
#' This function compares two lists of strings and provides information about the names present in each list.
#'
#' @param A A list of strings.
#' @param B A list of strings to compare to.
#' @param showNames Which names to show. Options are "both" (default), "AB", or "BA".
#' @return None. Names are printed in the console.
#'
#' @examples
#' # Compare two lists of strings and show names in both lists
#' f_compareNames(list1, list2, showNames = "both")
#'
#' @importFrom base unique
#'
f_compareNames <- function(A, B, showNames = "both") {
          #' Function to compare two list of strings
          #' @param A list of strings
          #' @param B list of strings to compare to
          #' @param showNames which names to show options are both, AB, BA
          #' @return nothing, names are printed in console
          #'
  A = unique(as.character(A))
  B = unique(as.character(B))

  AinB = which(A %in% B)
  BinA = which(B %in% A)

  AnotinB = which(!(A %in% B))
  BnotinA = which(!(B %in% A))

  print(paste0("A in B n= ", length(AinB)))
  print(paste0("B in A n= ", length(BinA)))

  print(paste0("A not in B n= ", length(AnotinB)))
  print(paste0("B not in A n= ", length(BnotinA)))

  if (showNames == "both") {
    print(paste0("A not in B: "))
    print(A[AnotinB])

    print(paste0("B not in A: "))
    print(B[BnotinA])
  }
  if (showNames == "AB") {
    print(paste0("A not in B: "))
    print(A[AnotinB])
  }
  if (showNames == "BA") {
    print(paste0("B not in A: "))
    print(B[BnotinA])
  }

}


#' Get Custom Theme for Plots
#'
#' This function returns a custom theme for plots with modified visual elements such as text sizes, font styles, and plot margins.
#'
#' @param fontscl Scaling factor for font sizes. Default is 1.
#' @return A custom theme object.
#'
#' @examples
#' # Get the custom theme with default font scaling
#' custom_theme <- f_getCustomTheme()
#'
#' # Get the custom theme with increased font scaling
#' custom_theme <- f_getCustomTheme(fontscl = 1.5)
#'
#' @importFrom ggplot2 theme element_text element_blank element_rect element_line unit
#'
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

#' Remove Legends from ggplot Objects
#'
#' This function removes the legends from a list of ggplot objects.
#'
#' @param gglist A list of ggplot objects.
#' @return A list of ggplot objects with legends removed.
#'
#' @examples
#' # Create a list of ggplot objects
#' plots <- list(plot1, plot2, plot3)
#'
#' # Remove legends from the plots
#' plots <- remove_legends(plots)
#'
remove_legends <- function(gglist) {
  for (i in c(1:length(gglist))) {
    gglist[[i]] <- gglist[[i]] + theme(legend.position = 'None')
  }
  return(gglist)
}

scale_twentyfour_palette <- function(){
  scale_color_manual(values  = c(
    "dodgerblue2", "#E31A1C",
    "green4",
    "#6A3D9A", 
    "#FF7F00", 
    "gold1",
    "skyblue2", "#FB9A99",
    "palegreen2",
    "#CAB2D6", 
    "#FDBF6F", 
    "gray70", "khaki2",
    "maroon", "orchid1", "deeppink1", "blue1", "steelblue4",
    "darkturquoise", "green1", "yellow4", "yellow3",
    "darkorange4", "brown")
  )
}

