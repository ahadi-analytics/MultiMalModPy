### Carrying Capacity Figure
setwd("~/model-characterization")
library(ggplot2)
library(dplyr)
library(data.table)
library(tidyr)
library(patchwork)
source('functions.R')
theme_set(theme_bw())
datetoday <- Sys.Date()

customTheme <- f_getCustomTheme() +
  theme(legend.position = "right",
        panel.grid.major = element_blank(),
        panel.grid.minor = element_blank())

if (Sys.getenv("OS") == "Windows_NT") {
  box <- 'NU-malaria-team Dropbox'
  projdir <- file.path(Sys.getenv('USERPROFILE'), box, 'projects/EMOD_OM/simulation_outputs')
}else {
  username <- Sys.getenv('USER') #Sys.getenv('USERNAME')
  projdir <- file.path('/projects/b1139/emod-om/simulation_outputs', username)
}



# Load simulation outputs  CCStep_daily.csv-------------------------------
cc_path <- file.path(projdir, 'test_sims_20240731/sims_dynamic_perennial_cc_step_16_02_14') #Note: missing data  commited so code is available
cc_noImp <- file.path(projdir, 'test_sims_20240731/sims_dynamic_perennial_cc_step_16_02_14') #Note: missing data, commited so code is available
modelname <- c("EMOD", "OpenMalaria", "MalSim")

dat_cc <- get_output_df(cc_path, modelname = modelname, cc=TRUE) # with importation
dat_cc_noImp <- get_output_df(cc_noImp_path, modelname = modelname, cc=TRUE) # with no importation WILL BE DIFFERENT LATER, 

dat_cc <- dat_cc %>%
  group_by(timestep, cm_clinical,seasonality, modelname, cc_title, cc_change, output_target) %>%
  summarise(prevalence_2to10__mean = mean(prevalence_2to10),
            prevalence_2to10__min = quantile(prevalence_2to10, 0.05),
            prevalence_2to10__up = quantile(prevalence_2to10, 0.95)
            ) %>%
  ungroup()

dat_cc$date <- as.Date(dat_cc$timestep-1, origin = "2000-01-01")
cc_title <-  c("10%-25%", "10%-50%", "25%-50%", "25%-10%", "50%-10%", "50%-25%")
dat_cc$modelname <- factor(dat_cc$modelname, levels = modelname, labels = c("EMOD", "OpenMalaria", "MalSim"))
dat_cc$cc_title <- factor(dat_cc$cc_title, levels = cc_title, labels = c("10%-25%", "10%-50%", "25%-50%", "25%-10%", "50%-10%", "50%-25%"))

dat_cc_noImp$date <- as.Date(dat_cc_noImp$timestep-1, origin = "2000-01-01")
cc_title <-  c("50%-10%")
dat_cc_noImp$modelname <- factor(dat_cc_noImp$modelname, levels = modelname, labels = c("EMOD", "OpenMalaria", "MalSim"))
dat_cc_noImp$cc_title <- factor(dat_cc_noImp$cc_title, levels = cc_title, labels = c("50%-10%"))


pA <- dat_cc %>%
  filter(cm_clinical == 0.0, seasonality == 'perennial') %>%
  filter(cc_title %in% c("10%-25%", "10%-50%", "25%-50%")) %>%
  ggplot() + 
  geom_ribbon(aes(x = date, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = date, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_cc$cc_change, dat_cc$output_target), color='#696969',linetype='dotted')+
  facet_wrap(~ cc_title, nrow=1) +   
  scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_x_date(date_breaks = "5 years", date_labels = "%Y",expand = expansion(mult = c(0, 0))) +
  labs(title = "A: Carrying Capacity Increase - w/ Importation (pop = 10,000)",
       x = "Years",
       y = expression('PfPR'[2-10]),
       color = 'Model') +
  customTheme

pB<- dat_cc %>%
  filter(cm_clinical == 0.0, seasonality == 'perennial') %>%
  filter(cc_title %in% c("25%-10%", "50%-10%", "50%-25%")) %>%
  ggplot() + 
  geom_line(aes(x = date, y = prevalence_2to10__mean, color = modelname)) +  
  geom_hline(yintercept = c(dat_cc$cc_change, dat_cc$output_target), color='#696969',linetype='dotted')+
  facet_wrap(~ cc_title, nrow=1) +   
  scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_x_date(date_breaks = "5 years", date_labels = "%Y",expand = expansion(mult = c(0, 0))) +
  labs(title = "B: Carrying Capacity Decrease - w/ Importation (pop = 10,000)",
       x = "Years",
       y = expression('PfPR'[2-10]),
       color = 'Model') +
  customTheme

pC <- dat_cc_noImp %>%
  filter(cc_title == "50%-10%") %>%
  ggplot() + 
  geom_line(aes(x = date, y = prevalence_2to10, group=seed), 
            alpha = 0.1) +  
  geom_hline(yintercept = c(dat_cc_noImp$cc_change, dat_cc_noImp$output_target), color='#696969',linetype='dotted')+
  facet_wrap(modelname ~ cc_title, nrow=1) +   
  labs(title = "C: Carrying Capacity Decrease w/o Importation (pop = 10,000)",
       x = "Years",
       y = expression('PfPR'[2-10]),
       color = 'Simulation') +
  scale_x_date(date_breaks = "5 years", date_labels = "%Y",expand = expansion(mult = c(0, 0))) +
  customTheme + 
  theme(legend.position="none")

#Saving Outputs
mylayout <- "A
             B
             C"

pABC <- (pA+pB+pC)+plot_layout(design=mylayout)
pABC
ggsave(plot = pABC,filename = file.path(getwd(), 'Figure4.pdf'), height = 15, width = 22)
ggsave(plot = pABC, filename = file.path(getwd(), 'Figure4.png'), height = 15, width = 22)

# dat_elim <- fread(file.path(projdir,exp_name, 'elimination.csv'))
# dat_elim$modelname <- factor(dat_elim$modelname, levels = modelname, labels = c("EMOD", "OpenMalaria", "MalSim"))
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
