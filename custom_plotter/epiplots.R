###-------------------------------------------------------------------------------------------------------
### Custom R plotter to create basic EIR-PfPR and PfPR-Incidence plots for EMOD and OpenMalaria
### Draft version to be modified for paper figure 2  (version 1)
###-------------------------------------------------------------------------------------------------------

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

exp_name <- 'test__noburnin'
wdir <- file.path(projdir, 'simulation_outputs', exp_name)
proj_fig_dir <- file.path(projdir, 'figures')
exp_fig_dir <- file.path(wdir, 'comb')
modelname <- c('EMOD','OpenMalaria')

# Load simulation outputs  -------------------------------
dat <- get_output_df(wdir, modelname=modelname)

# Table to check entries per model and EIR
table(dat$eir, dat$modelname, exclude = NULL)
table(dat$ageGroup, dat$modelname, exclude = NULL)

# Additional monthly EIR inputs and simultion outputs  -------------------------------
# OpenMalaria extracted EIR (in forced EIR not available for EMOD)
dateir_mth <- fread(file.path(wdir, 'om', 'OM_EIR_mth.csv')) %>%
  filter(year < 2001 &
           eir == 64 &
           seasonality == 'seasonal') %>%
  group_by(month, seasonality, cm_clinical, eir) %>%
  summarize(mean_val = mean(simulatedEIR)) %>%
  mutate(modelname = 'OpenMalaria - EIR sim') %>%
  ungroup() %>%
  select(eir, month, modelname, mean_val)

# OpenMalaria  EIR as in OM benchmarking (aggregated over years per month)
dat_mth <- get_output_df(wdir, modelname=modelname, mth=TRUE) %>%
  filter(ageGroup == '0-5' &
           eir == max(eir) &
           seed == min(seed))

# Check
table(dat_mth$eir, dat_mth$modelname, exclude = NULL)
table(dat_mth$seed, dat_mth$modelname, exclude = NULL)

eir_seasonal_input <- c(0.89536936, 1., 0.99861637, 0.88644885, 0.69983342,
                        0.4785287, 0.29422502, 0.18798817, 0.18941683, 0.29804822,
                        0.4907383, 0.70506627)
eir_input_df <- data.frame(cbind('month' = c(1:12),
                                 'mean_val' = eir_seasonal_input,
                                 "modelname" = 'input EIR (scaled)')) %>%
  mutate(eir =unique( dat_mth$eir),
         mean_val = as.numeric(mean_val) * 10,
         month = as.numeric(month)) %>%
  select(eir, month, modelname, mean_val)


# Annual EIR by PfPR 2to10 plot  (a) -------------------------------
p1 <- dat %>%
  filter(ageGroup == '0-5') %>%
  group_by(eir, seasonality, modelname) %>%
  summarize(pfpr2to10_mean = mean(prevalence_2to10),
            pfpr2to10_min = min(prevalence_2to10),
            pfpr2to10_max = max(prevalence_2to10)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = eir, ymin = pfpr2to10_min, ymax = pfpr2to10_max, fill = modelname,
                  group = interaction(seasonality, modelname)), alpha = 0.3) +
  geom_line(aes(x = eir, y = pfpr2to10_mean, col = modelname, linetype = seasonality)) +
  scale_y_continuous(lim = c(0, 1), breaks = seq(0, 1, 0.2)) +
  scale_x_log10(labels = comma) +  # + facet_wrap(~modelname)
  scale_color_brewer(palette = 'Set1') +
  scale_fill_brewer(palette = 'Set1') +
  labs(subtitle = '', fill = '', col = '',
       linetype = 'seasonality',
       y = expr(italic(Pf) * 'PR'['2 to 10']),
       x = 'Annual  EIR (input)',caption='') +
  theme(legend.position = c(0.25, 0.65)) +
  f_getCustomTheme()
p1


