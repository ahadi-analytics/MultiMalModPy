### 'Baseline' figure
setwd("~/model-characterization")
library(ggplot2)
library(dplyr)
library(data.table)
library(tidyr)
library(patchwork)

source('utility/functions.R')
theme_set(theme_bw())

modelname <- c("EMOD", "malariasimulation","OpenMalaria")
agegrps <- c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100')

customTheme <- f_getCustomTheme() +
  theme(legend.position = "None",
        panel.grid.minor = element_blank())

# Load simulation outputs  -------------------------------
dat_em_45 <- get_output_df("/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240827/sims_dynamic_perennial__12_07_01", modelname = "EMOD")
dat_ms_45 <- get_output_df("/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240827/sims_dynamic_perennial__12_07_01", modelname = "malariasimulation")
dat_ms_45 <- dat_ms_45 %>%
  mutate(severe_incidence = case_when(modelname=='malariasimulation' ~ severe_incidence * (0.5 * cm_severe + (1-cm_severe)),
                                      .default = severe_incidence))
dat_om_45 <- get_output_df("/projects/b1139/emod-om/simulation_outputs/rer4177/20241011_production/sims_dynamic_perennial__21_32_32", modelname = "OpenMalaria")
dat_total <- rbind(dat_om_45, dat_em_45, dat_ms_45, fill=TRUE)
rm(dat_ms_45, dat_em_45, dat_om_45)

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
  mutate(severe_incidence = case_when(modelname=='malariasimulation' ~ severe_incidence * (0.5 * (cm_clinical*1.15) + (1-(cm_clinical*1.15))),
                                      .default = severe_incidence))
i_em <- fread(file.path('/home/rer4177/model-characterization/target_calibration/EMOD/interpolation_data.csv'))
i_om <- fread(file.path('/home/rer4177/model-characterization/target_calibration/OpenMalaria/interpolation_data.csv'))
i_full <- rbind(i_om, i_em, i_ms, fill=TRUE)
rm(i_om, i_em, i_ms)



for (ii in unique(dat_total$cm_clinical)){
  dat_p <- filter(dat_total, cm_clinical == ii, seasonality == 'perennial')
  i_p <- filter(i_full, cm_clinical == ii, seasonality == 'perennial', pop_size == 50000, importation == FALSE)
  i_p <- filter(i_p, simulatedEIR >= 0.01)
  # ------------------------------ Figure 2A and B ------------------------------
  pA <- i_p %>%
    ggplot() +
    #geom_ribbon(aes(x = simulatedEIR, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = simulatedEIR, y = prevalence_2to10, col = modelname),linewidth=1.25) +
    expand_limits(y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(trans = "log10",expand = expansion(mult = c(0, 0)), breaks=c(0.1,1,10,100,1000),
                       labels = c(0.1, 1,10,100,1000),limits = c(0.1,1000)) +
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
    expand_limits(y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(expand = expansion(mult = c(0, 0))) +
    customTheme +
    theme(panel.grid.minor = element_blank())+
    labs(y = "Clinical Incidence\n(ppa)",
         x = "",
         title = "",
         subtitle = "")
  pB2 <- i_p %>%
    mutate(severe_incidence = severe_incidence * 100) %>%
    ggplot() +
    #geom_ribbon(aes(x = simulatedEIR, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.15) +
    geom_line(aes(x = prevalence_2to10, y = severe_incidence, col = modelname),linewidth=1.25) +
    expand_limits(y=0) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_continuous(expand = expansion(mult = c(0, 0))) +
    customTheme +
    theme(panel.grid.minor = element_blank())+
    labs(y = "Severe Incidence\n(ppa)",
         x = expression('PfPR'[2-10]),
         title = "",
         subtitle = "")
  pB <- pB1 / pB2
  pB
  
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
      modelname == 'OpenMalaria' & output_target %in% pfpr_values[1] ~ pfpr_labels[1],
      modelname == 'OpenMalaria' & output_target %in% pfpr_values[2] ~ pfpr_labels[2],
      modelname == 'OpenMalaria' & output_target %in% pfpr_values[3] ~ pfpr_labels[3],
      modelname == 'OpenMalaria' & output_target %in% pfpr_values[4] ~ pfpr_labels[4],
      modelname == 'Original' & output_target %in% pfpr_values[1] ~ pfpr_labels[1],
      modelname == 'Original' & output_target %in% pfpr_values[2] ~ pfpr_labels[2],
      modelname == 'Original' & output_target %in% pfpr_values[3] ~ pfpr_labels[3],
      modelname == 'Original' & output_target %in% pfpr_values[4] ~ pfpr_labels[4],
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
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
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
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
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
    geom_line(aes(x = ageGroup, y = mean, col = modelname, group = modelname),linewidth=1.25) +
    expand_limits(y=0) +
    facet_wrap(~ pfpr_grp, scales = 'free', nrow=1)+
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
    scale_x_discrete(expand = expansion(mult = c(0, 0))) +
    customTheme +
    labs(x = "Age (years)",
         y = 'Severe Incidence\n(ppa)',
         title = "",
         subtitle = "") +
    theme(strip.text.x = element_blank(),
          axis.text.x = element_text(angle = 45,vjust = 1, hjust=1))
  
  
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
    expand_limits(y=0) +
    facet_wrap(~ageGroup, scales = 'free_y', nrow = 1) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
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
    geom_line(aes(x = prevalence_2to10__mean, y = mean, col = modelname),linewidth=1) +
    expand_limits(y=0) +
    facet_wrap(~ageGroup, scales = 'free_y', nrow = 1) +
    scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
    scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
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
  ggsave(plot = pABCD, filename = file.path(getwd(), paste('Figure2_CM', ii, '_11OCT24.pdf',sep="")), height = 17.89, width = 34.13)
  ggsave(plot = pABCD, filename = file.path(getwd(), paste('Figure2_CM', ii, '_11OCT24.png',sep="")), height = 17.89, width = 34.13)
}
pABCD
