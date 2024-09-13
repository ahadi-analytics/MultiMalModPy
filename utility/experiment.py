import manifest
from utility.helper import *

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
        self.emod_calib_params = args.emod_calib_params
        self.malariasimulation_parameter_variation = args.mpv
        self.output_type = args.output_type

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

        # OpenMalaria and malariasimulation settings
        self.openmalaria_scaffold = "R0000GA"
        self.openmalaria_survey_step = '5d'
        self.malariasimulation_script = 'malariasimulation_base.R'
        self.analyzer_script = ['analyze_sim.py']
        self.analyzer_list = ['all_age_analyzer', 'annual', '5day', 'monthly', 'timeavrg']
        self.plots_to_run = ['relationship', 'timeseries', 'agecurves'] # 'anova_rmse', 'ccstep', 'smc'  ## plot for internal version, cleanup in mmmpy public

        # Entomology settings
        self.entomology_mode = 'dynamic'
        self.seasonality = ['perennial']
        self.mem_increase_factor = 5.0

        # Age groups and case management settings
        self.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]
        self.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5], [0, 100]]
        self.cm_start = 1
        self.cm_clinical = [0, 0.45]
        self.cm_severe = 0.48
        self.detectionLimit = 40
        self.importation_rate = 0
        self.num_seeds_burnin = 1
        self.burnin = 80
        self.start_year = 2000
        self.end_year = 2005

        # Custom settings based on run_mode
        self.configure_run_mode()

        # Parameters to vary
        self.sweep_list = ['output_target', 'cm_clinical', 'seasonality']
        if self.emod_calib_params:
            self.configure_calibration()

    def configure_run_mode(self):
        """
        Configures settings based on the specified run_mode.
        """
        if self.run_mode == 'calibrun':
            if self.output_type != 'eir':
                raise Warning(f"output_type changed to 'eir' as required for calibrun (not {self.output_type})")
            self.output_type = 'eir'
            self.analyzer_list = ['timeavrg']
            self.plots_to_run = ['relationship']
            self.output_target = [0.25, 0.5, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 1.75, 2,
                                 2.5, 2.75, 3, 3.25, 4, 5, 6, 7, 8, 9,
                                 10, 12, 14, 16, 18, 20, 25, 30, 35, 40,
                                 45, 50, 100, 200, 500, 1000]

        elif self.run_mode == 'test':
            self.pop_size = 1000
            self.num_seeds = 1
            self.start_year = 2000
            self.end_year = 2005
            self.burnin = 10

            if self.output_type == 'eir':
                self.output_target = [1, 5, 10, 20, 35, 50]
            elif self.output_type == 'prevalence_2to10':
                self.output_target = [0.05, 0.1, 0.25, 0.4, 0.5, 0.6]

        elif self.run_mode == 'productionrun':
            self.SUITEname = self.SUITEname.replace('test', 'production')
            self.pop_size = 50000
            self.num_seeds = 20
            if self.output_type == 'eir':
                self.output_target = [1, 5, 10, 20, 50, 100, 500, 1000]
            elif self.output_type == 'prevalence_2to10':
                self.output_target = [0.05, 0.1, 0.2, 0.25, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]

        else:  # Default to simulation
            self.SUITEname = self.SUITEname.replace('test', 'sim')
            self.pop_size = 10000
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


