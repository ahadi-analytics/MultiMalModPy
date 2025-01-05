from utility.helper import *
from utility.helper_calibration import *
from setup_sim import SimulationConfig
import warnings


class RunModeManager:
    """
    A manager class to configure and manage experiment settings based on the selected run mode.

    Attributes:
        experiment (object): An object representing the experiment configuration. This object is updated
                             with specific settings based on the chosen run mode and testing requirements.

    Methods:
        configure(run_mode, test):
            Configures the experiment settings based on the selected run mode and whether testing is enabled.
        _configure_calibration():
            Applies configuration specific to calibration runs, including output types, population sizes, and ranges.
        _configure_simple():
            Configures the experiment for simplified runs with reduced seeds and population settings.
        _configure_production():
            Configures the experiment for production-level runs, with optimized seeds and target ranges.
        _configure_csv():
            Reads experiment-specific settings from a CSV file and updates the experiment accordingly.
        _configure_test_overwrite():
            Overwrites settings to enable faster runs for testing or debugging purposes.
    """
    def __init__(self, experiment):
        self.experiment = experiment

    def configure(self, run_mode, test):
        """
        Configures the experiment based on the specified run mode.

        Args:
            run_mode (str): The mode of the run. Options include:
                - 'custom': No changes to the default setup.
                - 'calibration': Applies calibration-specific configurations.
                - 'simple': Simplified experimental setup.
                - 'production': Production-level configurations.
                - 'csv': Settings derived from a CSV file.
            test (bool): If True, applies test-specific overwrites for faster execution.
        """
        if run_mode == 'calibration':
            self._configure_calibration()
        elif run_mode == 'simple':
            self._configure_simple()
        elif run_mode == 'production':
            self._configure_production()
        elif run_mode == 'csv':
            self._configure_csv()
        elif run_mode == 'custom':
            ## User provided values will be kept as is
            pass
        else:
            raise ValueError(f"run_mode {run_mode} is not valid. ")

        # If test flag True, overwrite popsize, burnin and seeds to run a lower computational intensive simulation.
        # This is useful for debugging and testing new features as they allow for faster simulation runs (at the cost of being able to use results).
        if test:
            self._configure_test_overwrite()

    def _configure_calibration(self):
        self.experiment.SUITEname = f'{self.experiment.SUITEname}_calibration'
        self.experiment.importation_rate = 0 # need to be 0 for OpenMalaria and 5 for EMOD, we need to figure out a better way to do this.
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
                f"Warning: output_type changed to 'eir' as required for calibration (not {self.experiment.output_type})")
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

    def _configure_simple(self):
        """
        Configures the experiment for a pre-defined simple run.
        Using fewer seeds and reduced ranges for output targets.
        Keeps appropriate values for popsize and burnin to ensure accurary of results.
        """
        self.experiment.SUITEname = f'{self.experiment.SUITEname}_simple'
        self.experiment.num_seeds = 3
        self.experiment.emod_burnin = 100
        self.experiment.openmalaria_burnin = 100
        self.experiment.malariasimulation_burnin = 100
        self.experiment.openmalaria_pop_size = 50000
        self.experiment.malariasimulation_pop_size = 50000
        self.experiment.emod_pop_size = 1000
        if self.experiment.output_type == 'eir':
            self.experiment.output_target = np.arange(1, 4)
        if self.experiment.output_type == 'prevalence_2to10':
            self.experiment.output_target = [0.1, 0.25, 0.5]
        if self.experiment.output_type == 'clinical_incidence_U5':
            self.experiment.output_target = [0.5, 1.2, 2.0]

    def _configure_production(self):
        """
        Configures the experiment for a pre-defined production run.
        Using appropriate number of seeds and large ranges for output targets.
        """
        self.experiment.SUITEname = f'{self.experiment.SUITEname}_production'
        self.experiment.num_seeds = 20
        self.experiment.emod_burnin = 100
        self.experiment.openmalaria_burnin = 100
        self.experiment.malariasimulation_burnin = 100
        self.experiment.openmalaria_pop_size = 50000
        self.experiment.malariasimulation_pop_size = 50000
        self.experiment.emod_pop_size = 50000
        if self.experiment.output_type == 'eir':
            self.experiment.output_target = [20]
        if self.experiment.output_type == 'prevalence_2to10':
            self.experiment.output_target = [0.05, 0.1, 0.2, 0.25, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]
        if self.experiment.output_type == 'clinical_incidence_U5':
            raise ValueError('output_type clinical_incidence_U5 not defined for production run')

    def _configure_csv(self):
        """
        Configures the experiment based on user-defined parameters in the specified csv file
        If not specified, parameters as defined in setup_sim.py are used.
        """
        self.experiment.SUITEname = f'{self.experiment.SUITEname}_CSV'
        exp_scen_df = pd.read_csv(os.path.join(f'scenario_csv/{self.experiment.csv}.csv'))
        exp_scen_df = exp_scen_df[exp_scen_df['rownum'] == self.experiment.rownum]
        self.experiment.exp_name = f'{exp_scen_df.exp_name.iat[0]}_{dt.now().strftime("%H_%M_%S")}'

        ## Overwriting default parameters with parameters specific in scenario csv file
        not_param_columns = ['rownum', 'exp_name']
        for col in exp_scen_df.columns:
            if col not in not_param_columns:
                setattr(self.experiment, col, get_param_from_dataframe(exp_scen_df, col, self.experiment.sim_params_list))

    def _configure_test_overwrite(self):
        """
        Overwrites popsize, burnin periods and seeds to allow a faster run of simulations (i.e. for testing, debugging).
        """
        self.experiment.SUITEname = f'{self.experiment.SUITEname}_TEST'
        self.experiment.num_seeds = 3
        self.experiment.emod_burnin = 10
        self.experiment.openmalaria_burnin = 10
        self.experiment.malariasimulation_burnin = 10
        self.experiment.openmalaria_pop_size = 1000
        self.experiment.malariasimulation_pop_size = 1000
        self.experiment.emod_pop_size = 1000


