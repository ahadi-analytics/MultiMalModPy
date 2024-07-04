### Seasonality figure
setwd("~/model-characterization")
library(ggplot2)
library(dplyr)
library(data.table)
library(scales)
library(cowplot)
library(tidyr)
library(gridExtra)
library(lubridate)
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

projdir <- file.path(projdir, 'test_sims_20240626')
exp_name <- "sims_dynamic_seasonal__13_03_24"
modelname <- c("EMOD", "OpenMalaria", "MalSim")

# Load simulation outputs  BENCHMARK-------------------------------
dat_s <- get_output_df(file.path(projdir,exp_name), modelname = modelname, timeseries = TRUE, fiveday=TRUE)

dat_s <- dat_s %>%
  group_by(day, year, eir, cm_clinical, ageGroup, seasonality, modelname) %>%
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
            severe_incidence__up = quantile(severe_incidence, 0.95),
            n_total_mos_pop__mean = mean(n_total_mos_pop),
            n_total_mos_pop__min = quantile(n_total_mos_pop, 0.05),
            n_total_mos_pop__up = quantile(n_total_mos_pop, 0.95)) %>%
  ungroup()


dat_s$ageGroup <- factor(dat_s$ageGroup,
                         levels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'),
                         labels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'))

dat_s$modelname <- factor(dat_s$modelname, levels = modelname, labels = c("EMOD", "OpenMalaria", "MalSim"))

dat_s <- dat_s %>%
  mutate(day = ((day+180) %% 365)) %>%
  mutate(times = (day+365*(year-2000)))

#Setting up which EIRS have pfpr2to10 values closest to our targets
pfpr_labels <- c(0.05,0.1,0.25,0.5)
emod_eirs <- c(1,1.25,3,10)
om_eirs <- c(0.25,1,2.5,8)
malsim_eirs <- c(0.5,1.25,5,22)
sel_eirs <- c(1,5,10,100)

dat_s <- dat_s %>%
  mutate(pfpr_grp = case_when(
    modelname == 'EMOD' & eir %in% emod_eirs[1] ~ pfpr_labels[1],
    modelname == 'EMOD' & eir %in% emod_eirs[2] ~ pfpr_labels[2],
    modelname == 'EMOD' & eir %in% emod_eirs[3] ~ pfpr_labels[3],
    modelname == 'EMOD' & eir %in% emod_eirs[4] ~ pfpr_labels[4],
    ## OM
    modelname == 'OpenMalaria' & eir %in% om_eirs[1] ~ pfpr_labels[1],
    modelname == 'OpenMalaria' & eir %in% om_eirs[2] ~ pfpr_labels[2],
    modelname == 'OpenMalaria' & eir %in% om_eirs[3] ~ pfpr_labels[3],
    modelname == 'OpenMalaria' & eir %in% om_eirs[4] ~ pfpr_labels[4],
    ## MalSim
    modelname == 'MalSim' & eir %in% malsim_eirs[1] ~ pfpr_labels[1],
    modelname == 'MalSim' & eir %in% malsim_eirs[2] ~ pfpr_labels[2],
    modelname == 'MalSim' & eir %in% malsim_eirs[3] ~ pfpr_labels[3],
    modelname == 'MalSim' & eir %in% malsim_eirs[4] ~ pfpr_labels[4]),
    pfpr_grp = factor(pfpr_grp, levels = pfpr_labels, labels = pfpr_labels))

#Generate Tables if you would like a quick sanity check
#table(dat_s$ageGroup)
#table(dat_s$eir, dat_s$modelname)
#table(dat_s$eir, dat_ss$modelname)
#table(dat_s$day, dat_ss$modelname)

pA <- dat_s %>%
  filter(year == max(year)) %>%
  filter(ageGroup %in% '0-100') %>%
  filter(eir %in% c(20)) %>%
  ggplot() +
  geom_ribbon(aes(x = day, ymin = simulatedEIR__min, ymax = simulatedEIR__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = day, y = simulatedEIR__mean, col = modelname), linewidth = 1) +
  scale_color_manual(values = emodom_cols) +
  scale_fill_manual(values = emodom_cols) +
  scale_y_continuous(expand = expansion(mult = c(0, 0))) +
  scale_x_continuous(expand = expansion(mult = c(0, 0))) +
  labs(y = "Simulated EIR",
       x = "Days",
       color = 'Model',
       fill = 'Model',
       title = 'EIR = 20',
       caption = 'All Ages') +
  customTheme +
  theme(legend.position = c(.1, .8))

pB <- dat_s %>%
  filter(year == max(year)) %>% ## FIXME
  filter(ageGroup %in% '0-100') %>%
  filter(eir %in% c(20)) %>%
  dplyr::select(year, day, eir, ageGroup, modelname,
                simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                n_total_mos_pop__mean, n_total_mos_pop__min, n_total_mos_pop__up) %>%
  pivot_longer(cols = -c(day, year, eir, ageGroup, modelname)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name,
                       levels = c('n_total_mos_pop','simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('Total Mosquito\nPopulation','Simulated EIR', 'Prevalence', 'Clinical incidence (ppa)'))) %>%
  group_by(modelname, name) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  group_by(eir, ageGroup, modelname, name) %>%
  mutate(max_y = max(mean),
         ismax = mean==max_y) %>%
  ggplot() +
  geom_ribbon(aes(x = day, ymin = min, ymax = up, fill = name), alpha = 0.1) +
  geom_point(aes(x = day, y = mean, col = name)) +
  geom_line(aes(x = day, y = mean, col = name), linewidth = 0.35) +
  scale_color_manual(values = c('#003d52','#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#003d52','#408941', '#009acd', '#fdbf11')) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  scale_x_continuous(expand = expansion(mult = c(0, 0))) +
  #geom_segment(aes(x = mean(day), y = max_y, xend = mean(day), yend = max_y),
  #             arrow = arrow(length = unit(0.5, "cm")))+
  geom_text(data = .%>%filter(ismax), 
            aes(x=day, y= max_y, col = name),
            label = 'v', size = 6, 
            hjust = 0.5, vjust = 0, 
            position=position_nudge(y=0.05)) +
  facet_wrap(~modelname, ncol = 1, strip.position = "right") +
  labs(y = "Simulated value (re-scaled)",
       x = "Days",
       col = 'Simulation Output',
       fill = 'Simulation Output',
       title = 'EIR = 20',
       caption = 'All Ages') +
  customTheme +
  theme(legend.position = 'right')


## Varying EIRs
line_cols <- c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c')



pC_pfpr <- dat_s %>%
  ungroup() %>%
  filter(ageGroup %in% '0-100') %>%
  filter(pfpr_grp %in% pfpr_labels) %>%
  select(times, pfpr_grp, ageGroup, modelname,
         simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
         prevalence__mean, prevalence__min, prevalence__up,
         clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
         n_total_mos_pop__mean, n_total_mos_pop__min, n_total_mos_pop__up) %>%
  pivot_longer(cols = -c(times, pfpr_grp, ageGroup, modelname)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(custom_col = case_when(
    name == 'simulatedEIR' & pfpr_grp == pfpr_labels[1] ~ line_cols[1],
    name == 'simulatedEIR' & pfpr_grp == pfpr_labels[2] ~ line_cols[2],
    name == 'simulatedEIR' & pfpr_grp == pfpr_labels[3] ~ line_cols[3],
    name == 'simulatedEIR' & pfpr_grp == pfpr_labels[4] ~ line_cols[4],
    # prev
    name == 'prevalence' & pfpr_grp == pfpr_labels[1] ~ line_cols[1],
    name == 'prevalence' & pfpr_grp == pfpr_labels[2] ~ line_cols[2],
    name == 'prevalence' & pfpr_grp == pfpr_labels[3] ~ line_cols[3],
    name == 'prevalence' & pfpr_grp == pfpr_labels[4] ~ line_cols[4],
    # inc
    name == 'clinical_incidence' & pfpr_grp == pfpr_labels[1] ~ line_cols[1],
    name == 'clinical_incidence' & pfpr_grp == pfpr_labels[2] ~ line_cols[2],
    name == 'clinical_incidence' & pfpr_grp == pfpr_labels[3] ~ line_cols[3],
    name == 'clinical_incidence' & pfpr_grp == pfpr_labels[4] ~ line_cols[4],
    # Mos Pop
    name == 'n_total_mos_pop' & pfpr_grp == pfpr_labels[1] ~ line_cols[1],
    name == 'n_total_mos_pop' & pfpr_grp == pfpr_labels[2] ~ line_cols[2],
    name == 'n_total_mos_pop' & pfpr_grp == pfpr_labels[3] ~ line_cols[3],
    name == 'n_total_mos_pop' & pfpr_grp == pfpr_labels[4] ~ line_cols[4])) %>%
  mutate(name = factor(name,
                       levels = c('n_total_mos_pop','simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('Total Mosquito\nPopulation','Simulated EIR', 'Prevalence', 'Clinical incidence\n(ppa)'))) %>%
  group_by(modelname, name, pfpr_grp) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_vline(xintercept = c(365,730,1095, 1465, 1825), color='#696969',linetype='dotted')+
  geom_ribbon(aes(x = times, ymin = min, ymax = up, fill = custom_col), color = 'transparent', alpha = 0.1) +
  geom_line(aes(x = times, y = mean,color=custom_col), linewidth = 1) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  scale_x_continuous(expand = expansion(mult = c(0, 0))) +
  facet_grid(name ~ modelname, scales = "free", switch = 'y') +
  labs(y = "",
       x = "Days",
       color = 'Pfpr 2-10',
       fill = 'Pfpr 2-10',
       caption = "All Ages") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing.x = unit(1, "lines"),
        panel.spacing.y = unit(0.5, "lines"),
        strip.placement = "outside") +
  theme(legend.position = 'right')+
  scale_color_manual(labels = pfpr_labels, values = c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c')) +
  scale_fill_manual(labels = pfpr_labels, values = c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c'))
pC_pfpr


pC_eir <- dat_s %>%
  ungroup() %>%
  filter(ageGroup %in% '0-100') %>%
  filter(eir %in% sel_eirs) %>%
  select(times, eir, ageGroup, modelname,
                simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
         n_total_mos_pop__mean, n_total_mos_pop__min, n_total_mos_pop__up) %>%
  pivot_longer(cols = -c(times, eir, ageGroup, modelname)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(custom_col = case_when(
                      name == 'simulatedEIR' & eir == sel_eirs[1] ~ line_cols[1],
                      name == 'simulatedEIR' & eir == sel_eirs[2] ~ line_cols[2],
                      name == 'simulatedEIR' & eir == sel_eirs[3] ~ line_cols[3],
                      name == 'simulatedEIR' & eir == sel_eirs[4] ~ line_cols[4],
                      # prev
                      name == 'prevalence' & eir == sel_eirs[1] ~ line_cols[1],
                      name == 'prevalence' & eir == sel_eirs[2] ~ line_cols[2],
                      name == 'prevalence' & eir == sel_eirs[3] ~ line_cols[3],
                      name == 'prevalence' & eir == sel_eirs[4] ~ line_cols[4],
                      # inc
                      name == 'clinical_incidence' & eir == sel_eirs[1] ~ line_cols[1],
                      name == 'clinical_incidence' & eir == sel_eirs[2] ~ line_cols[2],
                      name == 'clinical_incidence' & eir == sel_eirs[3] ~ line_cols[3],
                      name == 'clinical_incidence' & eir == sel_eirs[4] ~ line_cols[4],
                      # Mos Pop
                      name == 'n_total_mos_pop' & eir == sel_eirs[1] ~ line_cols[1],
                      name == 'n_total_mos_pop' & eir == sel_eirs[2] ~ line_cols[2],
                      name == 'n_total_mos_pop' & eir == sel_eirs[3] ~ line_cols[3],
                      name == 'n_total_mos_pop' & eir == sel_eirs[4] ~ line_cols[4])) %>%
  mutate(name = factor(name,
                       levels = c('n_total_mos_pop','simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('Total Mosquito\nPopulation','Simulated EIR', 'Prevalence', 'Clinical incidence\n(ppa)'))) %>%
  group_by(modelname, name, eir) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_vline(xintercept = c(365,730,1095, 1465, 1825), color='#696969',linetype='dotted')+
  geom_ribbon(aes(x = times, ymin = min, ymax = up, fill = custom_col), color = 'transparent', alpha = 0.1) +
  geom_line(aes(x = times, y = mean,color=custom_col), linewidth = 1) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  scale_x_continuous(expand = expansion(mult = c(0, 0))) +
  facet_grid(name ~ modelname, scales = "free", switch = 'y') +
  labs(y = "",
       x = "Days",
       color = 'Annual EIR\n(input)',
       fill = 'Annual EIR\n(input)',
       caption = "All Ages") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing.x = unit(1, "lines"),
        panel.spacing.y = unit(0.5, "lines"),
        strip.placement = "outside") +
  theme(legend.position = 'right')+
  scale_color_manual(labels = sel_eirs, values = c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c')) +
  scale_fill_manual(labels = sel_eirs, values = c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c'))
pC_eir


#Saving Outputs
mylayout <- "AAAABBBB
             AAAABBBB
             AAAABBBB
             CCCCCCCC
             CCCCCCCC
             CCCCCCCC"

pABC_pfpr <- (pA+pB+pC_pfpr)+plot_layout(design=mylayout)
pABC_pfpr
ggsave(plot = pABC_pfpr,filename = file.path(getwd(), 'Figure3_pfpr_ratio.pdf'), height = 14, width = 22)
ggsave(plot = pABC_pfpr, filename = file.path(getwd(), 'Figure3_pfpr_ratio.png'), height = 14, width = 22)

pABC_eir <- (pA+pB+pC_eir)+plot_layout(design=mylayout)
pABC_eir
ggsave(plot = pABC_eir,filename = file.path(getwd(), 'Figure3_eir_ratio.pdf'), height = 14, width = 22)
ggsave(plot = pABC_eir, filename = file.path(getwd(), 'Figure3_eir_ratio.png'), height = 14, width = 22)



#### With  EIR exploration
#pAB <- plot_grid(pA, pB, ncol = 1, labels = c('A', 'B'))
#pABC <- plot_grid(pAB, pC, ncol = 2, rel_widths = c(0.4, 1), labels = c(NA, 'C'))
#pABC
# pB_wide <- dat_s %>%
#   ungroup() %>%
#   filter(year == 2001) %>% ## FIXME
#   filter(ageGroup %in% '0-5') %>%
#   filter(eir %in% c(5)) %>%
#   dplyr::select(year, day, eir, ageGroup, modelname,
#                 simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
#                 prevalence__mean, prevalence__min, prevalence__up,
#                 clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
#                 n_total_mos_pop__mean, n_total_mos_pop__min, n_total_mos_pop__up) %>%
#   pivot_longer(cols = -c(year, day, eir, ageGroup, modelname)) %>%
#   separate(name, into = c('name', 'stat'), sep = '__') %>%
#   mutate(name = factor(name,
#                        levels = c('simulatedEIR', 'prevalence', 'clinical_incidence', 'n_total_mos_pop'),
#                        labels = c('simulated EIR', 'Prevalence', 'Clinical incidence (ppa)', 'Total Mosquito\nPopulation'))) %>%
#   group_by(modelname, name) %>%
#   mutate(value = rescale(value, to = c(0, 1))) %>%
#   pivot_wider(names_from = stat, values_from = value) %>%
#   ggplot() +
#   geom_col(data = subset(input_eir_df, year = 2001),
#            aes(x = day, y = finput_eir * 5), fill = '#ececec') +
#   geom_ribbon(aes(x = day, ymin = min, ymax = up, fill = name), alpha = 0.18) +
#   geom_line(aes(x = day, y = mean, col = name), linewidth = 1) +
#   scale_color_manual(values = c('#408941', '#009acd', '#fdbf11','#003d52')) +
#   scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11','#003d52')) +
#   scale_y_continuous(expand = expansion(mult = c(0, .1))) +
#   #scale_x_date(date_breaks = '1 months', date_labels = '%b', expand = c(0, 0),guide = guide_axis(angle = 90)) +
#   facet_wrap(~modelname, nrow = 1, strip.position = "top") +
#   labs(y = "Simulated value (re-scaled)",
#        x = "",
#        col = '',
#        fill = '') +
#   customTheme +
#   theme(legend.position = 'right')
# pB_wide
# 
# pA2 <- pA +theme(legend.position = 'right')
# pAB <- plot_grid(pA2, pB_wide, nrow = 1, rel_widths = c(0.6, 1),labels = c('A', 'B'))
# pABC <- plot_grid(pAB, pC, ncol = 1, rel_heights = c(0.4, 1), labels = c(NA, 'C'))
# pABC
# 
# ggsave(plot = pABC, filename = file.path(getwd(), 'Figure3_wide_R.pdf'), height = 12, width = 20)
# ggsave(plot = pABC, filename = file.path(getwd(), 'Figure3_wide_R.png'), height = 12, width = 20)
# 
# 
# 
# #### With  age  exploration
# 
# sel_agegrps <- c('1-2','5-10','15-20','20-100')
# pD <- dat_s %>%
#   ungroup() %>%
#   filter(ageGroup %in% c('1-2','5-10','15-20','20-100')) %>%
#   filter(eir == 5) %>%
#   dplyr::select(times, eir, ageGroup, modelname,
#                 simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
#                 prevalence__mean, prevalence__min, prevalence__up,
#                 clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up, 
#                 n_total_mos_pop__mean, n_total_mos_pop__min, n_total_mos_pop__up) %>%
#   pivot_longer(cols = -c(times, eir, ageGroup, modelname)) %>%
#   separate(name, into = c('name', 'stat'), sep = '__') %>%
#   mutate(custom_col =
#            case_when(name == 'simulatedEIR' & ageGroup == sel_agegrps[1] ~ simEIR_cols[1],
#                      name == 'simulatedEIR' & ageGroup == sel_agegrps[2] ~ simEIR_cols[2],
#                      name == 'simulatedEIR' & ageGroup == sel_agegrps[3] ~ simEIR_cols[3],
#                      name == 'simulatedEIR' & ageGroup == sel_agegrps[4] ~ simEIR_cols[4],
#                      # prev
#                      name == 'prevalence' & ageGroup == sel_agegrps[1] ~ prev_cols[1],
#                      name == 'prevalence' & ageGroup == sel_agegrps[2] ~ prev_cols[2],
#                      name == 'prevalence' & ageGroup == sel_agegrps[3] ~ prev_cols[3],
#                      name == 'prevalence' & ageGroup == sel_agegrps[4] ~ prev_cols[4],
#                      # inc
#                      name == 'clinical_incidence' & ageGroup == sel_agegrps[1] ~ inc_cols[1],
#                      name == 'clinical_incidence' & ageGroup == sel_agegrps[2] ~ inc_cols[2],
#                      name == 'clinical_incidence' & ageGroup == sel_agegrps[3] ~ inc_cols[3],
#                      name == 'clinical_incidence' & ageGroup == sel_agegrps[4] ~ inc_cols[4],
#                      # Mos Pop
#                      name == 'n_total_mos_pop' & eir == sel_eirs[1] ~ mos_cols[1],
#                      name == 'n_total_mos_pop' & eir == sel_eirs[2] ~ mos_cols[2],
#                      name == 'n_total_mos_pop' & eir == sel_eirs[3] ~ mos_cols[3],
#                      name == 'n_total_mos_pop' & eir == sel_eirs[4] ~ mos_cols[4])) %>%
#   mutate(name = factor(name,
#                        levels = c('simulatedEIR', 'prevalence', 'clinical_incidence', 'n_total_mos_pop'),
#                        labels = c('simulated EIR', 'Prevalence', 'Clinical incidence (ppa)', 'Total Mosquito\nPopulation'))) %>%
#   group_by(modelname, name, eir) %>%
#   mutate(value = rescale(value, to = c(0, 1))) %>%
#   pivot_wider(names_from = stat, values_from = value) %>%
#   ggplot() +
#   geom_col(data = input_eir_df,
#            aes(x = times, y = finput_eir * 5), fill = '#ececec') +
#   geom_ribbon(aes(x = times, ymin = min, ymax = up, fill = custom_col), color = 'transparent', alpha = 0.1) +
#   geom_vline(xintercept = c(365,730,1825), color='#696969',linetype='dotted') +
#   geom_line(aes(x = times, y = mean,color=custom_col,
#                 alpha= as.factor(ageGroup), group = as.factor(ageGroup)), linewidth = 1) +
#   scale_alpha_manual(values = c(0.5, 0.6, 0.8, 1)) +
#   scale_color_identity() +
#   scale_y_continuous(expand = expansion(mult = c(0, .1))) +
#   facet_grid(name ~ modelname, scales = "free", switch = 'y') +
#   labs(y = "",
#        x = "",
#        alpha = 'Age group (years)',
#        fill = '',
#        caption = "Age 5-10 years") +
#   customTheme +
#   theme(axis.title.y = element_blank(),
#         panel.spacing.x = unit(1, "lines"),
#         panel.spacing.y = unit(0.5, "lines"),
#         strip.placement = "outside") +
#   guides(alpha = guide_legend(reverse = TRUE))
# 
# pD
# 
# 
# pAB <- plot_grid(pA, pB, ncol = 1, labels = c('A', 'B'))
# pABD <- plot_grid(pAB, pD, ncol = 2, rel_widths = c(0.4, 1), labels = c(NA, 'C'))
# pABD
# 
# ggsave(plot = pABD, filename = file.path(getwd(), 'Figure3_agrgrp_R.pdf'), height = 12, width = 20)
# ggsave(plot = pABD, filename = file.path(getwd(), 'Figure3_agrgrp_R.png'), height = 12, width = 20)