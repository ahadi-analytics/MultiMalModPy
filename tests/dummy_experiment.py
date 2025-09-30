import os
import sys

import pytest


# ----------------- DummyExperiment -----------------
class DummyExperiment:
    def __init__(self):
        self.SUITEname = "TestSuite"
        self.csv = "test_csv"
        self.rownum = 1
        self.suite = "mmmpy_test_suite"
        self.expname = "mmmpy_test_exp"
        self.serializedid = ""
        self.models = ["malariasimulation"]  # 'EMOD'
        self.models_pickup = ["malariasimulation"]  # 'EMOD'
        self.user = os.environ.get("USER")
        self.custom_subdir = ""
        self.job_directory = ""
        self.output_directory = ""
        self.job_directory_manifest = ""
        self.interp_path = "/tmp/test_interp"
        self.interp_csv = "interp.csv"
        self.csv = None
        self.run_mode = "custom"
        self.overwrite = False
        self.test = True
        self.note = ""
        self.entomology_mode = "dynamic"
        self.seasonality = ["perennial", "seasonal"]
        self.cm_start = 1
        self.case_management = [(0, 0), (0.15, 0.5)]
        self.detectionLimit = 40
        self.target_output_name = "prevalence_2to10"
        self.target_output_values = [0.05, 0.1, 0.25]
        self.intervention_list = []
        self.sweep_list = ["target_output_values", "case_management", "seasonality"]
        self.agebins = [5, 10, 15, 20, 100]
        self.age_groups_aggregates = [
            [5, 10],
            [10, 15],
            [15, 20],
            [20, 100],
            [0, 5],
            [0, 100],
        ]

        # Simulation Settings
        self.num_seeds_burnin = 1
        self.num_seeds = 3
        self.start_year = 2000
        self.end_year = 2005
        self.mem_increase_factor = (
            1.0  # Currently the memory increase factor only effects the analyzers
        )

        # EMOD Settings
        self.emodstep = None
        self.emod_step = None
        self.emod_serialized_id = "abc123"
        self.burnin_directory = ""
        self.emod_burnin = 3
        self.emod_pop_size = 1000
        self.emod_calib_params = False
        self.emod_calib_type = "emod_severe"  # could be 'emod_severe' or 'emod_best'
        self.emod_memory_per_sim = 6  # memory is represented in gigabytes allocated for each SLURM job, i.e. 5GB
        self.emod_time_per_sim = (
            "3:59:00"  # time is represented in hours:minutes:seconds
        )
        self.emod_importation_rate = 0

        # malariasimulation Settings
        self.malariasimulation_burnin = 3
        self.malariasimulation_pop_size = 1000
        self.malariasimulation_memory_per_sim = 3
        self.malariasimulation_time_per_sim = "3:00:00"
        self.mpv = False

        # OpenMalaria Settings
        self.openmalaria_burnin = 3
        self.openmalaria_pop_size = 1000
        self.openmalaria_scaffold = "R0000GA"
        self.openmalaria_modeloptions = "R0000GA_model_options.txt"
        self.openmalaria_parameter = "R0000GA_parameter.txt"
        self.openmalaria_survey_step = "5d"
        self.openmalaria_memory_per_sim = 3
        self.openmalaria_time_per_sim = "2:00:00"
        self.openmalaria_importation_rate = 0

        # Framework Settings
        self.analyzer_script = ["analyze_sim.py"]
        self.analyzer_list = ["timeavrg", "annual", "monthly", "5day"]
        self.plots_to_run = ["relationship", "timeseries", "agecurves"]
        self.burnin_directory = None
        self.sim_params_list = [
            "seasonality",
            "sweep_list",
            "case_management",
            "eir",
            "intervention_list",
            "agebins",
            "target_output_values",
            "plots_to_run",
        ]

        # Derived parameters
        self.nexps = 36
        self.monitoring_years = 5
