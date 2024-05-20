### Seasonality figure

library(ggplot2)
library(dplyr)
library(data.table)
library(scales)
library(cowplot)
library(tidyr)
library(gridExtra)
library(lubridate)

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

# FIXME redo  plots with newer simulation and 5 day reporting!

# /projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240212/sims_dynamic_seasonal_13_53_14/

projdir <- file.path(projdir, 'test_sims_20240113')
exp_name <- "sims_dynamic_seasonal_13_53_14"
emodom <- c("EMOD", "OpenMalaria", "MalSim")
agegrps <- c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100')

start_date = as.Date('2001-07-01')
date_period <- c(start_date,start_date+months(12), start_date+months(24), start_date+years(5))

# Load simulation outputs  BENCHMARK-------------------------------
dat_s <- get_emodom_df(file.path(projdir, exp_name), emodom = emodom, mth = TRUE, timeseries = TRUE)

dat_s <- dat_s %>%
  group_by(date, year, month, agebin, eir, cm_clinical, ageGroup, seasonality, emodom) %>%
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
            severe_incidence__up = quantile(severe_incidence, 0.95)) %>%
  mutate(date = as.Date(date)) %>%
  ungroup()

table(dat_s$ageGroup)
dat_s$ageGroup <- factor(dat_s$ageGroup,
                         levels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'),
                         labels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'))

table(dat_s$eir, dat_s$emodom)
table(dat_s$month, dat_s$emodom)

input_eir_df <- data.frame(
  month = 1:12,
  finput_eir = c(0.110650869, 0.073115112, 0.073611502, 0.072567808, 0.071765752,
                 0.065682898, 0.065480693, 0.066513955, 0.074306173, 0.085359082,
                 0.118347574, 0.122598589)
)

dat_s <- dat_s %>% left_join(input_eir_df)
input_eir_df <- input_eir_df %>% left_join(unique(dat_s[, c('month', 'date')]))
dat_s$emodom <- factor(dat_s$emodom, levels = emodom, labels = c("EMOD", "OpenMalaria", "malariasimulation"))

pA <- dat_s %>%
  filter(date >= date_period[1] & date <=date_period[2]) %>%
  filter(ageGroup %in% '5-10') %>%
  filter(eir %in% c(5)) %>%
  ggplot() +
  geom_col(data = subset(input_eir_df, date >= date_period[1] & date <=date_period[2]),
           aes(x = date, y = finput_eir * 5), fill = '#ececec') +
  geom_ribbon(aes(x = date, ymin = simulatedEIR__min, ymax = simulatedEIR__up, fill = emodom), alpha = 0.18) +
  geom_line(aes(x = date, y = simulatedEIR__mean, col = emodom), linewidth = 1) +
  scale_color_manual(values = emodom_cols) +
  scale_fill_manual(values = emodom_cols) +
  scale_y_continuous(expand = expansion(mult = c(0, .1))) +
  scale_x_date(date_breaks = '1 months', date_labels = '%b', expand = c(0, 0),guide = guide_axis(angle = 90)) +
  labs(y = "Simulated EIR",
       x = "",
       color = '',
       fill = '',
       title = '') +
  customTheme +
  theme(legend.position = c(.2, .875))


pB <- dat_s %>%
  ungroup() %>%
  filter(date >= date_period[1] & date <=date_period[2]) %>% ## FIXME
  filter(ageGroup %in% '5-10') %>%
  filter(eir %in% c(5)) %>%
  dplyr::select(date, eir, ageGroup, emodom,
                simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up) %>%
  pivot_longer(cols = -c(date, eir, ageGroup, emodom)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name,
                       levels = c('simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('simulated EIR', 'Prevalence', 'Clinical incidence (ppa)'))) %>%
  group_by(emodom, name) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_col(data = subset(input_eir_df, date >= date_period[1] & date <=date_period[2]),
           aes(x = date, y = finput_eir * 5), fill = '#ececec') +
  geom_ribbon(aes(x = date, ymin = min, ymax = up, fill = name), alpha = 0.18) +
  geom_line(aes(x = date, y = mean, col = name), linewidth = 1) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_y_continuous(expand = expansion(mult = c(0, .1))) +
  scale_x_date(date_breaks = '1 months', date_labels = '%b', expand = c(0, 0),guide = guide_axis(angle = 90)) +
  facet_wrap(~emodom, ncol = 1, strip.position = "right") +
  labs(y = "Simulated value (re-scaled)",
       x = "",
       col = '',
       fill = '') +
  customTheme +
  theme(legend.position = 'bottom')


pB_wide <- dat_s %>%
  ungroup() %>%
  filter(date >= date_period[1] & date <=date_period[2]) %>% ## FIXME
  filter(ageGroup %in% '5-10') %>%
  filter(eir %in% c(5)) %>%
  dplyr::select(date, eir, ageGroup, emodom,
                simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up) %>%
  pivot_longer(cols = -c(date, eir, ageGroup, emodom)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name,
                       levels = c('simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('simulated EIR', 'Prevalence', 'Clinical incidence (ppa)'))) %>%
  group_by(emodom, name) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_col(data = subset(input_eir_df, date >= date_period[1] & date <=date_period[2]),
           aes(x = date, y = finput_eir * 5), fill = '#ececec') +
  geom_ribbon(aes(x = date, ymin = min, ymax = up, fill = name), alpha = 0.18) +
  geom_line(aes(x = date, y = mean, col = name), linewidth = 1) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_y_continuous(expand = expansion(mult = c(0, .1))) +
  scale_x_date(date_breaks = '1 months', date_labels = '%b', expand = c(0, 0),guide = guide_axis(angle = 90)) +
  facet_wrap(~emodom, nrow = 1, strip.position = "top") +
  labs(y = "Simulated value (re-scaled)",
       x = "",
       col = '',
       fill = '') +
  customTheme +
  theme(legend.position = 'right')

## Varying EIRs
simEIR_cols <- c('#9fc4a0', '#66a066', '#408941', '#132913')
prev_cols <- c('#66c2e1', '#009acd', '#006b8f', '#003d52')
inc_cols <- c('#fdd870', '#fdbf11', '#b1850b', '#654c06')
sel_eirs <- c(1, 5, 50, 200)


pC <- dat_s %>%
  ungroup() %>%
  filter(date >= date_period[1] & date <=date_period[4]) %>%
  filter(ageGroup %in% '5-10') %>%
  filter(eir %in% sel_eirs) %>%
  dplyr::select(date, eir, ageGroup, emodom,
                simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up) %>%
  pivot_longer(cols = -c(date, eir, ageGroup, emodom)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(custom_col =
           case_when(name == 'simulatedEIR' & eir == sel_eirs[1] ~ simEIR_cols[1],
                     name == 'simulatedEIR' & eir == sel_eirs[2] ~ simEIR_cols[2],
                     name == 'simulatedEIR' & eir == sel_eirs[3] ~ simEIR_cols[3],
                     name == 'simulatedEIR' & eir == sel_eirs[4] ~ simEIR_cols[4],
                     # prev
                     name == 'prevalence' & eir == sel_eirs[1] ~ prev_cols[1],
                     name == 'prevalence' & eir == sel_eirs[2] ~ prev_cols[2],
                     name == 'prevalence' & eir == sel_eirs[3] ~ prev_cols[3],
                     name == 'prevalence' & eir == sel_eirs[4] ~ prev_cols[4],
                     # inc
                     name == 'clinical_incidence' & eir == sel_eirs[1] ~ inc_cols[1],
                     name == 'clinical_incidence' & eir == sel_eirs[2] ~ inc_cols[2],
                     name == 'clinical_incidence' & eir == sel_eirs[3] ~ inc_cols[3],
                     name == 'clinical_incidence' & eir == sel_eirs[4] ~ inc_cols[4]

           )) %>%
  mutate(name = factor(name,
                       levels = c('simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('simulated EIR', 'Prevalence', 'Clinical incidence (ppa)'))) %>%
  group_by(emodom, name, eir) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_col(data = subset(input_eir_df, date >= date_period[1] & date <=date_period[4]),
           aes(x = date, y = finput_eir * 5), fill = '#ececec') +
      geom_vline(xintercept = seq(as.Date(start_date),date_period[3], 365), color='#696969',linetype='dotted')+
  #geom_ribbon(aes(x = date, ymin = min, ymax = up, fill = as.factor(eir)), alpha = 0.1) +
  geom_line(aes(x = date, y = mean,color=custom_col, alpha= as.factor(eir), group = as.factor(eir)), linewidth = 1) +
  scale_alpha_manual(values = c(0.5, 0.6, 0.8, 1)) +
  scale_color_identity() +
  scale_y_continuous(expand = expansion(mult = c(0, .1))) +
  scale_x_date(date_breaks = '3 months', date_labels = '%b',
               expand = c(0, 0),guide = guide_axis(angle = 90)) +
  facet_grid(name ~ emodom, scales = "free", switch = 'y') +
  labs(y = "",
       x = "",
        alpha = 'Annual EIR\n(input)',
       fill = '',
       caption = "Age 5-10 years") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing.x = unit(1, "lines"),
        panel.spacing.y = unit(0.5, "lines"),
        strip.placement = "outside") +
  guides(alpha = guide_legend(reverse = TRUE))

sel_agegrps <- c('1-2','5-10','15-20','20-100')

pD <- dat_s %>%
  ungroup() %>%
  filter(date >= date_period[1] & date <=date_period[4]) %>%
  filter(ageGroup %in% c('1-2','5-10','15-20','20-100')) %>%
  filter(eir == 5) %>%
  dplyr::select(date, eir, ageGroup, emodom,
                simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up) %>%
  pivot_longer(cols = -c(date, eir, ageGroup, emodom)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(custom_col =
           case_when(name == 'simulatedEIR' & ageGroup == sel_agegrps[1] ~ simEIR_cols[1],
                     name == 'simulatedEIR' & ageGroup == sel_agegrps[2] ~ simEIR_cols[2],
                     name == 'simulatedEIR' & ageGroup == sel_agegrps[3] ~ simEIR_cols[3],
                     name == 'simulatedEIR' & ageGroup == sel_agegrps[4] ~ simEIR_cols[4],
                     # prev
                     name == 'prevalence' & ageGroup == sel_agegrps[1] ~ prev_cols[1],
                     name == 'prevalence' & ageGroup == sel_agegrps[2] ~ prev_cols[2],
                     name == 'prevalence' & ageGroup == sel_agegrps[3] ~ prev_cols[3],
                     name == 'prevalence' & ageGroup == sel_agegrps[4] ~ prev_cols[4],
                     # inc
                     name == 'clinical_incidence' & ageGroup == sel_agegrps[1] ~ inc_cols[1],
                     name == 'clinical_incidence' & ageGroup == sel_agegrps[2] ~ inc_cols[2],
                     name == 'clinical_incidence' & ageGroup == sel_agegrps[3] ~ inc_cols[3],
                     name == 'clinical_incidence' & ageGroup == sel_agegrps[4] ~ inc_cols[4]

           )) %>%
  mutate(name = factor(name,
                       levels = c('simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('simulated EIR', 'Prevalence', 'Clinical incidence (ppa)'))) %>%
  group_by(emodom, name, eir) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_col(data = subset(input_eir_df, date >= date_period[1] & date <=date_period[4]),
           aes(x = date, y = finput_eir * 5), fill = '#ececec') +
    geom_vline(xintercept = seq(as.Date(start_date),date_period[3], 365), color='#696969',linetype='dotted')+
  #geom_ribbon(aes(x = date, ymin = min, ymax = up, fill = as.factor(eir)), alpha = 0.1) +
  geom_line(aes(x = date, y = mean,color=custom_col,
                alpha= as.factor(ageGroup), group = as.factor(ageGroup)), linewidth = 1) +
  scale_alpha_manual(values = c(0.5, 0.6, 0.8, 1)) +
  scale_color_identity() +
  scale_y_continuous(expand = expansion(mult = c(0, .1))) +
  scale_x_date(date_breaks = '3 months', date_labels = '%b',
               expand = c(0, 0),guide = guide_axis(angle = 90)) +
  facet_grid(name ~ emodom, scales = "free", switch = 'y') +
  labs(y = "",
       x = "",
        alpha = 'Age group (years)',
       fill = '',
       caption = "Age 5-10 years") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing.x = unit(1, "lines"),
        panel.spacing.y = unit(0.5, "lines"),
        strip.placement = "outside") +
  guides(alpha = guide_legend(reverse = TRUE))




#### With  EIR exploration
pAB <- plot_grid(pA, pB, ncol = 1, labels = c('A', 'B'))
pABC <- plot_grid(pAB, pC, ncol = 2, rel_widths = c(0.4, 1), labels = c(NA, 'C'))
pABC

ggsave(plot = pABC, filename = file.path(getwd(), 'Figure3_R.pdf'), height = 12, width = 20)
ggsave(plot = pABC, filename = file.path(getwd(), 'Figure3_R.png'), height = 12, width = 20)

pA2 <- pA +theme(legend.position = 'right')
pAB <- plot_grid(pA2, pB_wide, nrow = 1, rel_widths = c(0.6, 1),labels = c('A', 'B'))
pABC <- plot_grid(pAB, pC, ncol = 1, rel_heights = c(0.4, 1), labels = c(NA, 'C'))
pABC

ggsave(plot = pABC, filename = file.path(getwd(), 'Figure3_wide_R.pdf'), height = 12, width = 20)
ggsave(plot = pABC, filename = file.path(getwd(), 'Figure3_wide_R.png'), height = 12, width = 20)



#### With  age  exploration
pAB <- plot_grid(pA, pB, ncol = 1, labels = c('A', 'B'))
pABD <- plot_grid(pAB, pD, ncol = 2, rel_widths = c(0.4, 1), labels = c(NA, 'C'))
pABD

ggsave(plot = pABD, filename = file.path(getwd(), 'Figure3_agrgrp_R.pdf'), height = 12, width = 20)
ggsave(plot = pABD, filename = file.path(getwd(), 'Figure3_agrgrp_R.png'), height = 12, width = 20)


