### Seasonality figure
setwd("~/model-characterization")
library(ggplot2)
library(dplyr)
library(data.table)
library(scales)
library(tidyr)
library(patchwork)
source('utility/functions.R')
theme_set(theme_bw())

customTheme <- f_getCustomTheme() +
  theme(panel.grid.minor = element_blank())

modelname <- c("EMOD", "malariasimulation", "OpenMalaria")


#Useful code to generate the EMOD seasonal profile to then use for the other two models
#wdir <- file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250220_production/sims_dynamic_seasonal_10_58_01/')
#calculate_monthlyEIRs_seasonal(wdir, "current_2_25_25")
#calculate_dailyEIRs_seasonal(wdir, "current_3_7_25")

wdir_eir <- file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250220_production/sims_dynamic_seasonal_10_58_01')
dat_s_eir_em <- get_output_df(wdir_eir, modelname = "EMOD", timeseries = TRUE, fiveday=TRUE)

wdir_eir <- file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250307_production/sims_dynamic_seasonal_12_39_01/')
dat_s_eir_ms <- get_output_df(wdir_eir, modelname = "malariasimulation", timeseries = TRUE, fiveday=TRUE)

wdir_eir <- file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250225_production/sims_dynamic_seasonal_17_05_51')
dat_s_eir_om <- get_output_df(wdir_eir, modelname = "OpenMalaria", timeseries = TRUE, fiveday=TRUE)

dat_s_eir <- rbind(dat_s_eir_em, dat_s_eir_ms, dat_s_eir_om, fill=TRUE)
dat_s_eir$output_type <-'eir'

dat_s_eir <- dat_s_eir%>%
  filter(year == 2004, cm_clinical == 0.15, ageGroup == '0-100', seasonality == 'seasonal', target_output_values == 20) %>%
  group_by(target_output_values, cm_clinical, seasonality, modelname, seed) %>%
  mutate(sumEIR = sum(simulatedEIR),
         simulatedEIR = (simulatedEIR/sumEIR)*20)
rm(dat_s_eir_em, dat_s_eir_ms, dat_s_eir_om, wdir_eir)

wdir_pfpr <- file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250225_production/sims_dynamic_seasonal_16_53_27')
dat_s_pfpr <- get_output_df(wdir_pfpr, modelname = c("EMOD", "OpenMalaria"), timeseries = TRUE, fiveday=TRUE)
wdir_pfpr <- file.path('/projects/b1139/emod-om/simulation_outputs/rer4177/20250304_production/sims_dynamic_seasonal_14_34_59/')
dat_s_pfpr_ms <- get_output_df(wdir_pfpr, modelname = c("malariasimulation"), timeseries = TRUE, fiveday=TRUE)
dat_s_pfpr <- rbind(dat_s_pfpr, dat_s_pfpr_ms, fill=TRUE)
dat_s_pfpr$output_type <- 'pfpr'

dat_s_pfpr <- dat_s_pfpr %>%
  filter(cm_clinical == 0.15, ageGroup == '0-100', seasonality == 'seasonal', target_output_values %in% c(0.05, 0.1, 0.25, 0.5))

dat_s <- rbind(dat_s_eir, dat_s_pfpr)
rm(dat_s_eir, dat_s_pfpr, dat_s_pfpr_ms)

dat_s <- dat_s %>%
  group_by(day, year, output_type, target_output_values, cm_clinical, cm_severe, seasonality, modelname) %>%
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

dat_s$modelname <- factor(dat_s$modelname, levels = modelname, labels = c("EMOD", "malariasimulation","OpenMalaria"))

dat_s <- dat_s %>%
  mutate(times = (day+365*(year-2000)))

#Setting up which EIRS have pfpr2to10 values closest to our targets
pfpr_labels <- c(0.05,0.1,0.25,0.5)


pA <- dat_s %>%
  filter(year == max(year)) %>%
  filter(target_output_values == 20) %>%
  ggplot() +
  geom_ribbon(aes(x = day, ymin = simulatedEIR__min, ymax = simulatedEIR__up, fill = modelname), alpha = 0.1) +
  geom_line(aes(x = day, y = simulatedEIR__mean, col = modelname), linewidth = 1) +
  expand_limits(y=0) +
  scale_color_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_fill_manual(values = c('#1b9e77ff','#7570b3ff','#d95f02ff')) +
  scale_y_continuous(expand = expansion(mult = c(0, 0))) +
  scale_x_continuous(expand = expansion(mult = c(0, 0))) +
  labs(y = "Simulated EIR (5 day)",
       x = "Day of year",
       color = 'Model',
       fill = 'Model',
       title = 'A) EIR = 20, CM = 15%',
       caption = 'All Ages') +
  customTheme +
  theme(legend.position = "inside",
        legend.position.inside = c(.12, .8),
        plot.margin = margin(0, 0, 0,0, "pt"))
pA

