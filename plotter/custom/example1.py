import os
from plotter.plot_timeseries import monthly_timeseries
from plotter.plot_agecurves import age_curves
from plotter.plot_relationship import eir_to_outcome, prevalence2to10_to_outcome


def combine_plot_example1(
    panel_a_name,
    panel_b_name,
    panel_c_name,
    panel_a_path,
    panel_b_path,
    panel_c_path,
    save_path=None,
    save_name="combined_figure.png",
    padding=30,
    panel_c_scale=1.2,
    panel_ab_gap=30,
    panel_c_padding=30,
):
    from PIL import Image, ImageDraw, ImageFont
    import matplotlib.font_manager as fm

    font_path = fm.findfont("DejaVu Sans", fallback_to_default=True)
    font = ImageFont.truetype(font_path, size=40)

    # Load images
    panel_a = Image.open(os.path.join(panel_a_path, panel_a_name))
    panel_b = Image.open(os.path.join(panel_b_path, panel_b_name))
    panel_c = Image.open(os.path.join(panel_c_path, panel_c_name))

    # Resize A and B to match width
    target_width = max(panel_a.width, panel_b.width)
    panel_a = panel_a.resize(
        (target_width, int(panel_a.height * target_width / panel_a.width))
    )
    panel_b = panel_b.resize(
        (target_width, int(panel_b.height * target_width / panel_b.width))
    )

    # Stack A and B vertically with gap
    stacked_height = panel_a.height + panel_b.height + panel_ab_gap
    stacked_left = Image.new("RGB", (target_width, stacked_height), (255, 255, 255))
    stacked_left.paste(panel_a, (0, 0))
    stacked_left.paste(panel_b, (0, panel_a.height + panel_ab_gap))

    # Add padding around A + B
    stacked_left_padded = Image.new(
        "RGB",
        (stacked_left.width + 2 * padding, stacked_left.height + 2 * padding),
        (255, 255, 255),
    )
    stacked_left_padded.paste(stacked_left, (padding, padding))

    # Resize Panel C to match height of padded left side and scale width
    target_height = stacked_left_padded.height
    panel_c = panel_c.resize(
        (
            int(panel_c.width * panel_c_scale * target_height / panel_c.height),
            target_height,
        )
    )

    # Add padding around Panel C
    panel_c_padded = Image.new(
        "RGB",
        (panel_c.width + 2 * panel_c_padding, panel_c.height + 2 * panel_c_padding),
        (255, 255, 255),
    )
    panel_c_padded.paste(panel_c, (panel_c_padding, panel_c_padding))

    # Combine into final image
    total_width = stacked_left_padded.width + panel_c_padded.width
    total_height = max(stacked_left_padded.height, panel_c_padded.height)
    combined_img = Image.new("RGB", (total_width, total_height), (255, 255, 255))
    combined_img.paste(stacked_left_padded, (0, 0))
    combined_img.paste(panel_c_padded, (stacked_left_padded.width, 0))

    # Add labels
    draw = ImageDraw.Draw(combined_img)
    label_offset = 10
    draw.text((label_offset, label_offset), "A", fill="black", font=font)
    draw.text(
        (label_offset, panel_a.height + panel_ab_gap + label_offset),
        "B",
        fill="black",
        font=font,
    )
    draw.text(
        (stacked_left_padded.width + label_offset, label_offset),
        "C",
        fill="black",
        font=font,
    )

    if save_path is None:
        save_path = panel_a_path
    combined_img.save(os.path.join(save_path, save_name))
    print(f"Combined figure saved to: {os.path.join(save_path, save_name)}")


def define_submit_combine_plot(out_dir, scen1_name, scen2_name):
    combine_plot_example1(
        panel_a_name="timeseries_monthly_prevalence_2to10_0_model_target_output_values.png",
        panel_b_name="eir_prevalence_2to10_0_cm_clinical_model.png",
        panel_c_name="agecurves_clinical_incidence_target_output_values_model.png",
        panel_a_path=os.path.join(out_dir, scen2_name, "plots/"),
        panel_b_path=os.path.join(out_dir, scen1_name, "plots/"),
        panel_c_path=os.path.join(out_dir, scen2_name, "plots/"),
        save_path=os.path.join(out_dir, scen2_name, "plots/"),
        padding=10,
        panel_ab_gap=70,
        panel_c_padding=10,
        panel_c_scale=1,
        save_name="figure_combined.png",
    )


def generate_plots_example1(
    out_dir, exp, df, df_mth, file_format="png", run_combine_plot=False
):
    if run_combine_plot:

        ## USER to modify, for combined plots across simulation experiments
        scen1_name = "example_scen1_forced_07_58_19"
        scen2_name = "example_scen2_forced_07_58_31"

        define_submit_combine_plot(
            os.path.dirname(os.path.dirname(out_dir)), scen1_name, scen2_name
        )

    else:

        # print(df_mth['target_output_values'].unique())
        if exp.target_output_name == "prevalence_2to10":
            sub_values = [0.25, 0.50]

        if exp.target_output_name == "eir":
            sub_values = [
                1.0,
                5.0,
            ]  # FIXME some plots do not allow single facets (i.e. for 5.0 only)

        if exp.target_output_name == "prevalence_2to10":

            # Plot A
            df_mth_sub = df_mth[
                df_mth["target_output_values"].round(2).isin(sub_values)
            ]
            if df_mth_sub.empty:
                df_mth_sub = df_mth  # Fallback to the original dataframe

            monthly_timeseries(
                out_dir,
                df_mth_sub,
                channel="prevalence_2to10",
                sweepvar="models",
                facet_var="target_output_values",
                agegrps="0-100",
                facet_name=exp.target_output_name,
                facet_layout="horizontal",
                width_per_col=8,
                height_per_row=5,
                space=0.15,
                file_format=file_format,
            )

            # Plot C
            age_groups_aggregates_sub = [
                x for x in exp.age_groups_aggregates if x not in ([[0, 5], [0, 100]])
            ]
            age_groups_aggregates_sub = [
                "{}-{}".format(sublist[0], sublist[1])
                for sublist in age_groups_aggregates_sub
            ]

            df_sub = df[df["target_output_values"].round(2).isin(sub_values)]
            if df_sub.empty:
                df_sub = df  # Fallback to the original dataframe

            age_curves(
                out_dir,
                df_sub,
                channel="clinical_incidence",
                sweepvar="target_output_values",
                facet_var="models",
                age_groups_aggregates=age_groups_aggregates_sub,
                facet_layout="vertical",
                width_per_col=7,
                height_per_row=5,
                space=0.5,
                file_format=file_format,
            )

        if exp.target_output_name == "eir":
            # Plot B
            eir_to_outcome(
                out_dir,
                df,
                sweepvar="cm_clinical",
                facet_var="models",
                eir_val="eir",
                channel="prevalence_2to10",
                agegrps="0-100",
                facet_layout="horizontal",
                width_per_col=5,
                height_per_row=5,
                space=0.3,
                file_format=file_format,
            )