class ArgsConfig:
    """
    A class to configure the user-defined parameters provided via command-line arguments when launching simulations.

    Attributes:
        SUITEname (str): Name of the simulation suite, typically used for grouping related experiments.
        exp_name (str): Name of the specific experiment being launched.
        models_to_run (list): List of models to execute in the simulation (e.g., ['EMOD', 'OpenMalaria']).
        run_mode (str): Specifies the type of simulation to run (e.g., 'custom', 'calibration', 'simple', 'production').
        test (bool): Indicates if the simulation should run in test mode with reduced resources.
        csv (str): Path to a CSV file specifying scenario parameters.
        rownum (int): Row number in the CSV file to be used for the current simulation.
        intervention_list (list): List of interventions to include in the simulation.
        output_type (str): Specifies the output alignment for the simulation (e.g., 'prevalence_2to10', 'eir').
        directory (str): Directory for storing or accessing simulation-related files.
        user (str): Name of the user launching the simulation; also used for organizing directories.
        custom_subdir (str): Subdirectory for simulations, often derived from the `user` attribute.
        emod_step (str): Specifies the EMOD simulation step (e.g., 'burnin', 'pickup', 'new_pickup').
        serializedid (str): Serialized ID for initializing an EMOD simulation.
        emod_calib_params (bool): Indicates if calibration parameters should be included for EMOD.
        malariasimulation_parameter_variation (bool): Specifies whether parameter variation is enabled for malariasimulation.

    Methods:
        __init__(args): Initializes the ArgsConfig object by mapping command-line arguments to attributes.
    """

    def __init__(self, args):
        self.SUITEname = args.suite
        self.exp_name = args.expname
        ## Parameter specifying setup and type of simulations to run and models to use
        self.models_to_run = args.models
        self.run_mode = args.run_mode
        self.test = args.test
        self.csv = args.csv
        self.rownum = args.rownum
        ## Allow to overwrite interventions or output_type if specified when running launch_sim.py
        self.intervention_list = args.interventions
        self.output_type = args.output_type
        # User and directory settings
        self.directory = args.directory
        self.user = args.user
        self.custom_subdir = self.user
        # Model specific args
        self.emod_step = args.emodstep
        self.serializedid = args.serializedid
        self.emod_calib_params = args.emod_calib_params
        self.malariasimulation_parameter_variation = args.mpv


class ManifestConfig:
    """
    A class to configure the parameters provided by the manifest.py .

    Attributes:
        hpc (bool): Indicates whether the simulation is configured to run on a High-Performance Computing (HPC) platform.
        sh_hpc_config (str): Path to the HPC configuration script or settings.
        selected_platform (str): The computing platform selected for the simulation (e.g., local, HPC, cloud).
        emod_build (str): Path or identifier for the EMOD build used in the simulation.
        emod_input_path (str): Path to the input files for the EMOD simulation framework.
        EMOD_venv (str): Path to the virtual environment for the EMOD framework.
        OPENMALARIA_venv (str): Path to the virtual environment for the OpenMalaria framework.
        openmalaria_path (str): Path to the OpenMalaria executable or installation directory.
        openmalaria_version (str): Version of the OpenMalaria framework being used.
        openmalaria_input_path (str): Path to the input files for OpenMalaria simulations.
        malariasimulation_input_path (str): Path to the input files for malariasimulation simulations.
        job_directory_manifest (str): Directory where job-specific files from the manifest are stored.
        output_directory_manifest (str): Directory where simulation output files from the manifest will be saved.
        interp_path (str): Path to the interpolation data files or directory.
        interp_csv (str): Path to the CSV file containing interpolation configuration or data.

    Methods:
        __init__(manifest): Initializes the ManifestConfig object by mapping manifest attributes to class attributes.
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
    """
    A class to initialize and manage the configuration of a simulation experiment, incorporating user-defined arguments,
    manifest settings, and runtime-specific configurations.

    Attributes:
        manifest_config (ManifestConfig): Encapsulates manifest-related settings, including HPC and path configurations.
        simulation_config (SimulationConfig): Stores simulation-related default settings and configurations.
        args_config (ArgsConfig): Manages user-defined arguments provided at launch.
        run_mode_manager (RunModeManager): Handles configuration of the experiment based on the specified run mode.
        emod_calib_params (bool): Indicates if EMOD calibration parameters are used.
        calib_config_pointer (range): Points to the indices of the calibration configuration data, if applicable.
        sweep_list (list): List of parameters to be included in the simulation sweeps.

    Methods:
        __init__(args, manifest):
            Initializes the LoadExperiment object by combining configurations from arguments, manifest, and simulation settings.

        configure_emod_calibration():
            Configures calibration settings for EMOD simulations when calibration parameters are enabled.

        update(**kwargs):
            Updates specific attributes of the LoadExperiment instance with new values.

        _assign_attributes(source_obj):
            Copies all attributes from a given source object to the current instance.
    """

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
        self.run_mode_manager.configure(args.run_mode, args.test)
        self._assign_attributes(self.run_mode_manager)

        # Configure EMOD model calibration parameter use if needed,
        if self.emod_calib_params:
            self.configure_emod_calibration()

            
    def configure_emod_calibration(self):
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
