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

# Load simulation outputs  -------------------------------
dat1 <- fread(file.path(wdir, 'om', 'OM_benchmark.csv')) %>% mutate(emodom = 'OpenMalaria')
dat2 <- fread(file.path(wdir, 'em', 'EMOD_benchmark.csv')) %>%
  mutate(emodom = 'EMOD') %>%
  mutate(eir = inputEIR)

# Combine dataframes (append rows)
dat <- dat1 %>% bind_rows(dat2)
agegrp_lbl <- c('0-5', '5-10', '10-15', '15-20')
dat$age_group <- factor(dat$age_group,
                        levels = agegrp_lbl,
                        labels = agegrp_lbl)

# Table to check entries per model and EIR
table(dat$eir, dat$emodom, exclude = NULL)
table(dat$age_group, dat$emodom, exclude = NULL)

# Additional monthly EIR inputs and simultion outputs  -------------------------------
# OpenMalaria extracted EIR (in forced EIR not available for EMOD)
dateir_mth <- fread(file.path(wdir, 'om', 'OM_EIR_mth.csv')) %>%
  filter(year < 2001 &
           eir == 64 &
           seasonality == 'seasonal') %>%
  group_by(month, seasonality, access, eir) %>%
  summarize(mean_val = mean(simulatedEIR)) %>%
  mutate(emodom = 'OpenMalaria - EIR sim') %>%
  ungroup() %>%
  select(eir, month, emodom, mean_val)

# OpenMalaria  EIR as in OM benchmarking (aggregated over years per month)
dat1_mth <- fread(file.path(wdir, 'om', 'OM_benchmark_mth.csv')) %>%
  filter(age_group == '0-5' &
           eir == 64 &
           seed == 0 &
           seasonality == 'seasonal') %>%
  group_by(eir, month) %>%
  filter(index == min(index)) %>%
  mutate(emodom = 'OpenMalaria - EIR aggregated sim')  # FIXME, annual aggregation over mths in OM

# EMOD monthly benchmarking outputs
dat2_mth <- fread(file.path(wdir, 'em', 'EMOD_benchmark_mth.csv')) %>%
  rename(seed = Run_Number,
         eir = inputEIR) %>%
  filter(age_group == '0-5' &
           eir == 64 &
           seed == 0 &
           seasonality == 'seasonal') %>%
  mutate(emodom = 'EMOD') %>%
  select(any_of(colnames(dat1_mth)))

# Combine
dat_mth <- dat1_mth %>% bind_rows(dat2_mth)

# Check
table(dat_mth$eir, dat_mth$emodom, exclude = NULL)
table(dat_mth$seed, dat_mth$emodom, exclude = NULL)

eir_seasonal_input <- c(0.89536936, 1., 0.99861637, 0.88644885, 0.69983342,
                        0.4785287, 0.29422502, 0.18798817, 0.18941683, 0.29804822,
                        0.4907383, 0.70506627)
eir_input_df <- data.frame(cbind('month' = c(1:12),
                                 'mean_val' = eir_seasonal_input,
                                 "emodom" = 'input EIR (scaled)')) %>%
  mutate(eir = 65,
         mean_val = as.numeric(mean_val) * 10,
         month = as.numeric(month)) %>%
  select(eir, month, emodom, mean_val)


# Annual EIR by PfPR 2to10 plot  (a) -------------------------------
p1 <- dat %>%
  filter(age_group == '0-5') %>%
  group_by(eir, seasonality, emodom) %>%
  summarize(pfpr2to10_mean = mean(prevalence_2to10),
            pfpr2to10_min = min(prevalence_2to10),
            pfpr2to10_max = max(prevalence_2to10)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = eir, ymin = pfpr2to10_min, ymax = pfpr2to10_max, fill = emodom,
                  group = interaction(seasonality, emodom)), alpha = 0.3) +
  geom_line(aes(x = eir, y = pfpr2to10_mean, col = emodom, linetype = seasonality)) +
  scale_y_continuous(lim = c(0, 1), breaks = seq(0, 1, 0.2)) +
  scale_x_log10(labels = comma) +  # + facet_wrap(~emodom)
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
  filter(emodom != 'EMOD' & emodom != 'OpenMalaria - EIR aggregated sim') %>%
  group_by(eir, month, emodom) %>%
  summarize(mean_val = mean(inputEIR),
            min_val = min(inputEIR),
            max_val = max(inputEIR)) %>%
  bind_rows(eir_input_df) %>%
  bind_rows(dateir_mth) %>%
  ggplot() +
  geom_hline(yintercept = 0, alpha = 0) +
  #geom_ribbon(aes(x = month, ymin = min_val, ymax = max_val, fill = emodom,
  #                group = emodom), alpha = 0.3) +
  geom_line(aes(x = month, y = mean_val, col = emodom)) +
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
  group_by(eir, age_group, emodom) %>%
  summarize(prevalence_2to10 = mean(prevalence_2to10),
            clinical_incidence_mean = mean(clinical_incidence),
            clinical_incidence_min = min(clinical_incidence),
            clinical_incidence_max = max(clinical_incidence)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = prevalence_2to10, ymin = clinical_incidence_min, ymax = clinical_incidence_max, fill = age_group,
                  group = interaction(age_group, emodom)), alpha = 0.3) +
  geom_line(aes(x = prevalence_2to10, y = clinical_incidence_mean, col = age_group)) +
  scale_y_continuous(lim = c(0, 6), breaks = seq(0, 6, 1)) +
  facet_wrap(~emodom, nrow = 1) +
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
  group_by(eir, age_group, emodom) %>%
  summarize(prevalence_2to10 = mean(prevalence_2to10),
            severe_incidence_mean = mean(severe_incidence),
            severe_incidence_min = min(severe_incidence),
            severe_incidence_max = max(severe_incidence)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = prevalence_2to10, ymin = severe_incidence_min, ymax = severe_incidence_max, fill = age_group,
                  group = interaction(age_group, emodom)), alpha = 0.3) +
  geom_line(aes(x = prevalence_2to10, y = severe_incidence_mean, col = age_group)) +
  scale_y_continuous(lim = c(0, 0.1), breaks = seq(0, 0.1, 0.01)) +
  facet_wrap(~emodom, nrow = 1) +
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

