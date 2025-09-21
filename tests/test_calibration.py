import pytest
import os
import numpy as np
import pandas as pd
from utility.experiment import LoadExperiment
from utility.helper import parse_launch_args
from utility.helper_calibration import output_target_to_eir, output_target_to_xTemp
import manifest

@pytest.fixture
def dummy_exp():

    # from tests.dummy_experiment import DummyExperiment

    if __name__ == "__main__" and any(arg.endswith("launch_sim.py") for arg in sys.argv):
        args = parse_launch_args()
    else:
        from utility.helper_local import LoadLaunchArgs
        args = LoadLaunchArgs()

    #return DummyExperiment()
    return LoadExperiment(args, manifest)


def dummy_interp_data(num_rows=10, seed=42, modelname="malariasimulation"):
    np.random.seed(seed)

    data = {
        "input_target": np.round(np.random.uniform(0.1, 2.5, num_rows), 8),
        "seasonality": ["perennial"] * num_rows,
        "cm_clinical": [0] * num_rows,
        "cm_severe": [0] * num_rows,
        "eir": np.round(np.random.uniform(0.09, 2.5, num_rows), 9),
        "prevalence_2to10": np.round(np.random.uniform(0.01, 0.25, num_rows), 9),
        "prevalence": np.round(np.random.uniform(0.01, 0.2, num_rows), 9),
        "severe_incidence": np.round(np.random.uniform(0.001, 0.006, num_rows), 9),
        "n_total_mos_pop": np.round(np.random.uniform(3000, 22000, num_rows), 6),
        "clinical_incidence": np.round(np.random.uniform(0.03, 0.35, num_rows), 9),
        "clinical_incidence_U5": np.round(np.random.uniform(0.01, 0.35, num_rows), 9),
        "models": [modelname] * num_rows,
        "pop_size": [50000] * num_rows,
        "importation": ["FALSE"] * num_rows
    }

    return pd.DataFrame(data)


# Test function
def test_output_target_to_eir(tmp_path, dummy_exp):
    # Create dummy interpolation data
    interp_df = dummy_interp_data(num_rows=30)

    # Save to a temp CSV in a mock directory structure
    model_name = "malariasimulation"
    model_dir = tmp_path / model_name
    model_dir.mkdir()
    csv_path = model_dir / "interp.csv"
    interp_df.to_csv(csv_path, index=False)

    # Create dummy experiment
    exp = dummy_exp
    exp.interp_path = tmp_path  # Set path to the temporary directory
    exp.interp_csv = "interp.csv"  # Set CSV filename
    exp.target_output_name = "eir"  # Set target output name as 'eir'
    exp.test = True  # Enable test mode (optional, based on your logic)

    # Create input dataframe for the test
    test_input = pd.DataFrame({
        "target_output_values": [0.5, 1.0, 2.0],
        "seasonality": ["perennial"] * 3,
        "cm_clinical": [0, 0, 0],
        "cm_severe": [0, 0, 0]
    })

    # Run the function with the test input
    result = output_target_to_eir(test_input, exp, model_name)

    # Assertions to check the validity of the results
    assert len(result) == len(test_input)
    assert all(isinstance(r, float) for r in result)
    assert all(0.01 <= r <= 1000 for r in result)



# Test function
def test_output_target_to_xTemp(tmp_path, dummy_exp):
    # Create dummy interpolation data
    interp_df = dummy_interp_data(num_rows=30)

    # Save to a temp CSV in a mock directory structure
    model_name = "malariasimulation"
    model_dir = tmp_path / model_name
    model_dir.mkdir()
    csv_path = model_dir / "interp.csv"
    interp_df.to_csv(csv_path, index=False)

    # Create dummy experiment
    exp = dummy_exp
    exp.interp_path = tmp_path  # Set path to the temporary directory
    exp.interp_csv = "interp.csv"  # Set CSV filename
    exp.target_output_name = "eir"  # Set target output name as 'eir'
    exp.test = True  # Enable test mode (optional, based on your logic)

    # Create input dataframe for the test
    test_input = pd.DataFrame({
        "target_output_values": [0.5, 1.0, 2.0],
        "seasonality": ["perennial"] * 3,
        "cm_clinical": [0, 0, 0],
        "cm_severe": [0, 0, 0]
    })

    # Run the function with the test input
    result = output_target_to_xTemp(test_input, exp, model_name)

    # Assertions to check the validity of the results
    assert len(result) == len(test_input)
    assert all(isinstance(r, float) for r in result)
    assert all(0.01 <= r <= 10000 for r in result)

