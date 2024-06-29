### 'Baseline' figure
library(ggplot2)
library(dplyr)
library(data.table)
library(scales)
library(cowplot)
library(tidyr)
library(gridExtra)
library(patchwork)

source('functions.R')
theme_set(theme_bw())
datetoday <- Sys.Date()

if (Sys.getenv("OS") == "Windows_NT") {
  box <- 'NU-malaria-team Dropbox'
  projdir <- file.path(Sys.getenv('USERPROFILE'), box, 'projects/EMOD_OM')
}else {
  username <- Sys.getenv('USER') #Sys.getenv('USERNAME')
  projdir <- file.path('/projects/b1139/emod-om/simulation_outputs', username)
}

projdir <- file.path(projdir, 'test_sims_20240606')
exp_name <- "sims_dynamic_perennial__21_51_29"
emodom <- c("EMOD", "OpenMalaria", "MalSim")
agegrps <- c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100')

customTheme <- f_getCustomTheme() +
  theme(legend.position = "None",
        panel.grid.major = element_blank(),
        panel.grid.minor = element_blank())

# Load simulation outputs  BENCHMARK-------------------------------
wdir <- file.path(projdir, exp_name)
dat_total <- get_output_df(wdir, emodom = emodom)

table(dat_p$ageGroup, dat_p$emodom)


dat_total <- dat_total %>%
  group_by(eir, cm_clinical, ageGroup, seasonality, emodom) %>%
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

table(dat_total$ageGroup)
table(dat_total$cm_clinical)

dat_total$ageGroup <- factor(dat_total$ageGroup,
                         levels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'),
                         labels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'))

for (ii in unique(dat_total$cm_clinical)){
 dat_p <- filter(dat_total, cm_clinical == ii)
# ------------------------------ Figure 2A and B ------------------------------

pA <- dat_p %>%
  filter(ageGroup %in% '0-100') %>%
  ggplot() +
  geom_ribbon(aes(x = simulatedEIR__mean, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up, fill = emodom), alpha = 0.15) +
  geom_line(aes(x = simulatedEIR__mean, y = prevalence_2to10__mean, col = emodom)) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_x_log10(labels = comma) +
  customTheme +
  theme(panel.grid.major = element_blank(),
        panel.grid.minor = element_blank())+
  labs(y = expression('PfPR'[2-10]),
       x = "Simulated EIR",
       title = paste("All Ages CM: ", ii),
       subtitle = "",
       fill = 'Model',
       color = 'Model') +
  theme(legend.position = c(.15, .65))

pB1 <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% '0-100') %>%
  dplyr::select(eir, prevalence_2to10__mean, emodom,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, emodom, prevalence_2to10__mean)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  filter(name == 'clinical_incidence') %>%
  mutate(name = case_when(name == 'clinical_incidence' ~ 'Clinical Incidence\n(ppa)')) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = prevalence_2to10__mean, ymin = min, ymax = up, fill = emodom), alpha = 0.15) +
  geom_line(aes(x = prevalence_2to10__mean, y = mean, col = emodom)) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  customTheme +
  #facet_wrap(~name, scales = 'free_y', ncol = 1) +
  labs(y = "Clinical Incidence\n(ppa)",
       x = "",
       title = "",
       subtitle = "") +
  theme(axis.text.x= element_blank())

pB2 <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% '0-100') %>%
  dplyr::select(eir, prevalence_2to10__mean, emodom,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, emodom, prevalence_2to10__mean)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  filter(name == 'severe_incidence') %>%
  mutate(name = case_when(name == 'severe_incidence' ~ 'Severe Incidence\n(ppa)')) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = prevalence_2to10__mean, ymin = min, ymax = up, fill = emodom), alpha = 0.15) +
  geom_line(aes(x = prevalence_2to10__mean, y = mean, col = emodom)) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  customTheme +
  labs(x = expression('PfPR'[2-10]),
       y = 'Severe Incidence\n(ppa)',
       title = "",
       subtitle = "")

pB <- pB1 / pB2

# ------------------------------ Figure 2C ------------------------------

table(dat_p$eir, dat_p$seasonality)
emod_eirs <- c(2,2.5,7,18)  # c(1.1, 1.5, 3, 9)
om_eirs <- c(1.75, 4, 10, 50)  # c(0.6, 0.8, 2.2, 7)
malssim_eirs <- c(0.5, 1.25, 5, 20)  # c(0.5, 1, 3, 16)
pfpr_labels <- c('PfPR2-10 5%', 'PfPR2-10 10%', 'PfPR2-10 25%', 'PfPR2-10 50%')

dat_p <- dat_p %>%
  mutate(pfpr_grp = case_when(
    emodom == 'EMOD' & eir %in% emod_eirs[1] ~ pfpr_labels[1],
    emodom == 'EMOD' & eir %in% emod_eirs[2] ~ pfpr_labels[2],
    emodom == 'EMOD' & eir %in% emod_eirs[3] ~ pfpr_labels[3],
    emodom == 'EMOD' & eir %in% emod_eirs[4] ~ pfpr_labels[4],
    ## OM
    emodom == 'OpenMalaria' & eir %in% om_eirs[1] ~ pfpr_labels[1],
    emodom == 'OpenMalaria' & eir %in% om_eirs[2] ~ pfpr_labels[2],
    emodom == 'OpenMalaria' & eir %in% om_eirs[3] ~ pfpr_labels[3],
    emodom == 'OpenMalaria' & eir %in% om_eirs[4] ~ pfpr_labels[4],
    ## MalSim
    emodom == 'MalSim' & eir %in% malssim_eirs[1] ~ pfpr_labels[1],
    emodom == 'MalSim' & eir %in% malssim_eirs[2] ~ pfpr_labels[2],
    emodom == 'MalSim' & eir %in% malssim_eirs[3] ~ pfpr_labels[3],
    emodom == 'MalSim' & eir %in% malssim_eirs[4] ~ pfpr_labels[4]),
         pfpr_grp = factor(pfpr_grp, levels = pfpr_labels, labels = pfpr_labels))


