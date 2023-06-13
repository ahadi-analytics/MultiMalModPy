library(data.table)
library(dplyr)
library(glue)
library(wrapr)
library(cowplot)
theme_set(theme_bw())


source('functions.R')
wdir <- 'C:/Users/mrm9534/NU Malaria Modeling Dropbox/Manuela Runge/popsize_runs_sweep'  #FIXME hardcoded path for custom plot

dat <- fread(file.path(wdir, 'comb', 'benchmark.csv'))
head(dat)
max(dat$seed)

seeds_grp <- c(1, 3, 5, 10, 25)
datlist <- list()
for (rs in c(1:100)) {
  for (s in seeds_grp) {
    rnd_seeds <- sample(unique(dat$seed), s) ## successful seeds might be different in both models
    datlist[[length(datlist) + 1]] <- dat %>%
      group_by(emodom) %>%
      #filter(seed %in% rnd_seeds) %>% #%>%
      filter(seed %in% sample(seed, s)) %>%
      group_by(eir, seasonality, access, pop_size, emodom, age_group) %>%
      summarize(clinical_incidence = mean(clinical_incidence),
                severe_incidence = mean(severe_incidence),
                prevalence_2to10 = mean(prevalence_2to10),
                simulatedEIR = mean(simulatedEIR)) %>%
      mutate(resample_run = rs,
             nseeds = s)
  }
}
dat_seeds <- datlist %>% bind_rows()

table(dat_seeds$age_group)
table(dat_seeds$eir)

##### aggregated for 20 years after 80 year burnin
sdf <- dat %>%
  filter(age_group == '0-5') %>%
  group_by(emodom, eir) %>%
  summarise(meanval = mean(clinical_incidence),
            minval = quantile(clinical_incidence, 0.1),
            maxval = quantile(clinical_incidence, 0.9))

pdat <- subset(dat_seeds, age_group == '0-5') %>%
  left_join(sdf)


ggplot(data = pdat) +
  geom_hline(aes(yintercept = 1)) +
  geom_hline(aes(yintercept = 0.95), alpha = 0) +
  geom_hline(aes(yintercept = 1.05), alpha = 0) +
  geom_boxplot(aes(x = as.factor(nseeds), y = clinical_incidence / meanval, group = interaction(emodom, nseeds), fill = emodom),
               position = position_dodge(width = 0.6), width = 0.6) +
  facet_grid(eir ~ pop_size) +
  theme(legend.position = 'top') +
  labs(x = 'Number of random seeds', y = 'Ratio to mean clinical\nincidence (0.25-5 years)',
       fill = '',
       subtitle = 'aggregated for 20 years after 80 year burnin',
       caption = 'resampled 50 times') +
  f_getCustomTheme()

ggsave(glue('clinical_incidence_by_seeds_{season}.png'), path = file.path(wdir, 'comb'),
       width = 10, height = 6, units = 'in', device = "png")


sdf <- dat %>%
  filter(age_group == '0-5') %>%
  group_by(emodom, eir) %>%
  summarise(meanval = mean(severe_incidence),
            minval = quantile(severe_incidence, 0.1),
            maxval = quantile(severe_incidence, 0.9))

pdat <- subset(dat_seeds, age_group == '0-5') %>%
  left_join(sdf)


ggplot(data = pdat) +
  geom_hline(aes(yintercept = 1)) +
  geom_hline(aes(yintercept = 0.95), alpha = 0) +
  geom_hline(aes(yintercept = 1.05), alpha = 0) +
  geom_boxplot(aes(x = as.factor(nseeds), y = severe_incidence / meanval, group = interaction(emodom, nseeds), fill = emodom),
               position = position_dodge(width = 0.6), width = 0.6) +
  facet_grid(eir ~ pop_size) +
    scale_y_continuous(lim=c(0.8, 2)) +
  theme(legend.position = 'top') +
  labs(x = 'Number of random seeds', y = 'Ratio to mean severe\nincidence (0.25-5 years)',
       fill = '',
       subtitle = 'aggregated for 20 years after 80 year burnin', caption = 'resampled from 100 seeds 100 times') +
  f_getCustomTheme()

ggsave(glue('severe_incidence_by_seeds_{season}.png'), path = file.path(wdir, 'comb'),
       width = 10, height = 6, units = 'in', device = "png")


sdf <- dat %>%
  filter(age_group == '0-5') %>%
  group_by(emodom, eir) %>%
  summarise(meanval = mean(prevalence_2to10),
            minval = quantile(prevalence_2to10, 0.1),
            maxval = quantile(prevalence_2to10, 0.9))

pdat <- subset(dat_seeds, age_group == '0-5') %>%
  left_join(sdf)

ggplot(data = pdat) +
  geom_hline(aes(yintercept = 1)) +
  geom_hline(aes(yintercept = 0.95), alpha = 0) +
  geom_hline(aes(yintercept = 1.05), alpha = 0) +
  geom_boxplot(aes(x = as.factor(nseeds), y = prevalence_2to10 / meanval, group = interaction(emodom, nseeds), fill = emodom),
               position = position_dodge(width = 0.6), width = 0.6) +
  facet_grid(eir ~ pop_size) +
  theme(legend.position = 'top') +
  labs(x = 'Number of random seeds', y = 'Ratio to mean pfpr2-10',
       fill = '',
       subtitle = 'aggregated for 20 years after 80 year burnin',
       caption = 'resampled 50 times') +
  f_getCustomTheme()

ggsave(glue('pfpr_by_seeds_eir_{season}.png'), path = file.path(wdir, 'comb'),
       width = 10, height = 6, units = 'in', device = "png")
