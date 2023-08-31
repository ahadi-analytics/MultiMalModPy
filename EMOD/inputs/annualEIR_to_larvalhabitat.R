###-------------------------------------------------------------------------------------------------------
### Regression models to obtain x_Larval_Habitat_Multiplier from annual EIR (EMOD only)
###-------------------------------------------------------------------------------------------------------

source('functions.R')
library(tidyr)
theme_set(theme_bw())
datetoday <- Sys.Date()

if (Sys.getenv("OS") == "Windows_NT") {
  box <- 'NU Malaria Modeling Dropbox'
  projdir <- file.path(Sys.getenv('USERPROFILE'), box, 'projects/EMOD_OM')
}else {
  username <- Sys.getenv('USER') #Sys.getenv('USERNAME')
  projdir <- file.path('/projects/b1139/emod-om/simulation_outputs', username)
}


#exp_name <- 'sim_EMOD_dynamic_lhm_cm_sweep'
exp_name <- 'sim_EMOD_dynamic_exampleShift3m_LHSsweep'
subdir = 'seasonal_sims'  #'perennial_sims'
wdir <- file.path(projdir, 'simulation_outputs', subdir)
proj_fig_dir <- file.path(projdir, 'figures')

# dat <- fread(file.path(wdir, exp_name,  'em', 'annual_transmission_report.csv')) %>% mutate(exp_name = exp_name)
# dat_addon <- fread(file.path(wdir, 'sim_EMOD_dynamic_lhm_cm_sweep_cor', 'em', 'annual_transmission_report.csv')) %>% mutate(exp_name = 'addon')
# dat_addon2 <- fread(file.path(wdir, 'sim_EMOD_dynamic_lhm_cm_sweep_addon', 'em', 'annual_transmission_report.csv')) %>% mutate(exp_name = 'addon2')
dat <- fread(file.path(projdir, 'simulation_outputs/seasonal_sims', exp_name, 'em', 'annual_transmission_report.csv')) %>% mutate(exp_name = exp_name)
dat_addon <- fread(file.path(projdir, 'simulation_outputs/seasonal_sims', 'sim_EMOD_dynamic_exampleShift3m_LHSsweep_addon', 'em', 'annual_transmission_report.csv')) %>% mutate(exp_name = 'addon')
dat_addon2 <- fread(file.path(projdir, 'simulation_outputs/seasonal_sims', 'sim_EMOD_dynamic_exampleShift3m_LHSsweep_addon2', 'em', 'annual_transmission_report.csv')) %>% mutate(exp_name = 'addon2')

dat <- dat %>%
  bind_rows(dat_addon) %>%
  bind_rows(dat_addon2)

dat$x_Temporary_Larval_Habitat <- round(dat$x_Temporary_Larval_Habitat, 3)

dat <- dat %>%
  rename(annualEIR = `Annual EIR`) %>%
  mutate(annualEIR = ifelse(annualEIR < 1, round(annualEIR, 1), ifelse(annualEIR < 100, round(annualEIR, 0), round(annualEIR, -1))),
         annualEIR = ifelse(annualEIR > 500, round(annualEIR, -2), annualEIR))

sort(unique(dat$annualEIR))

dat <- dat %>%
  group_by(x_Temporary_Larval_Habitat, cm_clinical) %>%
  summarize(annualEIR_lo = min(annualEIR),
            annualEIR_up = max(annualEIR),
            annualEIR = mean(annualEIR),)


dat <- dat %>% filter(annualEIR > 0)
dat <- dat %>% mutate(annualEIR_log = log(annualEIR),
                      x_Temporary_Larval_Habitat_log = log(x_Temporary_Larval_Habitat))


dat <- dat %>%
  mutate(eir_grp = cut(annualEIR, c(-Inf, 5, 30, 100, Inf)),
         eir_grp2 = cut(annualEIR, c(-Inf, 5, Inf)))


eir_values <- c(0.1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)
xvalues = unique(dat$annualEIR)
x1_new <- unique(ifelse(xvalues < 1, round(xvalues, 1),
                        ifelse(xvalues < 100, round(xvalues, 0), round(xvalues, -1))))
x1_new <- sort(c(eir_values, x1_new))
x2_new = seq(0, 1, 0.2)
pred_dat <- expand_grid(x1_new, x2_new)
pred_dat <- data.frame(pred_dat, 'y_pred' = NA)
colnames(pred_dat) <- c('x1', 'x2', 'y_pred')


dat <- dat %>%
  dplyr::mutate(
    x1 = annualEIR,
    x2 = cm_clinical,
    y = x_Temporary_Larval_Habitat,
  )


