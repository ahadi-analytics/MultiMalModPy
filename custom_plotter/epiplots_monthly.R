###-------------------------------------------------------------------------------------------------------
### Custom R plotter to create basic EIR-PfPR and PfPR-Incidence plots for EMOD and OpenMalaria
### Draft version disaggregated by month, keep emodom as lines for direct comparison
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
# Monthly EIR inputs and simultion outputs  -------------------------------
# OpenMalaria extracted EIR (in forced EIR not available for EMOD)
dateir_mth <- fread(file.path(wdir, 'om', 'OM_EIR_mth.csv')) %>%
  filter(year < 2001 &
           eir == 64 &
           seasonality == 'seasonal') %>%
  group_by(month, seasonality, cm_clinical, eir) %>%
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


# Seasonality EIR figure  -------------------------------
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
  labs(subtitle = '',
       y = 'monthly EIR scaling',
       x = 'Month of year',
       fill = '', col = '', caption = '') +
  theme(legend.position = c(0.65, 0.90)) +
  f_getCustomTheme()
p0

# Seasonality PfPR figure -------------------------------
p0a <- dat_mth %>%
  group_by(eir, month, emodom) %>%
  summarize(mean_val = mean(prevalence_2to10),
            min_val = min(prevalence_2to10),
            max_val = max(prevalence_2to10)) %>%
  ggplot() +
  geom_ribbon(aes(x = month, ymin = min_val, ymax = max_val, fill = emodom,
                  group = emodom), alpha = 0.3) +
  geom_line(aes(x = month, y = mean_val, col = emodom)) +
  scale_y_continuous(lim = c(0, 1), breaks = seq(0, 1, 0.2)) +
  scale_x_continuous(lim = c(1, 12), breaks = c(1:12)) +
  scale_color_brewer(palette = 'Set1') +
  scale_fill_brewer(palette = 'Set1') +
  labs(y = expr(italic(Pf) * 'PR'['2 to 10']),
       x = 'Month of year\n(mean across years)') +
  f_getCustomTheme()
p0a

# Seasonality clinical cases figure -------------------------------
p0b <- dat_mth %>%
  group_by(eir, month, emodom) %>%
  summarize(mean_val = mean(clinical_incidence),
            min_val = min(clinical_incidence),
            max_val = max(clinical_incidence)) %>%
  ggplot() +
  geom_ribbon(aes(x = month, ymin = min_val, ymax = max_val, fill = emodom,
                  group = emodom), alpha = 0.3) +
  geom_line(aes(x = month, y = mean_val, col = emodom)) +
  scale_y_continuous(lim = c(0, 6), breaks = seq(0, 6, 1)) +
  scale_x_continuous(lim = c(1, 12), breaks = c(1:12)) +
  scale_color_brewer(palette = 'Set1') +
  scale_fill_brewer(palette = 'Set1') +
  labs(y = 'Clinical cases ppa',
       x = 'Month of year\n(mean across years)', caption = '') +
  f_getCustomTheme()
p0b

# Seasonality severe cases figure -------------------------------
p0c <- dat_mth %>%
  filter(age_group == '0-5' &
           eir == 64 &
           seasonality == 'seasonal') %>%
  group_by(eir, month, emodom) %>%
  summarize(mean_val = mean(severe_incidence),
            min_val = min(severe_incidence),
            max_val = max(severe_incidence)) %>%
  ggplot() +
  geom_ribbon(aes(x = month, ymin = min_val, ymax = max_val, fill = emodom,
                  group = emodom), alpha = 0.3) +
  geom_line(aes(x = month, y = mean_val, col = emodom)) +
  scale_y_continuous(lim = c(0, 0.15), breaks = seq(0, 0.15, 0.05)) +
  scale_x_continuous(lim = c(1, 12), breaks = c(1:12)) +
  scale_color_brewer(palette = 'Set1') +
  scale_fill_brewer(palette = 'Set1') +
  labs(y = 'Severe cases ppa',
       x = 'Month of year\n(mean across years)', caption = '') +
  f_getCustomTheme()
p0c


# Combine single plots into panels of figure and save ----------------------------
# add caption to bottom right figure
p0c <- p0c + labs(caption = glue('{exp_name} - {datetoday}'))

pB <- plot_combine(list(p0a, p0b, p0c), ncol = 2, labels = c('a', 'b', 'c'))
print(pB)

f_save_plot(pB, 'monthly_epiplot_DRAFT', plot_dir = proj_fig_dir, height = 7, width = 13)