pB <- dat_s %>%
  filter(year == max(year)) %>% 
  filter(target_output_values == 20) %>%
  dplyr::select(day, year, target_output_values, modelname,
                simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
                prevalence__mean, prevalence__min, prevalence__up,
                clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up,
                n_total_mos_pop__mean, n_total_mos_pop__min, n_total_mos_pop__up) %>%
  pivot_longer(cols = -c(day, year, target_output_values, modelname)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(name = factor(name,
                       levels = c('n_total_mos_pop','simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('Adult Female\nMosquitoes','Simulated EIR\n(5 day)', 'Prevalence\n(all ages)', 'Clinical Incidence\n(per 1000 per year)'))) %>%
  group_by(modelname, name) %>%
  mutate(value = rescale(value, to = c(0, 1))) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  group_by(target_output_values, modelname, name) %>%
  mutate(max_y = max(mean),
         ismax = mean==max_y) %>%
  ggplot() +
  geom_ribbon(aes(x = day, ymin = min, ymax = up, fill = name), alpha = 0.1) +
  geom_line(aes(x = day, y = mean, col = name), linewidth = 1.25) +
  scale_color_manual(values = c('#003d52','#408941', '#009acd', '#fdbf11')) +
  scale_fill_manual(values = c('#003d52','#408941', '#009acd', '#fdbf11')) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  scale_x_continuous(expand = expansion(mult = c(0, 0))) +
  geom_text(data = .%>%filter(ismax), 
            aes(x=day, y= max_y, col = name),
            label = 'v', size = 6, 
            hjust = 0.5, vjust = 0, 
            position=position_nudge(y=0.05)) +
  facet_wrap(~modelname, ncol = 1, strip.position = "right") +
  labs(y = "Simulated value (re-scaled)",
       x = "Day of year",
       col = 'Simulation Output',
       fill = 'Simulation Output',
       title = 'B) EIR = 20',
       caption = 'All Ages') +
  customTheme +
  theme(legend.position = 'right',plot.margin = margin(0, 0, 0, 0, "pt"))
pB
## Varying Pfprs
line_cols <- c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c')

pC_pfpr <- dat_s %>%
  ungroup() %>%
  filter(times>=730) %>%
  filter(target_output_values %in% pfpr_labels) %>%
  select(times, target_output_values, modelname,
         simulatedEIR__mean, simulatedEIR__min, simulatedEIR__up,
         prevalence__mean, prevalence__min, prevalence__up,
         clinical_incidence__mean, clinical_incidence__min, clinical_incidence__up) %>%
  pivot_longer(cols = -c(times, target_output_values, modelname)) %>%
  separate(name, into = c('name', 'stat'), sep = '__') %>%
  mutate(custom_col = case_when(
    name == 'simulatedEIR' & target_output_values == pfpr_labels[1] ~ line_cols[1],
    name == 'simulatedEIR' & target_output_values == pfpr_labels[2] ~ line_cols[2],
    name == 'simulatedEIR' & target_output_values == pfpr_labels[3] ~ line_cols[3],
    name == 'simulatedEIR' & target_output_values == pfpr_labels[4] ~ line_cols[4],
    # prev
    name == 'prevalence' & target_output_values == pfpr_labels[1] ~ line_cols[1],
    name == 'prevalence' & target_output_values == pfpr_labels[2] ~ line_cols[2],
    name == 'prevalence' & target_output_values == pfpr_labels[3] ~ line_cols[3],
    name == 'prevalence' & target_output_values == pfpr_labels[4] ~ line_cols[4],
    # inc
    name == 'clinical_incidence' & target_output_values == pfpr_labels[1] ~ line_cols[1],
    name == 'clinical_incidence' & target_output_values == pfpr_labels[2] ~ line_cols[2],
    name == 'clinical_incidence' & target_output_values == pfpr_labels[3] ~ line_cols[3],
    name == 'clinical_incidence' & target_output_values == pfpr_labels[4] ~ line_cols[4])) %>%
  mutate(name = factor(name,
                       levels = c('simulatedEIR', 'prevalence', 'clinical_incidence'),
                       labels = c('Simulated EIR\n(5 day)', 'Prevalence\n (all ages)', 'Clinical\nIncidence\n(per person\nper year,\nannualized)'))) %>%
  group_by(modelname, name, target_output_values) %>%
  pivot_wider(names_from = stat, values_from = value) %>%
  ggplot() +
  geom_vline(xintercept = c(1095,1460), color='#696969',linetype='dotted')+
  geom_ribbon(aes(x = times, ymin = min, ymax = up, fill = custom_col), color = 'transparent', alpha = 0.1) +
  geom_line(aes(x = times, y = mean,color=custom_col), linewidth = 1) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.05))) +
  scale_x_continuous(breaks=c(730,1095,1460,1820), labels=c(0,1,2,3),expand = expansion(mult = c(0, 0))) +
  facet_grid(name ~ modelname, scales = "free", switch = 'y') +
  labs(y = "",
       x = "Years",
       color = 'Annual\nPfpr 2-10',
       fill = 'Annual\nPfpr 2-10',
       caption = "All Ages") +
  customTheme +
  theme(axis.title.y = element_blank(),
        panel.spacing.x = unit(1, "lines"),
        panel.spacing.y = unit(0.5, "lines"),
        strip.placement = "outside",
        strip.text.y.left = element_text(angle = 0),
        legend.position = 'right',
        plot.margin = margin(0, 0, 0, 0, "pt"))+
  scale_color_manual(labels = pfpr_labels, values = c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c')) +
  scale_fill_manual(labels = pfpr_labels, values = c('#1bd9e9', '#2c7bb6','#cfae61','#d7191c'))
pC_pfpr
#Saving Outputs
mylayout <- "AB
             CC"

pABC_pfpr <- (pA+pB+pC_pfpr)+plot_layout(design=mylayout)
pABC_pfpr
ggsave(plot = pABC_pfpr,filename = file.path(getwd(), 'Figure3_CM15.pdf'), height = 15, width = 22)
ggsave(plot = pABC_pfpr, filename = file.path(getwd(), 'Figure3_CM15.png'), height = 15, width = 22)
