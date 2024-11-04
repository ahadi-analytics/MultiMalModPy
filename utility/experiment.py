from utility.helper import *
import warnings

class LoadExperiment:
    def __init__(self, args, manifest):
        """
        Initializes the CustomExperiment object with simulation and HPC settings based on the provided arguments
        and manifest.

        Args:
            args (argparse.Namespace): Parsed arguments containing various simulation settings.
            manifest (Manifest): Manifest object containing path and HPC configuration settings.
        """
        # Basic experiment settings
        self.SUITEname = args.suite
        self.exp_name = args.expname
        self.emod_step = args.emodstep
        self.models_to_run = args.models
        self.intervention_list = args.interventions
        self.run_mode = args.run_mode
        self.output_type = args.output_type
        self.start_year = 2000
        self.end_year = 2005
        self.mem_increase_factor = 5.0
        self.analyzer_script = ['analyze_sim.py']
        self.analyzer_list = ['all_age_analyzer', 'annual', '5day', 'monthly', 'timeavrg']
        self.plots_to_run = ['relationship', 'timeseries', 'agecurves'] # 'anova_rmse', 'ccstep', 'smc'  ## plot for internal version, cleanup in mmmpy public

        # User and directory settings
        self.user = args.user
        self.custom_subdir = self.user

        # Manifest-related settings
        self.hpc = manifest.hpc
        self.sh_hpc_config = manifest.sh_hpc_config
        self.selected_platform = manifest.selected_platform
        self.emod_build = manifest.emod_build
        self.emod_input_path = manifest.emod_input_path
        self.EMOD_venv = manifest.EMOD_venv
        self.OPENMALARIA_venv = manifest.OPENMALARIA_venv
        self.openmalaria_path = manifest.OPENMALARIA_PATH
        self.openmalaria_version = manifest.openmalaria_version
        self.openmalaria_input_path = manifest.openmalaria_input_path
        self.malariasimulation_input_path = manifest.malariasimulation_input_path
        self.job_directory_manifest = manifest.job_directory
        self.output_directory_manifest = manifest.output_directory
        self.interp_path = manifest.interp_path
        self.interp_csv = manifest.interp_csv
        self.burnin_directory = None

         # EMOD Settings
        self.emod_burnin = 200
        self.emod_pop_size = 10000
        self.emod_calib_params = args.emod_calib_params

        # malariasimulation Settings
        self.malariasimulation_burnin = 25
        self.malariasimulation_pop_size = 50000
        self.malariasimulation_script = 'malariasimulation_base.R'
        self.malariasimulation_parameter_variation = args.mpv

        # OpenMalaria Settings
        self.openmalaria_burnin = 25
        self.openmalaria_pop_size = 50000
        self.openmalaria_scaffold = "R0000GA"
        self.openmalaria_survey_step = '5d'


        # Entomology settings
        self.entomology_mode = 'dynamic'
        self.seasonality = ['perennial','seasonal']
        self.mem_increase_factor = 5.0

        # Age groups and case management settings
        #self.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]
        #self.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5], [0, 100]]
        self.agebins = [0.5, 1, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85,90,95, 100]
        self.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20,25], [25,30], [30,35],
                                    [35,40], [40,45], [45,50], [50,55], [55,60], [60,65], [65,70], [70, 75],
                                    [75,80], [80,85], [85,90], [90,95], [95,100], [0, 5], [0, 100]]
        self.cm_start = 1
        self.case_management = [(0,0)]
        self.detectionLimit = 40
        self.importation_rate = 0
        self.num_seeds_burnin = 1
        self.start_year = 2000
        self.end_year = 2005

        # Custom settings based on run_mode
        self.configure_run_mode()

        # Parameters to vary
        self.sweep_list = ['output_target', 'case_management', 'seasonality']
        if self.emod_calib_params:
            self.configure_calibration()

    def configure_run_mode(self):
        """
        Configures settings based on the specified run_mode.
        """
        if self.run_mode == 'calibrun':
            self.SUITEname = self.SUITEname.replace('test', 'calibrun')
            self.num_seeds = 20
            self.start_year = 2000
            self.end_year = 2005
            if self.output_type != 'eir':
                warnings.warn(f"Warning: output_type changed to 'eir' as required for calibrun (not {self.output_type})")
            self.output_type = 'eir'
            self.analyzer_list = ['timeavrg']
            self.plots_to_run = ['relationship']
            self.output_target = [0.25, 0.5, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 1.75, 2,
                                 2.5, 2.75, 3, 3.25, 4, 5, 6, 7, 8, 9,
                                 10, 12, 14, 16, 18, 20, 25, 30, 35, 40,
                                 45, 50, 100, 200, 500, 1000]
            if self.malariasimulation_parameter_variation:
                warnings.warn("Warning: malariasimulation should not use parameter variation during calibration run. Parameter variation is now set to False.")
                self.malariasimulation_parameter_variation = False

        elif self.run_mode == 'test' or self.run_mode is None:
            self.num_seeds = 20
            self.start_year = 2000
            self.end_year = 2005
            self.emod_burnin = 100
            self.openmalaria_burnin = 25
            self.malariasimulation_burnin = 25
            self.openmalaria_pop_size = 50000
            self.malariasimulation_pop_size = 50000
            self.emod_pop_size = 1000
            if self.output_type != 'eir':
                warnings.warn(f"Warning: output_type changed to 'eir' as required for test (not {self.output_type})")
                self.output_type = 'eir'
            self.output_target = np.arange(1,4)

        elif self.run_mode == 'productionrun':
            self.SUITEname = self.SUITEname.replace('test', 'production')
            self.num_seeds = 20
            if self.output_type == 'eir':
                self.output_target = [20]
            elif self.output_type == 'prevalence_2to10':
                self.output_target = [0.05, 0.1, 0.2, 0.25, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]

        else:  # Default to simulation
            self.SUITEname = self.SUITEname.replace('test', 'sim')
            self.num_seeds = 3
            if self.output_type == 'eir':
                self.output_target = [1, 5, 10, 20, 50, 100, 500, 1000]
            elif self.output_type == 'prevalence_2to10':
                self.output_target = [0.05, 0.1, 0.2, 0.25, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]

    def configure_calibration(self):
        """
        Configures calibration settings if emod_calib_params is enabled.
        """
        calib_config_df = pd.read_csv(os.path.join(self.emod_input_path, 'emod_best.csv'))
        self.calib_config_pointer = range(0, len(calib_config_df))
        del calib_config_df
        self.sweep_list += ['calib_config_pointer']

    def update(self, **kwargs):
        """
        Update the Args object with new values.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

