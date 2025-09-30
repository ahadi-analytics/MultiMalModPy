import os
import tempfile
from unittest.mock import patch

import manifest
import numpy as np
import pandas as pd
import pytest
from utility.experiment import LoadExperiment
from utility.helper import parse_launch_args
from utility.helper_local import write_bat_submission_plots, write_ps1_runmodel


@pytest.fixture
def dummy_exp():

    # from tests.dummy_experiment import DummyExperiment
    if __name__ == "__main__" and any(
        arg.endswith("launch_sim.py") for arg in sys.argv
    ):
        args = parse_launch_args()
    else:
        from utility.helper_local import LoadLaunchArgs

        args = LoadLaunchArgs()

    # return DummyExperiment()
    return LoadExperiment(args, manifest)


# ----------------- TEST: write_ps1_runmodel -----------------
def test_write_ps1_runmodel_writes_file(tmp_path, dummy_exp):
    # Setup: create a job directory and log folder
    dummy_exp.job_directory = tmp_path / "job"
    log_dir = dummy_exp.job_directory / "log"
    log_dir.mkdir(parents=True, exist_ok=True)

    ps1_file = tmp_path / "run_model.ps1"

    # Call the function
    write_ps1_runmodel(dummy_exp, ps1_file, model="malariasimulation")

    # Assertions: file exists
    assert ps1_file.exists()

    # File contains expected script references
    content = ps1_file.read_text()
    assert "run_malariasimulation.ps1" in content
    assert "run_analyze_malariasimulation.ps1" in content
    assert str(log_dir / "run_malariasimulation.out") in content
    assert str(log_dir / "run_analyzer_malariasimulation.out") in content


def test_write_ps1_runmodel_invalid_model(tmp_path, dummy_exp):
    dummy_exp.job_directory = tmp_path / "job"
    dummy_exp.job_directory.mkdir(parents=True)

    with pytest.raises(ValueError, match="model cannot be empty"):
        write_ps1_runmodel(dummy_exp, tmp_path / "file.ps1", model="")


def test_write_ps1_runmodel_invalid_model(tmp_path, dummy_exp):
    dummy_exp.job_directory = tmp_path / "job"
    dummy_exp.job_directory.mkdir(parents=True)

    with pytest.raises(ValueError, match="model cannot be empty"):
        write_ps1_runmodel(dummy_exp, tmp_path / "file.ps1", model="")


def test_write_ps1_runmodel_invalid_directory(tmp_path, dummy_exp):
    dummy_exp.job_directory = tmp_path / "nonexistent"

    with pytest.raises(ValueError, match="Invalid job directory"):
        write_ps1_runmodel(dummy_exp, tmp_path / "file.ps1", model="malariasimulation")


# ----------------- TEST: write_bat_submission_plots -----------------


def test_write_bat_submission_plots(tmp_path, dummy_exp):
    # Setup job directory and output directory
    dummy_exp.job_directory = tmp_path / "job"
    dummy_exp.job_directory.mkdir(parents=True, exist_ok=True)
    dummy_exp.output_directory = tmp_path / "output"
    dummy_exp.output_directory.mkdir(parents=True, exist_ok=True)

    # Call the function
    write_bat_submission_plots(dummy_exp)

    # Check that the batch file was created
    bat_file = dummy_exp.job_directory / "submit_run_plots.bat"
    assert bat_file.exists()

    # Read content
    content = bat_file.read_text()

    # Check basic content
    assert 'cd "%work_dir%\\plotter"' in content
    assert "pause" in content

    # Check that each plot script appears
    for plot in dummy_exp.plots_to_run:
        script_line = f"python plot_{plot}.py --directory {dummy_exp.output_directory} --models {' '.join(dummy_exp.models)}"
        assert script_line in content

    # Check that log paths are correctly included
    for plot in dummy_exp.plots_to_run:
        log_path = f"%log_dir%\\run_plot_{plot}.log"
        err_path = f"%log_dir%\\run_plot_{plot}.err"
        assert log_path in content
        assert err_path in content
