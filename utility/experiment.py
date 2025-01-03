from utility.helper import *
from utility.helper_calibration import *
from setup_sim import SimulationConfig
import warnings


class RunModeManager:
    def __init__(self, experiment):
        self.experiment = experiment

    def configure(self, run_mode):
        """
        Configures settings based on the specified run_mode.
        """
        if run_mode == 'calibrun':
            self._configure_calibrun()
        elif run_mode == 'test':
            self._configure_test()
        elif run_mode == 'productionrun':
            self._configure_productionrun()
        else:
            ## User provided values will be kept as is
            pass
            # self._configure_simulation()

    def _configure_calibrun(self):
        self.experiment.SUITEname = self.experiment.SUITEname.replace('test','calibrun')
        self.experiment.importation_rate = 5
        self.experiment.num_seeds = 20
        self.experiment.start_year = 2000
        self.experiment.end_year = 2005
        self.experiment.emod_burnin = 100
        self.experiment.openmalaria_burnin = 100
        self.experiment.malariasimulation_burnin = 100
        self.experiment.openmalaria_pop_size = 50000
        self.experiment.malariasimulation_pop_size = 50000
        self.experiment.emod_pop_size = 1000
        if self.experiment.output_type != 'eir':
            warnings.warn(
                f"Warning: output_type changed to 'eir' as required for calibrun (not {self.experiment.output_type})")
        self.experiment.output_type = 'eir'
        self.experiment.analyzer_list = ['timeavrg']
        self.experiment.plots_to_run = ['relationship']
        self.output_target = np.arange(1, 31)
        #self.experiment.output_target = [0.25, 0.5, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 1.75, 2,
        #                                 2.5, 2.75, 3, 3.25, 4, 5, 6, 7, 8, 9,
        #                                 10, 12, 14, 16, 18, 20, 25, 30, 35, 40,
        #                                 45, 50, 100, 200, 500, 1000]

        ## Configure calib run
        eir_range, x_temp_range = get_calib_range()
        self.experiment.eir_range = eir_range
        self.experiment.x_temp_range =x_temp_range

        if self.experiment.malariasimulation_parameter_variation:
            warnings.warn(
                "Warning: malariasimulation should not use parameter variation during calibration run. Parameter variation is now set to False.")
            self.experiment.malariasimulation_parameter_variation = False

    def _configure_test(self):
        self.experiment.num_seeds = 3
        self.experiment.start_year = 2000
        self.experiment.end_year = 2005
        self.experiment.emod_burnin = 25
        self.experiment.openmalaria_burnin = 25
        self.experiment.malariasimulation_burnin = 25
        self.experiment.openmalaria_pop_size = 1000
        self.experiment.malariasimulation_pop_size = 1000
        self.experiment.emod_pop_size = 1000
        if self.experiment.output_type == 'eir':
            self.experiment.output_target = np.arange(1, 4)
        if self.experiment.output_type == 'prevalence_2to10':
            self.experiment.output_target = [0.1, 0.25, 0.5]
        if self.experiment.output_type == 'clinical_incidence_U5':
            self.experiment.output_target = [0.5, 1.2, 2.0]

    def _configure_productionrun(self):
        self.experiment.SUITEname = self.experiment.SUITEname.replace('test', 'production')
        self.experiment.num_seeds = 20
        if self.experiment.output_type == 'eir':
            self.experiment.output_target = [20]
        if self.experiment.output_type == 'prevalence_2to10':
            self.experiment.output_target = [0.05, 0.1, 0.2, 0.25, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]
        if self.experiment.output_type == 'clinical_incidence_U5':
            raise ValueError('output_type clinical_incidence_U5 not defined for production run')

    # def _configure_simulation(self):
    #     self.experiment.SUITEname = self.experiment.SUITEname.replace('test', 'sim')
    #     self.experiment.num_seeds = 3
    #     if self.experiment.output_type == 'eir':
    #         self.experiment.output_target = [1, 5, 10, 20, 50, 100, 500, 1000]
    #     if self.experiment.output_type == 'prevalence_2to10':
    #         self.experiment.output_target = [0.05, 0.1, 0.2, 0.25, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]


class ArgsConfig:
    """
    Manages user-defined parameters provided via args when launching simulations.
    """

    def __init__(self, args):
        self.SUITEname = args.suite
        self.exp_name = args.expname
        self.emod_step = args.emodstep
        self.models_to_run = args.models
        self.intervention_list = args.interventions  # TODO move to MalariaConfig?
        self.run_mode = args.run_mode
        self.output_type = args.output_type
        # User and directory settings
        self.user = args.user
        self.custom_subdir = self.user

        self.emod_calib_params = args.emod_calib_params
        self.malariasimulation_parameter_variation = args.mpv


class ManifestConfig:
    """
    Encapsulates default settings from the manifest.
    """

    def __init__(self, manifest):
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


class LoadExperiment:
    def __init__(self, args, manifest):
        """
        Initializes the LoadExperiment object with simulation and HPC settings based on the provided arguments
        and manifest.

        Args:
            args (argparse.Namespace): Parsed arguments containing various simulation settings.
            manifest (Manifest): Manifest object containing path and HPC configuration settings.
        """
        # User and Manifest-related settings
        self.manifest_config = ManifestConfig(manifest)
        self._assign_attributes(self.manifest_config)

        # User-defined simulation setup
        self.simulation_config = SimulationConfig()
        self._assign_attributes(self.simulation_config)

        # User defined arguments when launching simulations
        self.args_config = ArgsConfig(args)
        self._assign_attributes(self.args_config)


        # Custom settings based on run_mode
        self.run_mode_manager = RunModeManager(self)
        self.run_mode_manager.configure(args.run_mode)
        self._assign_attributes(self.run_mode_manager)

        # Configure calibration if needed, #FIXME update naming
        if self.emod_calib_params:
            self.configure_calibration()

            
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

    def _assign_attributes(self, source_obj):
        """
        Assign all attributes from a source object to the current instance.

        Args:
            source_obj (object): The object from which attributes will be copied.
        """
        for key, value in vars(source_obj).items():
            setattr(self, key, value)
