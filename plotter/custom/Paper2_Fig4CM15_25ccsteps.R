### Carrying Capacity Figure
setwd("~/MultiMalModPy")
library(ggplot2)
library(dplyr)
library(data.table)
library(tidyr)
library(patchwork)
source('utility/functions.R')
theme_set(theme_bw())
datetoday <- Sys.Date()

customTheme <- f_getCustomTheme() +
  theme(panel.grid.minor = element_blank())

mmmpy_models <- c("EMOD", "malariasimulation", "OpenMalaria")

# Load simulation outputs  CCStep_daily.csv-------------------------------
dat_inc_em <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250403_production/sims_dynamic_perennial_ccstep_14_29_52_25_35_no_importation'),
                            modelname = c('EMOD'), ccstep=TRUE)
dat_inc_om <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250403_production/sims_dynamic_perennial_ccstep_12_09_51_25_35'),
                            modelname = c('OpenMalaria'), ccstep=TRUE)
#dat_inc_ms <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250402_production/sims_dynamic_perennial_ccstep_16_08_30_25_35'),
#                            modelname = c('malariasimulation'), ccstep=TRUE)
dat_inc_ms <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250403_production/sims_dynamic_perennial_ccstep_09_52_40_25_35_no_mpv'),
                                  modelname = c('malariasimulation'), ccstep=TRUE)

dat_inc <- rbind(dat_inc_em, dat_inc_om, dat_inc_ms, fill=TRUE)
rm(dat_inc_em, dat_inc_ms, dat_inc_ms_nompv, dat_inc_om)
dat_inc <- dat_inc %>%
  filter(cm_clinical == 0.15) %>%
  group_by(timestep,cm_clinical,seasonality, modelname, cc_title, ccstep, target_output_values) %>%
  summarise(prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95),
            simulatedEIR__mean = mean(simulatedEIR),
            simulatedEIR__min = quantile(simulatedEIR, 0.05),
            simulatedEIR__up = quantile(simulatedEIR, 0.95),
            n_total_mos_pop__mean = mean(n_total_mos_pop),
            n_total_mos_pop__min = quantile(n_total_mos_pop, 0.05),
            n_total_mos_pop__up = quantile(n_total_mos_pop, 0.95),
            clinical_incidence__mean = mean(clinical_incidence),
            clinical_incidence__min = quantile(clinical_incidence, 0.05),
            clinical_incidence__up = quantile(clinical_incidence, 0.95)) %>%
  ungroup()

cc_title <-  c("25%-35%")
dat_inc$modelname <- factor(dat_inc$modelname, levels = mmmpy_models)
dat_inc$cc_title <- factor(dat_inc$cc_title, levels = cc_title, labels = c("25% to 35%"))

pA <- dat_inc %>%
  filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
  filter(cc_title %in% c("25% to 35%")) %>%
  ggplot() + 
  geom_ribbon(aes(x = timestep, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = timestep, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_inc$ccstep, dat_inc$target_output_values), color='#696969',linetype='dotted')+
  scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', '#d95f02ff')) +
  scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
  labs(title = "A",
       x = "Years since perturbation",
       y = expression('PfPR'[2-10]),
       color = 'Model',
       fill = 'Model',
       linetype= 'Model') +
  customTheme
pA


rm(dat_inc)

dat_dec_em <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250403_production/sims_dynamic_perennial_ccstep_15_49_48_25_15_no_importation'),
                            modelname = c('EMOD'), ccstep=TRUE)
dat_dec_om <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250403_production/sims_dynamic_perennial_ccstep_12_12_00_25_15'),
                            modelname = c('OpenMalaria'), ccstep=TRUE)

#dat_dec_ms <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250402_production/sims_dynamic_perennial_ccstep_16_10_18_25_15'),
#                            modelname = c('malariasimulation'), ccstep=TRUE)
dat_dec_ms <- get_output_df(file.path('/gpfs/projects/b1139/emod-om/simulation_outputs/rer4177/20250403_production/sims_dynamic_perennial_ccstep_09_54_39_25_15_no_mpv'),
                                  modelname = c('malariasimulation'), ccstep=TRUE)