def initialize_exp_old(args, manifest):
    """
    Generates the default simulation settings we are interested in using across all three models,
    before any interventions or other functions overwrite the items in exp.
    User, if you want to make adjustments to your simulation and you are not using the overwrite functions,
    I would recommend you make those changes here.

    Example:
        exp.seasonality = get_param(exp_scen_df, 'seasonality', listparam=True)

    Args:
        args (obj, lst): List of inputs grabbed from the parse_args function.
        manifest (file, lst): List of inputs grabbed from the manifest.py file.
            manifest's inputs are more relevant for directories and hpc settings, then simulation settings.
    Returns:
        exp (Experiment): Returns an Experiment Object with simulation and hpc settings that will get shared across
            the three models.
    """
    exp = Experiment()
    exp.SUITEname = args.suite
    exp.exp_name = args.expname
    exp.emod_step = args.emodstep
    exp.models_to_run = args.models
    exp.intervention_list = args.interventions
    exp.run_mode = args.run_mode
    exp.emod_calib_params = args.emod_calib_params  # Whether to pass along NU's Within-Host framework recalibrated parameters, default will be false.
    exp.malariasimulation_parameter_variation = args.mpv
    exp.output_type = args.output_type

    # Name and location of simulation, a SUITE may contain multiple experiments that belong to a shared objective
    exp.user = args.user
    exp.custom_subdir = exp.user  # If None, no subdir created

    ## Manifest objects
    exp.hpc = manifest.hpc
    exp.sh_hpc_config = manifest.sh_hpc_config
    exp.selected_platform = manifest.selected_platform

    exp.emod_build = manifest.emod_build
    exp.emod_input_path = manifest.emod_input_path
    exp.EMOD_venv = manifest.EMOD_venv
    exp.OPENMALARIA_venv = manifest.OPENMALARIA_venv
    exp.openmalaria_path = manifest.OPENMALARIA_PATH
    exp.openmalaria_version = manifest.openmalaria_version
    exp.openmalaria_input_path = manifest.openmalaria_input_path
    exp.malariasimulation_input_path = manifest.malariasimulation_input_path

    exp.job_directory_manifest = manifest.job_directory
    exp.output_directory_manifest = manifest.output_directory
    exp.interp_path = manifest.interp_path
    exp.interp_csv = manifest.interp_csv
    exp.burnin_directory = None

    # Specify OpenMalaria XML and survey step, malariasimulation simulation setup
    # Note if, interventions are specified in intervention_list, these will get updated via get_intervention_params
    exp.openmalaria_scaffold = "R0000GA"  # defining which OpenMalaria XML scaffold to use
    exp.openmalaria_survey_step = '5d'  # '30d'
    exp.malariasimulation_script = 'malariasimulation_base.R'
    exp.analyzer_script = ['analyze_sim.py']
    exp.analyzer_list = ['all_age_analyzer', 'annual', '5day', 'monthly', 'timeavrg']  # ['all_age_analyzer', '5day', 'annual','monthly','timeavrg'.'daily']
    exp.plots_to_run = ['relationship', 'timeseries',  'agecurves']  # gets overwritten by get_intervention_params(exp) depending on 'interventions' specified

    # Flag to select whether to run with (dynamic) or without vector model (forced)
    exp.entomology_mode = 'dynamic'  # dynamic, forced
    exp.seasonality = ['perennial']  # ["perennial", "seasonal"]  #FIXME currently allowing only single seasonal pattern
    #"Current framework support only 1 seasonality patten per experiment"
    exp.mem_increase_factor = 5.0  # scaling factor on default memory requested

    # Define age groups to report/monitor in simulations and to aggregate in output
    exp.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]  # FIXME Note, keep these to ensure smooth postprocessing
    exp.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100], [0, 5],
                                 [0, 100]]

    # Define case management start and coverage
    exp.cm_start = 1
    exp.cm_clinical = [0, 0.45]  # [0, 0.2, 0.4, 0.6, 0.8, 1]  #[0.2029544]
    exp.cm_severe = 0.48  # keep fixed and single value, if < cm_clinical will be updated automatically to cm_clinical * 1.15
    exp.detectionLimit = 40
    exp.importation_rate = 0  # number of infections imported per 1000 population per year, i.e. suggested 0 or 5
    exp.num_seeds_burnin = 1  # used only if emod_step=='burnin' (EMOD specific)

    exp.burnin = 80  # Duration of burnin (pre-monitoring) period, should be 80 years to establish immunity in the population
    exp.start_year = 2000  # start of pickup and monitoring period (for EMOD set given burnin and serialization flags)
    exp.end_year = 2005  # end of pickup and monitoring period


    # FIXME - where is the best place for those custom parameter specifications? -  Specify parameters for test vs normal or production run
    if exp.run_mode =='calibrun':
        if exp.output_type != 'eir':
            raise Warning(f"output_type changed to 'eir' as required for calibrun (not {exp.output_type})")
        exp.output_type = 'eir'
        exp.analyzer_list = ['timeavrg']
        exp.plots_to_run = ['relationship']

        exp.output_target = [0.25, 0.5, 0.75, 0.9, 1, 1.1, 1.25, 1.5, 1.75,2,
                             2.5, 2.75, 3, 3.25, 4, 5, 6, 7, 8, 9,
                             10, 12, 14, 16, 18, 20, 25, 30, 35, 40,
                             45, 50, 100, 200, 500, 1000]

    elif exp.run_mode == 'test':
        exp.pop_size = 1000
        exp.num_seeds = 1
        exp.start_year = 2000
        exp.end_year = 2005
        exp.burnin = 10

        if exp.output_type == 'eir':
            exp.output_target = [1,5,10,20,35,50]
        if exp.output_type == 'prevalence_2to10':
            exp.output_target = [0.05,0.1,0.25,0.4,0.5,0.6]

        #if exp.hpc == 'NUCLUSTER':
        #    exp.sh_hpc_config['p'] = 'b1139testnode'  # Use test allocation
    elif exp.run_mode == 'productionrun':
        exp.SUITEname = exp.SUITEname.replace('test','production')
        exp.pop_size = 50000
        exp.num_seeds = 20
        if exp.output_type == 'eir':
            exp.output_target = [1, 5, 10, 20, 50, 100, 500, 1000]
        if exp.output_type == 'prevalence_2to10':
            exp.output_target = [0.05, 0.1, 0.2, 0.25, 0.4, 0.45, 0.5, 0.6, 0.7, 0.8]
    else:
        exp.SUITEname = exp.SUITEname.replace('test', 'sim')
        exp.pop_size = 10000
        exp.num_seeds = 3  # suggested minimum 3
        if exp.output_type == 'eir':
            exp.output_target = [1, 5, 10, 20, 50, 100, 500, 1000]
        if exp.output_type == 'prevalence_2to10':
            exp.output_target = [0.05,0.1,0.2,0.25,0.4,0.45,0.5,0.6,0.7,0.8]

    # Name of parameters to vary
    exp.sweep_list = ['output_target', 'cm_clinical', 'seasonality']
    if exp.emod_calib_params:
        calib_config_df = pd.read_csv(os.path.join(exp.emod_input_path, 'emod_best.csv'))
        exp.calib_config_pointer = range(0, len(calib_config_df))  # define rows from calib_params df to run
        del calib_config_df
        exp.sweep_list = exp.sweep_list + ['calib_config_pointer']

    return (exp)

