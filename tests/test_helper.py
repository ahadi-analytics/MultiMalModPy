import os
from unittest.mock import patch

import manifest
import numpy as np
import pandas as pd
import pytest
from utility.experiment import LoadExperiment
from utility.helper import get_param_from_dataframe, parse_launch_args, rep_scen_df
from utility.helper_simulation import *


@pytest.fixture
def dummy_exp():

    if __name__ == "__main__" and any(
        arg.endswith("launch_sim.py") for arg in sys.argv
    ):
        args = parse_launch_args()
    else:
        from utility.helper_local import LoadLaunchArgs

        args = LoadLaunchArgs()

    # return DummyExperiment()
    return LoadExperiment(args, manifest)


# ----------------- TEST: get_param_from_dataframe -----------------
@pytest.fixture
def example_scenario_CSV():
    # Creates a DataFrame equivalent to the contents of example1.csv
    data = {
        "rownum": [0, 1],
        "exp_name": ["example_scen1", "example_scen2"],
        "entomology_mode": ["dynamic", "dynamic"],
        "seasonality": ["perennial", "seasonal"],
        "target_output_name": ["eir", "prevalence_2to10"],
        "target_output_values": [
            "1.0 ,   1.64,   2.68,   4.39,   5,  7.2 ,   11.79,  19.31,  31.62,   51.79,  "
            " 84.83,  138.95,  227.58,  372.76,  610.54, 1000",
            "0.25, 0.5",
        ],
        "case_management": ["(0, 0), (0.15, 0.5)", "(0, 0), (0.15, 0.5)"],
        "plots_to_run": ["custom", "custom"],
    }
    return pd.DataFrame(data)


def test_get_param_from_dataframe(dummy_exp, example_scenario_CSV):
    exp_scen_df = example_scenario_CSV
    exp_scen_df = exp_scen_df[exp_scen_df["rownum"] == 0]

    ## Overwriting default parameters with parameters specific in scenario csv file
    not_param_columns = ["rownum", "exp_name"]
    for col in exp_scen_df.columns:
        if col not in not_param_columns:
            setattr(
                dummy_exp,
                col,
                get_param_from_dataframe(exp_scen_df, col, dummy_exp.sim_params_list),
            )

    # Assertions
    assert dummy_exp.seasonality == ["perennial"]
    assert dummy_exp.entomology_mode == "dynamic"
    assert dummy_exp.target_output_name == "eir"
    assert dummy_exp.target_output_values == [
        1.0,
        1.64,
        2.68,
        4.39,
        5.0,
        7.2,
        11.79,
        19.31,
        31.62,
        51.79,
        84.83,
        138.95,
        227.58,
        372.76,
        610.54,
        1000.0,
    ]
    assert dummy_exp.case_management == [(0, 0), (0.15, 0.5)]
    assert dummy_exp.plots_to_run == ["custom"]


# ----------------- TEST: rep_scen_df -----------------
@pytest.fixture
def basic_scenario_df():
    # Creates a basic DataFrame for testing with single `num_seeds`
    data = {"scen_id": [1, 2], "param1": ["A", "B"], "param2": [10, 20], "num_seeds": 3}
    return pd.DataFrame(data)


def test_rep_scen_df_basic_repetition(basic_scenario_df):
    # Test that the DataFrame repeats according to num_seeds column
    rep_df = rep_scen_df(basic_scenario_df)

    # Check the number of rows is correct (2 rows, each repeated 3 times)
    assert len(rep_df) == 2 * 3  # 2 rows with 3 seeds each

    # Check if 'seed' is correctly assigned
    assert rep_df["seed"].iloc[0] == 1
    assert rep_df["seed"].iloc[1] == 2
    assert rep_df["seed"].iloc[2] == 3
    assert rep_df["seed"].iloc[3] == 1
    assert rep_df["seed"].iloc[4] == 2
    assert rep_df["seed"].iloc[5] == 3


def test_rep_scen_df_missing_index_column(basic_scenario_df):
    # Test that the function works when there is no 'index' column
    basic_scenario_df.drop(columns=["index"], errors="ignore", inplace=True)
    rep_df = rep_scen_df(basic_scenario_df)

    # Ensure the function runs without errors
    assert "index" in rep_df.columns  # Ensure the 'index' column is added
    assert len(rep_df) == 2 * 3  # Again, check correct repetition


def test_rep_scen_df_index_reset(basic_scenario_df):
    # Test that the index is reset correctly
    rep_df = rep_scen_df(basic_scenario_df)

    # Ensure the 'index' column starts at 1 and increments correctly
    assert rep_df["index"].iloc[0] == 1
    assert rep_df["index"].iloc[1] == 2
    assert rep_df["index"].iloc[2] == 3
    assert rep_df["index"].iloc[3] == 4
    assert rep_df["index"].iloc[4] == 5
    assert rep_df["index"].iloc[5] == 6


# ----------------- TEST: create_scenarios_csv_combinations -----------------
def test_create_scenarios_csv_combinations(dummy_exp):

    # Patch processing functions to just return the dataframe
    with patch("utility.helper.process_case_management", lambda df: df), patch(
        "utility.helper.map_model_calib_inputs", lambda exp, df: df
    ), patch("utility.helper_interventions.scenario_df_to_update", lambda exp, df: df):
        from utility.helper import create_scenarios_csv  # import inside patch context

        df = create_scenarios_csv(dummy_exp, None)

    # Check default columns
    expected_cols = [
        "index",
        "scen_id",
        "target_output_values",
        "case_management",
        "seasonality",
        "entomology_mode",
        "num_seeds",
    ]
    for col in expected_cols:
        assert col in df.columns

    # Check number of rows: 2 x 2 x 2 = 8 combinations
    assert len(df) == len(dummy_exp.target_output_values) * len(
        dummy_exp.case_management
    ) * len(dummy_exp.seasonality)

    # Check entomology_mode and num_seeds are identical across all rows
    assert all(df["entomology_mode"] == dummy_exp.entomology_mode)
    assert all(df["num_seeds"] == dummy_exp.num_seeds)

    # Check index and scen_id start at 1 and increment
    assert df["index"].iloc[0] == 1
    assert df["scen_id"].iloc[0] == 1
    assert df["index"].iloc[-1] == len(df)
    assert df["scen_id"].iloc[-1] == len(df)
