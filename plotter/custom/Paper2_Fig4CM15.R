### Carrying Capacity Figure
setwd("~/model-characterization")
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
dat_inc <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250219_production/sims_dynamic_perennial_cc_step_09_56_28_increasing/'),
                                    modelname = c('EMOD','OpenMalaria'), ccstep=TRUE)
dat_inc_ms <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250227_production/sims_dynamic_perennial_cc_step_09_15_52'),
                            modelname = c('malariasimulation'), ccstep=TRUE)
dat_inc <- rbind(dat_inc, dat_inc_ms, fill=TRUE)
dat_inc <- dat_inc %>%
  filter(cm_clinical == 0.15) %>%
  group_by(timestep,cm_clinical,seasonality, modelname, cc_title, cc_change, target_output_values) %>%
  summarise(prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95)) %>%
  ungroup()

cc_title <-  c("10%-25%", "10%-50%", "25%-50%")
dat_inc$modelname <- factor(dat_inc$modelname, levels = mmmpy_models)
dat_inc$cc_title <- factor(dat_inc$cc_title, levels = cc_title, labels = c("10% to 25%", "10% to 50%", "25% to 50%"))

pA <- dat_inc %>%
  filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
  filter(cc_title %in% c("10% to 25%", "10% to 50%", "25% to 50%")) %>%
  ggplot() + 
  geom_ribbon(aes(x = timestep, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = timestep, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_inc$cc_change, dat_inc$target_output_values), color='#696969',linetype='dotted')+
  facet_wrap(~ cc_title, nrow=1) +   
  scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
  labs(title = "A",
       x = "Years since perturbation",
       y = expression('PfPR'[2-10]),
       color = 'Model',
       fill = 'Model') +
  customTheme
pA


dat_dec <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250219_production/sims_dynamic_perennial_cc_step_09_52_27_decreasing_and_OM_noImportation'),
                                  modelname = c('EMOD','OpenMalaria'), ccstep=TRUE)

dat_dec_ms <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250227_production/sims_dynamic_perennial_cc_step_09_12_53'),
                           modelname = c('malariasimulation'), ccstep=TRUE)
dat_dec <- rbind(dat_dec, dat_dec_ms, fill=TRUE)
dat_dec <- dat_dec %>%
  filter(cm_clinical == 0.15) %>%
  group_by(timestep,cm_clinical,seasonality, modelname, cc_title, cc_change, target_output_values) %>%
  summarise(prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95)) %>%
  ungroup()


cc_title <-  c("25%-10%", "50%-10%", "50%-25%")
dat_dec$modelname <- factor(dat_dec$modelname, levels = mmmpy_models, labels = c("EMOD*", "malariasimulation", "OpenMalaria"))
dat_dec$cc_title <- factor(dat_dec$cc_title, levels = cc_title, labels = c("25% to 10%", "50% to 10%", "50% to 25%"))

pB<- dat_dec %>%
  filter(cm_clinical == 0.15, seasonality == 'perennial', timestep<=20075) %>%
  filter(cc_title %in% c("25% to 10%", "50% to 10%", "50% to 25%")) %>%
  ggplot() + 
  geom_ribbon(aes(x = timestep, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = timestep, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_dec$cc_change, dat_dec$target_output_values), color='#696969',linetype='dotted')+
  facet_wrap(~ cc_title, nrow=1) +   
  scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_x_continuous(breaks = c(1825,3650,5475,7300,9125,10950,12775,14600,16425,18250,20075), labels = c('0','','10','','20','','30','','40','','50'), expand = expansion(mult = c(0, 0))) +
  labs(title = "B",
       x = "Years since perturbation",
       y = expression('PfPR'[2-10]),
       color = 'Model',
       fill = 'Model') +
  customTheme
pB
#Saving Outputs
mylayout <- "A
             B"

pAB <- (pA+pB)+plot_layout(design=mylayout)
pAB
ggsave(plot = pAB,filename = file.path(getwd(), 'Figure4_CM15.pdf'), height = 15, width = 22)
ggsave(plot = pAB, filename = file.path(getwd(), 'Figure4_CM15.png'), height = 15, width = 22)
