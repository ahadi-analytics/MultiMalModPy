###-------------------------------------------------------------------------------------------------------
### Custom R plotter to create basic EIR-PfPR and PfPR-Incidence plots for EMOD and OpenMalaria
### Draft version separate plots by age, keep emodom as lines for direct comparison
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


# PfPR 2to10  and PfPR by age figure  (a) -------------------------------
# p1 <- dat %>%
#   rename(age = age_group) %>%
#   group_by(eir, seasonality, emodom, age) %>%
#   summarize(prevalence_2to10 = mean(prevalence_2to10),
#             prevalence_mean = mean(prevalence),
#             prevalence_min = min(prevalence),
#             prevalence_max = max(prevalence)) %>%
#   ggplot() +
#   geom_hline(yintercept = 0.8, linewidth = 0.3) +
#   geom_ribbon(aes(x = prevalence_2to10, ymin = prevalence_min, ymax = prevalence_max, fill = emodom,
#                   group = interaction(seasonality, emodom)), alpha = 0.3) +
#   geom_line(aes(x = prevalence_2to10, y = prevalence_mean, col = emodom, linetype = seasonality)) +
#   scale_y_continuous(lim = c(0, 6), breaks = seq(0, 6, 1)) +
#   facet_wrap(~age, nrow = 1, labeller = label_both) +
#   scale_color_brewer(palette = 'Set1') +
#   scale_fill_brewer(palette = 'Set1') +
#   labs(x = expr(italic(Pf) * 'PR'['2 to 10']),
#        y = expr(italic(Pf) * 'PR'),
#        linetype = 'seasonality,
#        color = '', fill = '', caption = '') +
#   f_getCustomTheme()

# PfPR 2to10  and clinical incidence by age figure  (b) -------------------------------
p2a <- dat %>%
  rename(age = age_group) %>%
  group_by(eir, seasonality, emodom, age) %>%
  summarize(prevalence_2to10 = mean(prevalence_2to10),
            clinical_incidence_mean = mean(clinical_incidence),
            clinical_incidence_min = min(clinical_incidence),
            clinical_incidence_max = max(clinical_incidence)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = prevalence_2to10, ymin = clinical_incidence_min, ymax = clinical_incidence_max, fill = emodom,
                  group = interaction(seasonality, emodom)), alpha = 0.3) +
  geom_line(aes(x = prevalence_2to10, y = clinical_incidence_mean, col = emodom, linetype = seasonality)) +
  scale_y_continuous(lim = c(0, 6), breaks = seq(0, 6, 1)) +
  facet_wrap(~age, nrow = 1, labeller = label_both) +
  scale_color_brewer(palette = 'Set1') +
  scale_fill_brewer(palette = 'Set1') +
  labs(x = expr(italic(Pf) * 'PR'['2 to 10']),
       y = 'Clinical cases ppa',
       linetype = 'seasonality',
       color = '', fill = '', caption = '') +
  f_getCustomTheme()

# PfPR 2to10  and severe incidence by age figure (c) -------------------------------
p2b <- dat %>%
  rename(age = age_group) %>%
  group_by(eir, seasonality, emodom, age) %>%
  summarize(prevalence_2to10 = mean(prevalence_2to10),
            severe_incidence_mean = mean(severe_incidence),
            severe_incidence_min = min(severe_incidence),
            severe_incidence_max = max(severe_incidence)) %>%
  ggplot() +
  geom_hline(yintercept = 0.8, linewidth = 0.3) +
  geom_ribbon(aes(x = prevalence_2to10, ymin = severe_incidence_min, ymax = severe_incidence_max, fill = emodom,
                  group = interaction(seasonality, emodom)), alpha = 0.3) +
  geom_line(aes(x = prevalence_2to10, y = severe_incidence_mean, col = emodom, linetype = seasonality)) +
  scale_y_continuous(lim = c(0, 0.1), breaks = seq(0, 0.1, 0.025)) +
  facet_wrap(~age, nrow = 1, labeller = label_both) +
  scale_color_brewer(palette = 'Set1') +
  scale_fill_brewer(palette = 'Set1') +
  labs(x = expr(italic(Pf) * 'PR'['2 to 10']),
       y = 'Severe cases ppa',
       linetype = 'seasonality',
       color = '', fill = '', caption = '') +
  f_getCustomTheme()
p2b

# Combine single plots into panels of figure and save ----------------------------

# add caption to bottom right figure
p2b <- p2b + labs(caption = glue('{exp_name} - {datetoday}'))

pplot <- plot_combine(list(p2a, p2b), labels = c('a', 'b'))
print(pplot)

f_save_plot(pplot, 'epiplot_incidence_by_age', plot_dir = proj_fig_dir, height = 6, width = 11)

