library(ggplot2)
library(dplyr)
library(data.table)
library(scales)
library(cowplot)
library(tidyr)
library(gridExtra)


source('functions.R')
theme_set(theme_bw())
datetoday <- Sys.Date()

if (Sys.getenv("OS") == "Windows_NT") {
  box <- 'NU Malaria Modeling Dropbox'
  projdir <- file.path(Sys.getenv('USERPROFILE'), box, 'projects/EMOD_OM')
}else {
  username <- Sys.getenv('USER') #Sys.getenv('USERNAME')
  projdir <- file.path('/projects/b1139/emod-om/simulation_outputs', username)
}

# /projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240113/sims_dynamic_perennial_21_13_13/
# /projects/b1139/emod-om/simulation_outputs/rer4177/test_sims_20240212/sims_dynamic_seasonal_13_53_14/

projdir <- file.path('C:/Users/mrung/NU-malaria-team Dropbox/projects/EMOD_OM/simulation_outputs/test_sims_20240113')
exp_name1 <- "sims_dynamic_perennial_21_13_13"
exp_name2 <- "sims_dynamic_seasonal_13_53_14"
emodom <- c("EMOD", "OpenMalaria", "MalSim")
agegrps <- c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100')

customTheme <- f_getCustomTheme() +
  theme(legend.position = "None",
        panel.grid.major = element_blank(),
        panel.grid.minor = element_blank())

# Load simulation outputs  BENCHMARK-------------------------------
wdir <- file.path(projdir, exp_name1)
dat_p <- get_emodom_df(wdir, emodom = emodom)

table(dat_p$ageGroup, dat_p$emodom)

dat_p <- dat_p %>%
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

table(dat_p$ageGroup)
dat_p$ageGroup <- factor(dat_p$ageGroup,
                         levels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'),
                         labels = c('0-0.5', '0.5-1', '1-2', '2-5', '5-10', '10-15', '15-20', '20-100', '0-5', '0-100'))


# ------------------------------ Figure 2A and B ------------------------------
pA <- dat_p %>%
  filter(ageGroup %in% '0-100') %>%
  filter(seasonality == "perennial") %>%
  ggplot() +
  geom_ribbon(aes(x = simulatedEIR__mean, ymin = prevalence_2to10__min, ymax = prevalence_2to10__up,
                  fill = emodom, group = interaction(emodom, seasonality)), alpha = 0.3) +
  geom_line(aes(x = simulatedEIR__mean, y = prevalence_2to10__mean, col = emodom, linetype = seasonality)) +
  scale_x_log10(labels = comma) +
  labs(y = "PfPR 2 to 10",
       x = "Simulated EIR",
       title = "C) Children U5",
       subtitle = "") +
  customTheme


pB <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% '0-100') %>%
  filter(seasonality == "perennial") %>%
  dplyr::select(eir, simulatedEIR__mean, emodom,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, emodom, simulatedEIR__mean)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = case_when(name == 'clinical_incidence' ~ 'Clinical incidence (ppa)',
                          name == 'severe_incidence' ~ 'Severe incidence (ppa)')) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = simulatedEIR__mean, ymin = min, ymax = up, fill = emodom), alpha = 0.3) +
  geom_line(aes(x = simulatedEIR__mean, y = mean, col = emodom)) +
  facet_wrap(~name, scales = 'free_y', ncol = 1, strip.position = "left") +
  scale_x_log10(labels = comma) +
  labs(x = "Simulated EIR",
       title = "All ages",
       subtitle = "") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing = unit(2, "lines"),
        strip.placement = "outside")

pAB <- plot_grid(pA, pB, ncol = 1)


# ------------------------------ Figure 2C ------------------------------
table(dat_p$eir, dat_p$seasonality)
emod_eirs <- c(1, 1.5, 3, 9)  # c(1.1, 1.5, 3, 9)
om_eirs <- c(0.5, 0.75, 2, 7)  # c(0.6, 0.8, 2.2, 7)
malssim_eirs <- c(0.5, 1, 3, 16)  # c(0.5, 1, 3, 16)
pfpr_labels <- c('PfPR2to10 5%', 'PfPR2to10 10%', 'PfPR2to10 25%', 'PfPR2to10 50%')

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


pC <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% agegrps) %>%
  filter(seasonality == "perennial") %>%
  filter(!is.na(pfpr_grp)) %>%
  dplyr::select(eir, ageGroup, pfpr_grp, emodom,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, ageGroup, emodom, pfpr_grp)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name, levels = c('prevalence', 'clinical_incidence', 'severe_incidence'),
                       labels = c('Prevalence', 'Clinical incidence (ppa)', 'Severe incidence (ppa)'))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = ageGroup, ymin = min, ymax = up, fill = emodom, group = emodom), alpha = 0.3) +
  geom_line(aes(x = ageGroup, y = mean, col = emodom, group = emodom)) +
  facet_wrap(name ~ pfpr_grp, scales = 'free_y', nrow = 3) +  #, strip.position = "left"
  labs(x = "Age (years)",
       title = "",
       subtitle = "") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing = unit(2, "lines"),
        strip.placement = "outside")

# ------------------------------ Figure 2D ------------------------------
pD <- dat_p %>%
  ungroup() %>%
  filter(ageGroup %in% agegrps) %>%
  filter(seasonality == "perennial") %>%
  dplyr::select(eir, ageGroup, prevalence__mean, emodom,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                severe_incidence__mean, severe_incidence__min, severe_incidence__up) %>%
  pivot_longer(cols = -c(eir, ageGroup, emodom, prevalence__mean)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = case_when(name == 'clinical_incidence' ~ 'Clinical incidence (ppa)',
                          name == 'severe_incidence' ~ 'Severe incidence (ppa)')) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_ribbon(aes(x = prevalence__mean, ymin = min, ymax = up, fill = emodom), alpha = 0.3) +
  geom_line(aes(x = prevalence__mean, y = mean, col = emodom)) +
  facet_wrap(name ~ ageGroup, scales = 'free_y', nrow = 2) +  # ,  strip.position = "left"
  labs(x = "PfPR 2to10",
       title = "All ages",
       subtitle = "") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing = unit(2, "lines"),
        strip.placement = "outside")


pABC <- plot_grid(pAB, pC, ncol = 2, rel_heights = c(1, 1))
pABCD <- plot_grid(pABC, pD, ncol = 1, rel_heights = c(1, 0.7), rel_widths = c(1, 1))

print(pABCD)
ggsave(plot = pABCD, filename = file.path(getwd(), 'Figure2_R.pdf'), height = 15.5, width = 18)