pC1 <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% agegrps) %>%
  filter(!is.na(pfpr_grp)) %>%
  dplyr::select(eir, ageGroup, pfpr_grp, emodom,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, ageGroup, emodom, pfpr_grp)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name, levels = c('prevalence', 'clinical_incidence', 'severe_incidence'),
                       labels = c('Prevalence', 'Clinical Incidence (ppa)', 'Severe Incidence (ppa)'))) %>%
  filter(name =='Prevalence') %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = ageGroup, ymin = min, ymax = up, fill = emodom, group = emodom), alpha = 0.15) +
  geom_line(aes(x = ageGroup, y = mean, col = emodom, group = emodom)) +
  facet_wrap(~ pfpr_grp, scales = 'free', nrow=1) + 
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  customTheme +
  labs(x = "",
       y = 'Prevalence',
       title = "",
       subtitle = "") +
  theme(axis.text.x = element_text(angle = 45,vjust = 1, hjust=1))

pC2 <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% agegrps) %>%
  filter(!is.na(pfpr_grp)) %>%
  dplyr::select(eir, ageGroup, pfpr_grp, emodom,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, ageGroup, emodom, pfpr_grp)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name, levels = c('prevalence', 'clinical_incidence', 'severe_incidence'),
                       labels = c('Prevalence', 'Clinical Incidence (ppa)', 'Severe Incidence (ppa)'))) %>%
  filter(name =='Clinical Incidence (ppa)') %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = ageGroup, ymin = min, ymax = up, fill = emodom, group = emodom), alpha = 0.15) +
  geom_line(aes(x = ageGroup, y = mean, col = emodom, group = emodom)) +
  facet_wrap(~ pfpr_grp, scales = 'free', nrow=1) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
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
  dplyr::select(eir, ageGroup, pfpr_grp, emodom,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, ageGroup, emodom, pfpr_grp)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name, levels = c('prevalence', 'clinical_incidence', 'severe_incidence'),
                       labels = c('Prevalence', 'Clinical Incidence (ppa)', 'Severe Incidence (ppa)'))) %>%
  filter(name =='Severe Incidence (ppa)') %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = ageGroup, ymin = min, ymax = up, fill = emodom, group = emodom), alpha = 0.15) +
  geom_line(aes(x = ageGroup, y = mean, col = emodom, group = emodom)) +
  facet_wrap(~ pfpr_grp, scales = 'free', nrow=1)+
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  customTheme +
  labs(x = "Age (years)",
       y = 'Severe Incidence\n(ppa)',
       title = "",
       subtitle = "") +
  theme(strip.text.x = element_blank(),
        axis.text.x = element_text(angle = 45,vjust = 1, hjust=1))


pC <- pC1 / pC2 / pC3

# ------------------------------ Figure 2D ------------------------------

pD1 <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% agegrps) %>%
  dplyr::select(eir, ageGroup, prevalence_2to10__mean, emodom,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, ageGroup, emodom, prevalence_2to10__mean)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  filter(name =='clinical_incidence') %>%
  mutate(name = case_when(name == 'clinical_incidence' ~ 'Clinical Incidence\n(ppa)')) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = prevalence_2to10__mean, ymin = min, ymax = up, fill = emodom), alpha = 0.15) +
  geom_line(aes(x = prevalence_2to10__mean, y = mean, col = emodom)) +
  facet_wrap(~ageGroup, scales = 'free_y', nrow = 1) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  customTheme +
  labs(x = "",
       y = 'Clinical Incidence\n(ppa)',
       title = "Age Groups",
       subtitle = "") +
  xlim(0, 0.90) +
  theme(axis.text.x =  element_text(angle = 45, vjust = 1, hjust=1))

pD2 <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% agegrps) %>%
  dplyr::select(eir, ageGroup, prevalence_2to10__mean, emodom,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, ageGroup, emodom, prevalence_2to10__mean)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  filter(name =='severe_incidence') %>%
  mutate(name = case_when(name == 'severe_incidence' ~ 'Severe Incidence\n(ppa)')) %>%
  
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = prevalence_2to10__mean, ymin = min, ymax = up, fill = emodom), alpha = 0.15) +
  geom_line(aes(x = prevalence_2to10__mean, y = mean, col = emodom)) +
  facet_wrap(~ageGroup, scales = 'free_y', nrow = 1) +
  scale_color_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#408941', '#009acd', '#fdbf11')) +
  customTheme +
  labs(x = "PfPR 2to10",
       y = 'Severe Incidence\n(ppa)',
       subtitle = "") +
  xlim(0, 0.90) +
  theme(strip.text.x = element_blank(),
        axis.text.x = element_text(angle = 45, vjust = 1, hjust=1))

pD <- pD1 / pD2

mylayout <- "AACCCCCC
             BBCCCCCC
             BBCCCCCC
             DDDDDDDD
             DDDDDDDD"

pABCD <- (pA+pB+pC+pD)+plot_layout(design=mylayout)
pABCD

#pABC <- plot_grid(pAB, pC, ncol = 2, rel_heights = c(1, 1), rel_widths = c(0.5,1),labels = c(NA,'C'))
#pABCD <- plot_grid(pABC, pD, ncol = 1, rel_heights = c(1, 0.8), rel_widths = c(1, 1), labels = c(NA,'D'))

#print(pABCD)
ggsave(plot = pABCD, filename = file.path(getwd(), paste('Figure2_R_CM_', ii, '.pdf',sep="")), height = 17.89, width = 34.13)

}