# Seasonality EIR figure - placeholder for (b) -------------------------------
p0 <- dat_mth %>%
  filter(modelname != 'EMOD' & modelname != 'OpenMalaria - EIR aggregated sim') %>%
  group_by(eir, month, modelname) %>%
  summarize(mean_val = mean(inputEIR),
            min_val = min(inputEIR),
            max_val = max(inputEIR)) %>%
  bind_rows(eir_input_df) %>%
  bind_rows(dateir_mth) %>%
  ggplot() +
  geom_hline(yintercept = 0, alpha = 0) +
  #geom_ribbon(aes(x = month, ymin = min_val, ymax = max_val, fill = modelname,
  #                group = modelname), alpha = 0.3) +
  geom_line(aes(x = month, y = mean_val, col = modelname)) +
  scale_x_continuous(lim = c(1, 12), breaks = c(1:12)) +
  scale_color_brewer(palette = 'Set1') +
  scale_fill_brewer(palette = 'Set1') +
  labs(subtitle = '', y = 'monthly EIR scaling', x = 'Month of year',
       fill = '', col = '',caption='' ) +
  theme(legend.position = c(0.65, 0.90)) +
  f_getCustomTheme()
p0


# PfPR 2to10  and clinical incidence by age figure  (c) -------------------------------
p2a <- dat %>%
  filter(seasonality == 'perennial') %>%
  group_by(eir, age_group, modelname) %>%
  summarize(prevalence_2to10 = mean(prevalence_2to10),
            clinical_incidence_mean = mean(clinical_incidence),
            clinical_incidence_min = min(clinical_incidence),
            clinical_incidence_max = max(clinical_incidence)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = prevalence_2to10, ymin = clinical_incidence_min, ymax = clinical_incidence_max, fill = age_group,
                  group = interaction(age_group, modelname)), alpha = 0.3) +
  geom_line(aes(x = prevalence_2to10, y = clinical_incidence_mean, col = age_group)) +
  scale_y_continuous(lim = c(0, 6), breaks = seq(0, 6, 1)) +
  facet_wrap(~modelname, nrow = 1) +
  scale_color_brewer(palette = 'Dark2') +
  scale_fill_brewer(palette = 'Dark2') +
  labs(x = expr(italic(Pf) * 'PR'['2 to 10']),
       y = 'Clinical cases ppa',
       color = 'Age group',
       fill = 'Age group',
       caption='') +
  f_getCustomTheme()

# PfPR 2to10  and severe incidence by age figure (d) -------------------------------
p2b <- dat %>%
  filter(seasonality == 'perennial') %>%
  group_by(eir, age_group, modelname) %>%
  summarize(prevalence_2to10 = mean(prevalence_2to10),
            severe_incidence_mean = mean(severe_incidence),
            severe_incidence_min = min(severe_incidence),
            severe_incidence_max = max(severe_incidence)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = prevalence_2to10, ymin = severe_incidence_min, ymax = severe_incidence_max, fill = age_group,
                  group = interaction(age_group, modelname)), alpha = 0.3) +
  geom_line(aes(x = prevalence_2to10, y = severe_incidence_mean, col = age_group)) +
  scale_y_continuous(lim = c(0, 0.1), breaks = seq(0, 0.1, 0.01)) +
  facet_wrap(~modelname, nrow = 1) +
  scale_color_brewer(palette = 'Dark2') +
  scale_fill_brewer(palette = 'Dark2') +
  labs(x = expr(italic(Pf) * 'PR'['2 to 10']),
       y = 'Severe cases ppa',
       color = 'Age group',
       fill = 'Age group',
       caption='' ) +
  f_getCustomTheme()
p2b

# Combine single plots into panels of figure and save ----------------------------

# add caption to bottom right figure
p2b <- p2b + labs(caption = glue('{exp_name} - {datetoday}'))

pB <- plot_combine(list(p2a, p2b), ncol = 1, labels = c('c', 'd'))
pA <- plot_grid(p1, p0, ncol = 1, labels = c('a', 'b'))

pplot <- plot_grid(pA, pB, rel_widths = c(0.5, 1), align = 'hv')
print(pplot)

f_save_plot(pplot, 'epiplot_v1', plot_dir = proj_fig_dir, height = 8, width = 13)

