from utility.helper import *
import warnings


class SimulationConfig:
    """
    Configuration class for setting up simulation experiment parameters.

    This class provides a comprehensive structure for configuring various aspects of a malaria simulation experiment,
    including malaria-specific settings, simulation parameters, and framework-related configurations.

    Attributes:
        - **1. Malaria Config**:
            - entomology_mode (str): Mode of entomology setup ('dynamic' by default).
            - seasonality (list[str]): List of seasonality types to simulate (default is ['perennial']).
            - cm_start (int): Start time for case management interventions.
            - case_management (list[tuple]): List of tuples defining case management intervention configurations.
            - detectionLimit (int): Detection threshold for cases.
            - importation_rate (float): Importation rate of malaria cases.
            - target_output_name (str): Type of output metric ('prevalence_2to10' by default).
            - target_output_values (list[float]): List of target output values.
            - sweep_list (list[str]): List of parameters to vary in the simulation.

        - **2. Simulation Config**:
            - agebins (list[float]): List of age bins for simulation grouping.
            - age_groups_aggregates (list[list[float]]): Aggregates of age groups for output metrics.
            - num_seeds_burnin (int): Number of seeds for the burn-in phase.
            - start_year (int): Start year of the simulation.
            - end_year (int): End year of the simulation.
            - emod_burnin (int): Number of burn-in iterations for the EMOD model.
            - emod_pop_size (int): Population size for EMOD simulations.
            - malariasimulation_burnin (int): Burn-in duration for the malariasimulation model.
            - malariasimulation_pop_size (int): Population size for malariasimulation.
            - openmalaria_burnin (int): Burn-in duration for OpenMalaria.
            - openmalaria_pop_size (int): Population size for OpenMalaria.
            - openmalaria_scaffold (str): Scaffold file name for OpenMalaria.
            - openmalaria_survey_step (str): Survey step frequency in OpenMalaria.

        - **3. Framework Config**:
            - mem_increase_factor (float): Factor for increasing memory allocation (default is 5.0).
            - analyzer_script (list[str]): List of analyzer scripts to run.
            - analyzer_list (list[str]): List of analyzers to apply.
            - plots_to_run (list[str]): List of plots to generate during the analysis.
            - burnin_directory (str): Path to the directory containing burn-in data (if any).
    """
    def __init__(self):
        """
        1. Malaria Config
        """
        self.entomology_mode = 'dynamic' # could be forced or dynamic (vector model for EMOD)
        self.seasonality = ['perennial']
        self.cm_start = 1
        self.case_management = [(0, 0),(0.15,0.5)]  # format: [(cm_clinical, cm_severe), (...)]
        self.detectionLimit = 40
        self.emod_importation_rate = 5
        self.openmalaria_importation_rate = 0
        
        # Parameters also modifiable via args (if specified in args, those will get priority)
        # Transmission intensity calibration settings.
        # These settings define the type of output metric and its target values.
        # Note: These will be overwritten if a specific run mode is specified, as run modes may have their own defaults.
        self.target_output_name = 'prevalence_2to10'
        self.target_output_values = [0.25]

        # Interventions to include (intervention specific configurations in interventions/ folder
        self.intervention_list = [] #can be empty or 'ccstep'

        # Parameters to vary
        self.sweep_list = ['target_output_values', 'case_management', 'seasonality']

        """
        2. Simulation Config
        """
        # Age groups and case management settings
        self.agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]
        self.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20, 100],
                                      [0, 5], [0, 100]]
        # self.agebins = [0.5, 1, 2, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85,90,95, 100]
        # self.age_groups_aggregates = [[0, 0.5], [0.5, 1], [1, 2], [2, 5], [5, 10], [10, 15], [15, 20], [20,25], [25,30], [30,35],
        #                            [35,40], [40,45], [45,50], [50,55], [55,60], [60,65], [65,70], [70, 75],
        #                            [75,80], [80,85], [85,90], [90,95], [95,100], [0, 5], [0, 100]]

        self.num_seeds_burnin = 1
        self.num_seeds = 20
        self.start_year = 2000
        self.end_year = 2005
        self.mem_increase_factor = 1.0 #Currently the memory increase factor only effects the analyzers

        # EMOD Settings
        self.emod_burnin = 110
        self.emod_pop_size = 5000
        self.emod_calib_type = 'emod_severe' #could be 'emod_severe' or 'emod_best'
        self.emod_memory_per_sim = 6 #memory is represented in gigabytes allocated for each SLURM job, i.e. 5GB
        self.emod_time_per_sim = '6:00:00' #time is represented in hours:minutes:seconds

        # malariasimulation Settings
        self.malariasimulation_burnin = 100
        self.malariasimulation_pop_size = 50000
        self.malariasimulation_memory_per_sim = 3
        self.malariasimulation_time_per_sim = '3:00:00'


        # OpenMalaria Settings
        self.openmalaria_burnin = 100
        self.openmalaria_pop_size = 50000
        self.openmalaria_scaffold = "R0000GA"
        self.openmalaria_modeloptions = "R0000GA_model_options.txt"
        self.openmalaria_parameter = "R0000GA_parameter.txt"
        self.openmalaria_survey_step = '5d'
        self.openmalaria_memory_per_sim = 3
        self.openmalaria_time_per_sim = '2:00:00'

        """
        3. Framework Config
        """
        self.analyzer_script = ['analyze_sim.py']
        self.analyzer_list = ['timeavrg', 'annual', 'monthly', '5day']  # openmalaria_base, surveyallage
        self.plots_to_run = ['relationship', 'timeseries', 'agecurves']  # 'ccstep'
        self.burnin_directory = None
        self.sim_params_list = ['seasonality', 'sweep_list', 'case_management', 'eir', 'intervention_list', 'agebins',
                                'target_output_values', 'plots_to_run']

