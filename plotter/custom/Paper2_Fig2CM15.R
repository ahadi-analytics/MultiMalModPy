### 'Baseline' figure
setwd("~/MultiMalModPy")
library(ggplot2)
library(dplyr)
library(data.table)
library(tidyr)
library(patchwork)

source('utility/functions.R')
theme_set(theme_bw())

modelname <- c("EMOD", "malariasimulation","OpenMalaria_nSevere", "OpenMalaria_noCo")
agegrps <- c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100')

customTheme <- f_getCustomTheme() +
  theme(legend.position = "None",
        panel.grid.minor = element_blank())

# Load simulation outputs  -------------------------------
dat_em_15 <- get_output_df("/projects/b1139/emod-om/simulation_outputs/rer4177/20250207_production/sims_dynamic_perennial_seasonal_17_20_45", modelname = "EMOD")
dat_ms_15 <- get_output_df("/projects/b1139/emod-om/simulation_outputs/rer4177/20250207_production/sims_dynamic_perennial_seasonal_17_20_45", modelname = "malariasimulation")
dat_om_15_noCo <- get_output_df("/projects/b1139/emod-om/simulation_outputs/rer4177/20250207_production/sims_dynamic_perennial_seasonal_17_20_45", modelname = "OpenMalaria")
dat_om_15_noCo$modelname <- "OpenMalaria_noCo"
dat_om_15 <- get_output_df("/projects/b1139/emod-om/simulation_outputs/rer4177/20250207_production/sims_dynamic_perennial_seasonal_17_20_45", modelname = "OpenMalaria")
dat_om_15$modelname <- "OpenMalaria_nSevere"
dat_total <- rbind(dat_om_15_noCo, dat_om_15, dat_em_15, dat_ms_15, fill=TRUE)
dat_total <- dat_total %>%
  filter(cm_clinical == 0.15, seasonality == "perennial")
rm(dat_ms_15, dat_em_15, dat_om_15)

dat_total <- dat_total %>%
  group_by(output_target, cm_clinical, ageGroup, seasonality, modelname) %>%
  summarise(simulatedEIR__mean = mean(simulatedEIR),
            simulatedEIR__min = quantile(simulatedEIR, 0.05),
            simulatedEIR__up = quantile(simulatedEIR, 0.95),
            prevalence__mean = mean(prevalence),
            prevalence__min = quantile(prevalence, 0.05),
            prevalence__up = quantile(prevalence, 0.95),
            prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95),
            clinical_incidence__mean = mean(clinical_incidence),
            clinical_incidence__min = quantile(clinical_incidence, 0.05),
            clinical_incidence__up = quantile(clinical_incidence, 0.95),
            severe_incidence__mean = mean(severe_incidence),
            severe_incidence__min = quantile(severe_incidence, 0.05),
            severe_incidence__up = quantile(severe_incidence, 0.95))