dat_dec <- rbind(dat_dec_em, dat_dec_om, dat_dec_ms,fill=TRUE)
rm(dat_dec_em,dat_dec_ms, dat_dec_ms_nompv, dat_dec_om)
dat_dec <- dat_dec %>%
  filter(cm_clinical == 0.15) %>%
  group_by(timestep,cm_clinical,seasonality, modelname, cc_title, ccstep, target_output_values) %>%
  summarise(prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95),
            simulatedEIR__mean = mean(simulatedEIR),
            simulatedEIR__min = quantile(simulatedEIR, 0.05),
            simulatedEIR__up = quantile(simulatedEIR, 0.95),
            n_total_mos_pop__mean = mean(n_total_mos_pop),
            n_total_mos_pop__min = quantile(n_total_mos_pop, 0.05),
            n_total_mos_pop__up = quantile(n_total_mos_pop, 0.95),
            clinical_incidence__mean = mean(clinical_incidence),
            clinical_incidence__min = quantile(clinical_incidence, 0.05),
            clinical_incidence__up = quantile(clinical_incidence, 0.95)) %>%
  ungroup()


cc_title <-  c("25%-15%")
dat_dec$modelname <- factor(dat_dec$modelname, levels = mmmpy_models, labels = mmmpy_models)
dat_dec$cc_title <- factor(dat_dec$cc_title, levels = cc_title, labels = c("25% to 15%"))

pB<- dat_dec %>%
  filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
  filter(cc_title %in% c("25% to 15%")) %>%
  ggplot() + 
  geom_ribbon(aes(x = timestep, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname, linetype=modelname), alpha = 0.1) +
  geom_line(aes(x = timestep, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_dec$ccstep, dat_dec$target_output_values), color='#696969',linetype='dotted')+
  scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', '#d95f02ff')) +
  scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
  labs(title = "B",
       x = "Years since perturbation",
       y = expression('PfPR'[2-10]),
       color = 'Model',
       fill = 'Model',
       linetype = 'Model') +
  customTheme
pB



#Saving Outputs
mylayout <- "A
             B"

pAB <- (pA+pB)+plot_layout(design=mylayout)
pAB
ggsave(plot = pAB,filename = file.path(getwd(), 'Figure4_CM15.pdf'), height = 15, width = 22)
ggsave(plot = pAB, filename = file.path(getwd(), 'Figure4_CM15.png'), height = 15, width = 22)
# pABm <- (pAm+pBm)+plot_layout(design=mylayout)
# pABm
# 
# pABe <- (pAe+pBe)+plot_layout(design=mylayout)
# pABe
# 
# pABc <- (pAc+pBc)+plot_layout(design=mylayout)
# pABc



