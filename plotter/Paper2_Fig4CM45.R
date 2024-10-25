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
  theme(legend.position = "right",
        panel.grid.minor = element_blank())

mmmpy_models <- c("EMOD", "malariasimulation", "OpenMalaria")

# Load simulation outputs  CCStep_daily.csv-------------------------------
dat_inc_noImp_emod <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240906/sims_dynamic_perennial_cc_step_11_10_12'),
                                  modelname = 'EMOD', ccstep=TRUE)
dat_inc_noImp_malariasimulation <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20241016_production/sims_dynamic_perennial_cc_step_08_59_27'),
                                               modelname = 'malariasimulation', ccstep=TRUE)
dat_inc_noImp_malariasimulation <- dat_inc_noImp_malariasimulation %>%
  filter(cm_clinical == 0.45)
dat_inc_noImp_openmalaria <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20241011_production/sims_dynamic_perennial_cc_step_21_32_47'),
                                         modelname = 'OpenMalaria', ccstep=TRUE)
dat_inc_noImp <- rbind(dat_inc_noImp_emod, dat_inc_noImp_malariasimulation, dat_inc_noImp_openmalaria, fill=TRUE)
rm(dat_inc_noImp_emod, dat_inc_noImp_malariasimulation, dat_inc_noImp_openmalaria)

dat_inc_noImp <- dat_inc_noImp %>%
  group_by(timestep,cm_clinical,seasonality, modelname, cc_title, cc_change, output_target) %>%
  summarise(prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95)
  ) %>%
  ungroup()

cc_title <-  c("10%-25%", "10%-50%", "25%-50%")
dat_inc_noImp$modelname <- factor(dat_inc_noImp$modelname, levels = mmmpy_models)
dat_inc_noImp$cc_title <- factor(dat_inc_noImp$cc_title, levels = cc_title, labels = c("10% to 25%", "10% to 50%", "25% to 50%"))

pA <- dat_inc_noImp %>%
  filter(cm_clinical == 0.45, seasonality == 'perennial', timestep<=20075) %>%
  filter(cc_title %in% c("10% to 25%", "10% to 50%", "25% to 50%")) %>%
  ggplot() + 
  geom_ribbon(aes(x = timestep, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = timestep, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_inc_noImp$cc_change, dat_inc_noImp$output_target), color='#696969',linetype='dotted')+
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


dat_dec_imp_emod <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240906/sims_dynamic_perennial_cc_step_11_10_12'),
                                         modelname = 'EMOD', ccstep=TRUE)
dat_dec_malariasimulation <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20241016_production/sims_dynamic_perennial_cc_step_08_59_27'),
                                         modelname = 'malariasimulation', ccstep=TRUE)
dat_dec_malariasimulation <- dat_dec_malariasimulation %>%
  filter(cm_clinical == 0.45)
dat_dec_imp_openmalaria <- get_output_df(file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20241011_production/sims_dynamic_perennial_cc_step_23_39_21'),
                                         modelname = 'OpenMalaria', ccstep=TRUE)
dat_dec_imp <- rbind(dat_dec_imp_emod, dat_dec_malariasimulation, dat_dec_imp_openmalaria, fill=TRUE)
rm(dat_dec_imp_emod, dat_dec_malariasimulation, dat_dec_imp_openmalaria)

dat_dec_imp <- dat_dec_imp %>%
  group_by(timestep,cm_clinical,seasonality, modelname, cc_title, cc_change, output_target) %>%
  summarise(prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95)
  ) %>%
  ungroup()


cc_title <-  c("25%-10%", "50%-10%", "50%-25%")
dat_dec_imp$modelname <- factor(dat_dec_imp$modelname, levels = mmmpy_models, labels = c("EMOD*", "malariasimulation", "OpenMalaria*"))
dat_dec_imp$cc_title <- factor(dat_dec_imp$cc_title, levels = cc_title, labels = c("25% to 10%", "50% to 10%", "50% to 25%"))

pB<- dat_dec_imp %>%
  filter(cm_clinical == 0.45, seasonality == 'perennial', timestep<=20075) %>%
  filter(cc_title %in% c("25% to 10%", "50% to 10%", "50% to 25%")) %>%
  ggplot() + 
  geom_ribbon(aes(x = timestep, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = timestep, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_dec_imp$cc_change, dat_dec_imp$output_target), color='#696969',linetype='dotted')+
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
ggsave(plot = pAB,filename = file.path(getwd(), 'Figure4_CM45.pdf'), height = 15, width = 22)
ggsave(plot = pAB, filename = file.path(getwd(), 'Figure4_CM45.png'), height = 15, width = 22)

# dat_elim <- fread(file.path(projdir,exp_name, 'elimination.csv'))
# dat_elim$modelname <- factor(dat_elim$modelname, levels = mmmpy_models)
# pC <- dat_elim %>%
#   ggplot() + 
#   geom_line(aes(x = pop_size, y = elimination_ratio, color = modelname)) +  
#   geom_point(aes(x = pop_size, y = elimination_ratio, color = modelname)) +  
#   scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
#   scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
#   facet_wrap(~ cc_title, nrow=1) +   
#   labs(title = "C: Probability of Elimination w/o Importation (population on X)",
#        x = "Population Size",
#        y = "% of Sims that reached Elimination",
#        color = 'Model') +
#   customTheme