dat_total$ageGroup <- factor(dat_total$ageGroup,
                             levels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'),
                             labels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'))


# Load Interpolation (time avrg) Data
i_ms <- fread(file.path('/home/rer4177/model-characterization/target_calibration/malariasimulation/interpolation_data.csv'))
i_ms <- i_ms %>%
  filter(pop_size == 50000, seasonality == 'perennial', cm_clinical == 0.15)
i_em <- fread(file.path('/home/rer4177/model-characterization/target_calibration/EMOD/interpolation_data.csv'))
i_em <- i_em %>%
  filter(pop_size == 5000, seasonality == 'perennial', cm_clinical == 0.15, input_target <= 660)
i_om <- fread(file.path('/home/rer4177/model-characterization/target_calibration/OpenMalaria/interpolation_data.csv'))
i_om <- i_om %>%
  filter(pop_size == 50000, seasonality == 'perennial', cm_clinical == 0.15, input_target <= 290)
i_om$modelname <- "OpenMalaria_noCo"
i_om_nSevere <- fread(file.path('/home/rer4177/model-characterization/target_calibration/OpenMalaria/sims_dynamic_perennial_seasonal__11_53_26nSevere_interpolation_data.csv'))
i_om_nSevere <- i_om_nSevere %>%
  filter(pop_size == 50000, seasonality == 'perennial', cm_clinical == 0.15, input_target <= 290)
i_om_nSevere$modelname <- "OpenMalaria_nSevere"
i_full <- rbind(i_om, i_em, i_ms, i_om_nSevere, fill=TRUE)
rm(i_om, i_em, i_ms)

for (ii in unique(dat_total$cm_clinical)){
  ii = 0.15
  dat_p <- filter(dat_total, cm_clinical == 0.15, seasonality == 'perennial', output_target <= 0.8)
  i_p <- filter(i_full, cm_clinical == 0.15, seasonality == 'perennial')
  i_p <- filter(i_p, simulatedEIR >= 0.01)
  # ------------------------------ Figure 2A and B ------------------------------
  pA <- i_p %>%
    ggplot() +
    #geom_ribbon(aes(x = simulatedEIR, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = simulatedEIR, y = prevalence_2to10, col = modelname),linewidth=1.25) +
    expand_limits(y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(trans=scales::pseudo_log_trans(base = 10),expand = expansion(mult = c(0, 0)), breaks=c(0, 0.1,1,10,100,1000),
                       labels = c(0, 0.1, 1,10,100,1000),limits = c(0,1000)) +
    customTheme +
    theme(panel.grid.minor = element_blank())+
    labs(y = expression('PfPR'[2-10]),
         x = "Simulated EIR",
         title = paste("All Ages CM: ", ii),
         subtitle = "",
         fill = 'Model',
         color = 'Model') +
    theme(legend.position = c(.15, .65))
  pA
  
  pB1 <- i_p %>%
    ggplot() +
    #geom_ribbon(aes(x = simulatedEIR, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = prevalence_2to10, y = clinical_incidence, col = modelname),linewidth=1.25) +
    expand_limits(x=0, y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(expand = expansion(mult = c(0, 0))) +
    customTheme +
    theme(panel.grid.minor = element_blank())+
    labs(y = "Clinical Incidence\n(ppa)",
         x = "",
         title = "",
         subtitle = "")
  pB1
  pB2 <- i_p %>%
    mutate(severe_incidence = severe_incidence * 100) %>%
    ggplot() +
    #geom_ribbon(aes(x = simulatedEIR, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = prevalence_2to10, y = severe_incidence, col = modelname, linetype = modelname),linewidth=1.25) +
    expand_limits(x=0,y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_linetype_manual(values = c("solid", "solid","solid","dashed")) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(expand = expansion(mult = c(0, 0))) +
    customTheme +
    theme(panel.grid.minor = element_blank())+
    labs(y = "Severe Incidence\n(ppa)",
         x = expression('PfPR'[2-10]),
         title = "",
         subtitle = "")
  pB2
  pB <- pB1 / pB2
  pB
  
  pB1eir <- i_p %>%
    ggplot() +
    #geom_ribbon(aes(x = simulatedEIR, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = simulatedEIR, y = clinical_incidence, col = modelname),linewidth=1.25) +
    expand_limits(x=0,y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_linetype_manual(values = c("dotted", "solid","solid","dashed")) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(trans=scales::pseudo_log_trans(base = 10),expand = expansion(mult = c(0, 0)), breaks=c(0, 0.1,1,10,100,1000),
                       labels = c(0, 0.1, 1,10,100,1000),limits = c(0,1000)) +
    customTheme +
    theme(panel.grid.minor = element_blank())+
    labs(y = "Clinical Incidence\n(ppa)",
         x = "",
         title = "",
         subtitle = "")
  pB1eir
  pB2eir <- i_p %>%
    mutate(severe_incidence = severe_incidence * 100) %>%
    ggplot() +
    #geom_ribbon(aes(x = simulatedEIR, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = simulatedEIR, y = severe_incidence, col = modelname, linetype=modelname),linewidth=1.25) +
    expand_limits(y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_linetype_manual(values = c("solid", "solid","solid","dashed")) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(trans = "log10",expand = expansion(mult = c(0, 0)), breaks=c(0.1,1,10,100,1000),
                       labels = c(0.1, 1,10,100,1000),limits = c(0.1,1000)) +
    customTheme +
    theme(panel.grid.minor = element_blank())+
    labs(y = "Severe Incidence\n(ppa)",
         x = "Simulated EIR",
         title = "",
         subtitle = "")
  pBeir <- pB1eir / pB2eir
  
  mylayout <- "A
               B"
  
  pAB <- (pA+pBeir)+plot_layout(design=mylayout)
  pAB
  ggsave(plot = pAB, filename = file.path(getwd(), paste('Figure2_CM', ii, '_ABeir.pdf',sep="")), height = 17.89, width = 34.13)
  ggsave(plot = pAB, filename = file.path(getwd(), paste('Figure2_CM', ii, '_ABeir.png',sep="")), height = 17.89, width = 34.13)
  
  # ------------------------------ Figure 2C ------------------------------
  pfpr_labels <- c('PfPR2-10 5%', 'PfPR2-10 10%', 'PfPR2-10 25%', 'PfPR2-10 50%')
  pfpr_values <- c(0.05,0.1,0.25,0.5)
  
  dat_p <- dat_p %>%
    mutate(pfpr_grp = case_when(
      modelname == 'EMOD' & output_target %in% pfpr_values[1] ~ pfpr_labels[1],
      modelname == 'EMOD' & output_target %in% pfpr_values[2] ~ pfpr_labels[2],
      modelname == 'EMOD' & output_target %in% pfpr_values[3] ~ pfpr_labels[3],
      modelname == 'EMOD' & output_target %in% pfpr_values[4] ~ pfpr_labels[4],
      ## OM
      modelname == 'OpenMalaria_nSevere' & output_target %in% pfpr_values[1] ~ pfpr_labels[1],
      modelname == 'OpenMalaria_nSevere' & output_target %in% pfpr_values[2] ~ pfpr_labels[2],
      modelname == 'OpenMalaria_nSevere' & output_target %in% pfpr_values[3] ~ pfpr_labels[3],
      modelname == 'OpenMalaria_nSevere' & output_target %in% pfpr_values[4] ~ pfpr_labels[4],
      modelname == 'OpenMalaria_noCo' & output_target %in% pfpr_values[1] ~ pfpr_labels[1],
      modelname == 'OpenMalaria_noCo' & output_target %in% pfpr_values[2] ~ pfpr_labels[2],
      modelname == 'OpenMalaria_noCo' & output_target %in% pfpr_values[3] ~ pfpr_labels[3],
      modelname == 'OpenMalaria_noCo' & output_target %in% pfpr_values[4] ~ pfpr_labels[4],
      ## malariasimulation
      modelname == 'malariasimulation' & output_target %in% pfpr_values[1] ~ pfpr_labels[1],
      modelname == 'malariasimulation' & output_target %in% pfpr_values[2] ~ pfpr_labels[2],
      modelname == 'malariasimulation' & output_target %in% pfpr_values[3] ~ pfpr_labels[3],
      modelname == 'malariasimulation' & output_target %in% pfpr_values[4] ~ pfpr_labels[4]),
      pfpr_grp = factor(pfpr_grp, levels = pfpr_labels, labels = pfpr_labels))
  
  
  pC1 <- dat_p %>%
    ungroup() %>%
    filter(ageGroup %in% agegrps) %>%
    filter(!is.na(pfpr_grp)) %>%
    dplyr::select(output_target, ageGroup, pfpr_grp, modelname,
                  prevalence__mean, prevalence__min, prevalence__up,
                  clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                  severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
    pivot_longer(cols = -c(output_target, ageGroup, modelname, pfpr_grp)) %>%
    separate(name, into = c('name', 'stat'), sep = '__') %>%
    mutate(name = factor(name, levels = c('prevalence', 'clinical_incidence', 'severe_incidence'),
                         labels = c('Prevalence', 'Clinical Incidence (ppa)', 'Severe Incidence (ppa)'))) %>%
    filter(name =='Prevalence') %>%
    pivot_wider(names_from = stat, values_from = value) %>%
    ggplot() +
    geom_ribbon(aes(x = ageGroup, ymin = min, ymax = up, fill = modelname, group = modelname), alpha = 0.15) +
    geom_line(aes(x = ageGroup, y = mean, col = modelname, group = modelname),linewidth=1.25) +
    expand_limits(y=0) +
    facet_wrap(~ pfpr_grp, scales = 'free', nrow=1) + 
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_discrete(expand = expansion(mult = c(0, 0))) +
    customTheme +
    labs(x = "",
         y = 'Prevalence',
         title = "",
         subtitle = "") +
    theme(axis.text.x = element_text(angle = 45,vjust = 1, hjust=1))
  pC1
  
  pC2 <- dat_p %>%
    ungroup() %>%
    filter(ageGroup %in% agegrps) %>%
    filter(!is.na(pfpr_grp)) %>%
    dplyr::select(output_target, ageGroup, pfpr_grp, modelname,
                  prevalence__mean, prevalence__min, prevalence__up,
                  clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                  severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
    pivot_longer(cols = -c(output_target, ageGroup, modelname, pfpr_grp)) %>%
    separate(name, into = c('name', 'stat'), sep = '__') %>%
    mutate(name = factor(name, levels = c('prevalence', 'clinical_incidence', 'severe_incidence'),
                         labels = c('Prevalence', 'Clinical Incidence (ppa)', 'Severe Incidence (ppa)'))) %>%
    filter(name =='Clinical Incidence (ppa)') %>%
    pivot_wider(names_from = stat, values_from = value) %>%
    ggplot() +
    geom_ribbon(aes(x = ageGroup, ymin = min, ymax = up, fill = modelname, group = modelname), alpha = 0.15) +
    geom_line(aes(x = ageGroup, y = mean, col = modelname, group = modelname),linewidth=1.25) +
    expand_limits(y=0) +
    facet_wrap(~ pfpr_grp, scales = 'free', nrow=1) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_discrete(expand = expansion(mult = c(0, 0))) +
    customTheme +
    labs(x = "",
         y = 'Clinical Incidence\n(ppa)',
         title = "",
         subtitle = "") +
    theme(strip.text.x = element_blank(),
          axis.text.x = element_text(angle = 45,vjust = 1, hjust=1))
  
  pC3 <- dat_p %>%
    ungroup() %>%
    filter(ageGroup %in% agegrps) %>%
    filter(!is.na(pfpr_grp)) %>%
    dplyr::select(output_target, ageGroup, pfpr_grp, modelname,
                  prevalence__mean, prevalence__min, prevalence__up,
                  clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                  severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
    pivot_longer(cols = -c(output_target, ageGroup, modelname, pfpr_grp)) %>%
    separate(name, into = c('name', 'stat'), sep = '__') %>%
    mutate(name = factor(name, levels = c('prevalence', 'clinical_incidence', 'severe_incidence'),
                         labels = c('Prevalence', 'Clinical Incidence (ppa)', 'Severe Incidence (ppa)'))) %>%
    filter(name =='Severe Incidence (ppa)') %>%
    mutate(value = value * 100) %>%
    pivot_wider(names_from = stat, values_from = value) %>%
    ggplot() +
    geom_ribbon(aes(x = ageGroup, ymin = min, ymax = up, fill = modelname, group = modelname), alpha = 0.15) +
    geom_line(aes(x = ageGroup, y = mean, col = modelname, group = modelname, linetype = modelname),linewidth=1.25) +
    expand_limits(y=0) +
    facet_wrap(~ pfpr_grp, scales = 'free', nrow=1)+
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_linetype_manual(values = c("solid", "solid","solid","dashed")) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_discrete(expand = expansion(mult = c(0, 0))) +
    customTheme +
    labs(x = "Age (years)",
         y = 'Severe Incidence\n(ppa)',
         title = "",
         subtitle = "") +
    theme(strip.text.x = element_blank(),
          axis.text.x = element_text(angle = 45,vjust = 1, hjust=1))
  
  pC3
  pC <- pC1 / pC2 / pC3
  pC
  # ------------------------------ Figure 2D V1------------------------------
  
  pD1 <- dat_p %>%
    ungroup() %>%
    filter(ageGroup %in% agegrps) %>%
    dplyr::select(output_target, ageGroup, prevalence_2to10__mean, modelname,
                  clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                  severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
    pivot_longer(cols = -c(output_target, ageGroup, modelname, prevalence_2to10__mean)) %>%
    separate(name, into = c('name', 'stat'), sep = '__') %>%
    filter(name =='clinical_incidence') %>%
    mutate(name = case_when(name == 'clinical_incidence' ~ 'Clinical Incidence\n(ppa)')) %>%
    pivot_wider(names_from = stat, values_from = value) %>%
    ggplot() +
    geom_ribbon(aes(x = prevalence_2to10__mean, ymin = min, ymax = up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = prevalence_2to10__mean, y = mean, col = modelname),linewidth=1) +
    expand_limits(x=0,y=0) +
    facet_wrap(~ageGroup, scales = 'free_y', nrow = 1) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(expand = expansion(mult = c(0, 0))) +
    customTheme +
    labs(x = "",
         y = 'Clinical Incidence\n(ppa)',
         title = "Age Groups",
         subtitle = "") +
    theme(axis.text.x =  element_text(angle = 45, vjust = 1, hjust=1))
  
  pD2 <- dat_p %>%
    ungroup() %>%
    filter(ageGroup %in% agegrps) %>%
    dplyr::select(output_target, ageGroup, prevalence_2to10__mean, modelname,
                  clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                  severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
    pivot_longer(cols = -c(output_target, ageGroup, modelname, prevalence_2to10__mean)) %>%
    separate(name, into = c('name', 'stat'), sep = '__') %>%
    filter(name =='severe_incidence') %>%
    mutate(name = case_when(name == 'severe_incidence' ~ 'Severe Incidence\n(ppa)')) %>%
    mutate(value = value * 100) %>%
    pivot_wider(names_from = stat, values_from = value) %>%
    ggplot() +
    geom_ribbon(aes(x = prevalence_2to10__mean, ymin = min, ymax = up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = prevalence_2to10__mean, y = mean, col = modelname, linetype = modelname),linewidth=1) +
    expand_limits(x=0,y=0) +
    facet_wrap(~ageGroup, scales = 'free_y', nrow = 1) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff', '#d95f02ff')) +
    scale_linetype_manual(values = c("solid", "solid","solid","dashed")) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(expand = expansion(mult = c(0, 0))) +
    customTheme +
    labs(x = "PfPR 2to10",
         y = 'Severe Incidence\n(ppa)',
         subtitle = "") +
    theme(strip.text.x = element_blank(),
          axis.text.x = element_text(angle = 45, vjust = 1, hjust=1))
  
  pD <- pD1 / pD2
  mylayout <- "AAACCCCC
               BBBCCCCC
               BBBCCCCC
               DDDDDDDD
               DDDDDDDD"
  
  pABCD <- (pA+pB+pC+pD)+plot_layout(design=mylayout)
  pABCD
  ggsave(plot = pABCD, filename = file.path(getwd(), paste('Figure2_CM', ii, 'FEB25_noComorbidities.pdf',sep="")), height = 17.89, width = 34.13)
  ggsave(plot = pABCD, filename = file.path(getwd(), paste('Figure2_CM', ii, 'FEB25_noComorbidities.png',sep="")), height = 17.89, width = 34.13)
}
pABCD