# 
# 
# pAm <- dat_inc %>%
#   filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
#   filter(cc_title %in% c("25% to 35%")) %>%
#   ggplot() + 
#   geom_ribbon(aes(x = timestep, ymin = n_total_mos_pop__min, ymax = n_total_mos_pop__up, fill = modelname), alpha = 0.1) +
#   geom_line(aes(x = timestep, y = n_total_mos_pop__mean, color = modelname, linetype = modelname)) +  
#   scale_color_manual(values = c('#1b9e77ff','#7570b3ff', '#d95f02ff')) +
#   scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', '#d95f02ff')) +
#   scale_linetype_manual(values = c("solid", "solid","dashed","solid")) +
#   scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
#   labs(title = "A",
#        x = "Years since perturbation",
#        y = expression('Mosquito Population'),
#        color = 'Model',
#        fill = 'Model',
#        linetype= 'Model') +
#   customTheme
# pAm
# 
# pAc <- dat_inc %>%
#   filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
#   filter(cc_title %in% c("25% to 35%")) %>%
#   ggplot() + 
#   geom_ribbon(aes(x = timestep, ymin = clinical_incidence__min, ymax = clinical_incidence__up, fill = modelname), alpha = 0.1) +
#   geom_line(aes(x = timestep, y = clinical_incidence__mean, color = modelname, linetype = modelname)) +  
#   scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#7570b3aa', '#d95f02ff')) +
#   scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', 'black', '#d95f02ff')) +
#   scale_linetype_manual(values = c("solid", "solid","dashed","solid")) +
#   scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
#   labs(title = "A",
#        x = "Years since perturbation",
#        y = expression('Clinical Incidence'),
#        color = 'Model',
#        fill = 'Model',
#        linetype= 'Model') +
#   customTheme
# pAc
# 
# pAe <- dat_inc %>%
#   filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
#   filter(cc_title %in% c("25% to 35%")) %>%
#   ggplot() + 
#   geom_ribbon(aes(x = timestep, ymin = simulatedEIR__min, ymax = simulatedEIR__up, fill = modelname), alpha = 0.1) +
#   geom_line(aes(x = timestep, y = simulatedEIR__mean, color = modelname, linetype = modelname)) +  
#   scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#7570b3aa', '#d95f02ff')) +
#   scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', 'black', '#d95f02ff')) +
#   scale_linetype_manual(values = c("solid", "solid","dashed","solid")) +
#   scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
#   labs(title = "A",
#        x = "Years since perturbation",
#        y = expression('Simulated EIR'),
#        color = 'Model',
#        fill = 'Model',
#        linetype= 'Model') +
#   customTheme
# pAe
# 
# pBc <- dat_dec %>%
#   filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
#   filter(cc_title %in% c("25% to 15%")) %>%
#   ggplot() + 
#   geom_ribbon(aes(x = timestep, ymin = clinical_incidence__min, ymax = clinical_incidence__up, fill = modelname, linetype=modelname), alpha = 0.1) +
#   geom_line(aes(x = timestep, y = clinical_incidence__mean, color = modelname, linetype = modelname)) +  
#   geom_hline(yintercept = c(dat_dec$ccstep, dat_dec$target_output_values), color='#696969',linetype='dotted')+
#   scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#7570b3aa', '#d95f02ff')) +
#   scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', 'black', '#d95f02ff')) +
#   scale_linetype_manual(values = c("solid", "solid","dashed","solid")) +
#   scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
#   labs(title = "B",
#        x = "Years since perturbation",
#        y = expression('Clinical Incidence'),
#        color = 'Model',
#        fill = 'Model',
#        linetype = 'Model') +
#   customTheme
# pBc
# 
# pBe <- dat_dec %>%
#   filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
#   filter(cc_title %in% c("25% to 15%")) %>%
#   ggplot() + 
#   geom_ribbon(aes(x = timestep, ymin = simulatedEIR__min, ymax = simulatedEIR__up, fill = modelname, linetype=modelname), alpha = 0.1) +
#   geom_line(aes(x = timestep, y = simulatedEIR__mean, color = modelname, linetype = modelname)) +  
#   geom_hline(yintercept = c(dat_dec$ccstep, dat_dec$target_output_values), color='#696969',linetype='dotted')+
#   scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#7570b3aa', '#d95f02ff')) +
#   scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', 'black', '#d95f02ff')) +
#   scale_linetype_manual(values = c("solid", "solid","dashed","solid")) +
#   scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
#   labs(title = "B",
#        x = "Years since perturbation",
#        y = expression('Simulated EIR'),
#        color = 'Model',
#        fill = 'Model',
#        linetype = 'Model') +
#   customTheme
# pBe 
# 
# pBm <- dat_dec %>%
#   filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
#   filter(cc_title %in% c("25% to 15%")) %>%
#   ggplot() + 
#   geom_ribbon(aes(x = timestep, ymin = n_total_mos_pop__min, ymax = n_total_mos_pop__up, fill = modelname, linetype=modelname), alpha = 0.1) +
#   geom_line(aes(x = timestep, y = n_total_mos_pop__mean, color = modelname, linetype = modelname)) +  
#   geom_hline(yintercept = c(dat_dec$ccstep, dat_dec$target_output_values), color='#696969',linetype='dotted')+
#   scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#7570b3aa', '#d95f02ff')) +
#   scale_fill_manual(values = c('#1b9e77ff','#7570b3ff', 'black', '#d95f02ff')) +
#   scale_linetype_manual(values = c("solid", "solid","dashed","solid")) +
#   scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
#   labs(title = "B",
#        x = "Years since perturbation",
#        y = expression('Mosquito Population'),
#        color = 'Model',
#        fill = 'Model',
#        linetype = 'Model') +
#   customTheme
# pBm
