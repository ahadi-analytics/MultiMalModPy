from plotter.plot_timeseries import monthly_timeseries
from plotter.plot_agecurves import age_curves
from plotter.plot_relationship import eir_to_outcome, prevalence2to10_to_outcome


def generate_plots_example1(out_dir, exp, df, df_mth):

    # Plot 1
    # print(df_mth['target_output_values'].unique())
    if exp.target_output_name == "prevalence_2to10":
        sub_values = [0.25, 0.5]
    if exp.target_output_name == "eir":
        sub_values = [1.0, 5.0]  # FIXME some plots do not allow single facets (i.e. for 5.0 only)
    df_mth_sub = df_mth[df_mth['target_output_values'].round(1).isin(sub_values)]

    if df_mth_sub.empty:
        df_mth_sub = df_mth  # Fallback to the original dataframe

    monthly_timeseries(out_dir, df_mth_sub, channel='prevalence_2to10', sweepvar='models', facet_var='target_output_values',
                       agegrps='0-100', facet_name = exp.target_output_name)

    # Plot 2
    age_groups_aggregates_sub = [x for x in exp.age_groups_aggregates if x not in ([[0, 5], [0, 100]])]
    age_groups_aggregates_sub = ["{}-{}".format(sublist[0], sublist[1]) for sublist in age_groups_aggregates_sub]

    if exp.target_output_name == "prevalence_2to10":
        sub_values = [0.25, 0.5]
    if exp.target_output_name == "eir":
        sub_values = [1.0, 5.0, 1000.0]

    df_sub = df[df['target_output_values'].round(1).isin(sub_values)]
    if df_sub.empty:
        df_sub = df  # Fallback to the original dataframe

    age_curves(out_dir, df_sub, channel='clinical_incidence', sweepvar='target_output_values', facet_var='models',
               age_groups_aggregates=age_groups_aggregates_sub)

    # Plot 3
    eir_to_outcome(out_dir, df, sweepvar='models', facet_var='cm_clinical', eir_val='simulatedEIR',  channel='prevalence_2to10',  agegrps='0-100')
    prevalence2to10_to_outcome(out_dir, df, sweepvar='cm_clinical', facet_var='models', channel='clinical_incidence', agegrps=['0-100'])