fit_model2c = TRUE
if (fit_model2c) {

  ### Make predictions
  pred_list <- list()
  for (grp in unique(dat$eir_grp)) {

    dat_sub <- dat %>%
      filter(eir_grp == grp)
    pred_dat_sub <- pred_dat %>% filter(x1 <= ceiling(max(dat_sub$annualEIR)) & x1 >= floor(min(dat_sub$annualEIR)))

    dfGLM <- dat_sub %>%
      ungroup() %>%
      group_by(x2) %>%
      do(fitglm = glm(y ~ x1, data = .))

    for (i in c(1:nrow(dfGLM))) {
      glmmodel <- dfGLM[i, 'fitglm'][[1]]
      pred_dat_sub2 <- pred_dat_sub %>%
        mutate(x2 = as.numeric(as.character(x2))) %>%
        filter(x2 == as.numeric(dfGLM[i, 'x2']))
      pred_dat_sub2$y_pred <- predict(glmmodel[[1]], newdata = pred_dat_sub2, type = "response")
      pred_dat_sub2$eir_grp <- grp
      pred_list[[length(pred_list) + 1]] <- pred_dat_sub2
      rm(pred_dat_sub2)
    }
  }

  pred_dat_out <- pred_list %>% bind_rows()

  dat$eir_grp <- factor(dat$eir_grp, levels = c('(-Inf,5]', '(5,30]', '(30,100]', '(100, Inf]'),
                        labels = c('EIR < 5 ', 'EIR 5-30', 'EIR 30-100', 'EIR >100'))

  pred_dat_out$eir_grp <- factor(pred_dat_out$eir_grp, levels = c('(-Inf,5]', '(5,30]', '(30,100]', '(100, Inf]'),
                                 labels = c('EIR < 5 ', 'EIR 5-30', 'EIR 30-100', 'EIR >100'))

  p1a <- ggplot(data = dat) +
    geom_point(aes(x = log(x1), fill = as.factor(x2), y = log(y)), shape = 21, col = 'grey') +
    geom_line(data = dat, aes(x = log(x1), color = as.factor(x2), y = log(y)), linewidth = 0.3) +
    scale_color_brewer(palette = 'Dark2') +
    scale_fill_brewer(palette = 'Dark2') +
    labs(title = 'Simulated points', x = 'annual EIR (log)', y = 'x_Temporary_Larval_Habitat (log)', fill = 'cm_clinical', color = 'cm_clinical') +
    guides(colour = guide_legend(reverse = T), fill = guide_legend(reverse = T))


  p1b <- ggplot(data = dat) +
    geom_point(aes(x = x1, fill = as.factor(x2), y = y), shape = 21, col = 'grey') +
    geom_line(data = dat, aes(x = (x1), color = as.factor(x2), y = (y)), linewidth = 0.3) +
    scale_color_brewer(palette = 'Dark2') +
    scale_fill_brewer(palette = 'Dark2') +
    labs(x = 'annual EIR ', y = 'x_Temporary_Larval_Habitat', fill = 'cm_clinical', color = 'cm_clinical') +
    guides(colour = guide_legend(reverse = T), fill = guide_legend(reverse = T))

  p2 <- ggplot(data = dat) +
    geom_point(aes(x = x1, fill = as.factor(x2), y = y), shape = 21, col = 'grey') +
    geom_line(data = pred_dat_out, aes(x = x1, color = as.factor(x2), y = y_pred)) +
    facet_wrap(~eir_grp, scales = 'free') +
    scale_color_brewer(palette = 'Dark2') +
    scale_fill_brewer(palette = 'Dark2') +
    labs(title = 'Linear regression', x = 'annual EIR', y = 'x_Temporary_Larval_Habitat', fill = 'cm_clinical', color = 'cm_clinical') +
    guides(colour = guide_legend(reverse = T), fill = guide_legend(reverse = T))

  p1 <- plot_combine(list(p1a, p1b), ncol = 1, labels = c('a', 'b'))
  pplot <- plot_combine(list(p1, p2), ncol = 2, labels = c(' ', 'c'))

  f_save_plot(pplot, 'eir_to_lhs', plot_dir = getwd(), height = 6, width = 13)


}

pred_dat_out %>%
  mutate(x1 = as.numeric(as.character(x1)),
         x2 = as.numeric(as.character(x2))) %>%
  filter(x1 %in% eir_values) %>%
  group_by(x2) %>%
  mutate(y_pred = ifelse(y_pred < 1, round(y_pred, 3), round(y_pred, 2)),
         y_pred = ifelse(y_pred > 100, round(y_pred, 0), y_pred)) %>%
  dplyr::select(x1, x2, y_pred) %>%
  unique() %>%
  pivot_wider(names_from = x1, values_from = y_pred)

