import logging
from functools import partial
from emodpy.emod_task import EMODTask
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment
from datetime import datetime as dt
from idmtools.entities import Suite
import manifest
from EMOD.scaffolds.forcedEIR import *
from EMOD.scaffolds.interventions import treatment_camp
from EMOD.utils import *
from helper import *

log = logging.getLogger(__name__)
loaded_attr = set(dir())
testmode = True
emod_serialize = False
emod_pickup = False
entomology_mode = 'dynamic'  # dynamic, forced
event_recorder = False

om_scaffold = "R0000GA"  # build OpenMalaria XML schema- prerequisite
om_survey_step = '30d'

""" Simulation population and seeds"""
pop_size = 10000
agebins = [0.5, 1, 2, 5, 10, 15, 20, 100]
num_seeds = 3
burnin = 80  # Note burnin handled differently in OpenMalaria and EMOD

""" Model setup """
models_to_run = ['EMOD']  ## 'EMOD','OpenMalaria'
suite = Suite(name=f'explore_{entomology_mode}EIR')  # Collection of simulations, needs to be the same for burnin and pickup simulations
exp_name = f'climateData_noburnin'  # name of the experiment folder

## EMOD burnin
if entomology_mode == 'forced':
    emod_burnin_id = 'c32c30e5-d822-4854-8dd1-ba17f954a892'  ### forced EIR
else:
    emod_burnin_id = '1b5781b0-3d51-4d00-956b-c963fab53046'  ### dynamic EIR

## Name of parameters to vary
sweep_list = ['eir', 'access', 'seasonality'] + ['seed']

if testmode:
    exp_name = f'test_{exp_name}'
    pop_size = 1000
    num_seeds = 3
    burnin = 30

seed = list(range(num_seeds))  ## for scenarios csv

if emod_serialize and 'EMOD' in models_to_run:
    print('Message: Running burnin for EMOD')
    exp_name = f'{exp_name}_burnin{burnin}'
    emod_burnin_id = ''
    models_to_run = ['EMOD']
    sweep_list = ['eir', 'access', 'seasonality', 'seed']
if not emod_pickup:
    emod_burnin_id = None

""" SIMULATION TIME """
start_year = 2000  # start of monitoring period
end_year = 2020  # end of monitoring period
sim_start_year, burnin_start_year, monitoring_years, sim_dur_years = get_time_param(start_year, end_year, burnin,
                                                                                    emod_serialize)

""" INTERVENTIONS """
cm_start = 1  # [1]
access = [0.2029544]  # 5-day probability  ## already converted

""" TRANSMISSION, ENTOMOLOGY """
seasonality = ["seasonal"]  # , "seasonal"
eir = [4, 8, 16, 32]  # [0.1, 1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
season_daily, season_month, seasonal, perennial = get_seasonal_eir()

if entomology_mode == 'dynamic':
    lhs = np.logspace(-2, 3, len(eir))  ## to do funtcion to match eir to LHS
    print(
        'Dynamic EIR has not yet been aligned between EMOD and OpenMalaria, no dynamic seasonal EIR in EMOD yet')  # FIXME

""" DIRECTORIES AND POSTPROCESSING """
job_directory, sim_out_dir = make_dirs(manifest, suite.name, exp_name)
emod_analyzer = ['analyze_sim.py']
openmalaria_analyzer = ['analyze_sim.py']

""" EXPERIMENT ATTRIBUTES AND SCENARIOS """
# Save all defined attibutes into exp class object
my_obj = set(dir()) - loaded_attr
exp = Experiment()
exp.my_obj = my_obj
exp.hpc = manifest.hpc
exp.selected_platform = manifest.selected_platform
exp.om_version = manifest.om_version
exp.emod_build = manifest.emod_build
exp.om_path = manifest.OM_PATH
exp.om_input_path = manifest.om_input_path

for obj_name in my_obj:
    if hasattr(locals().get(obj_name), '__call__'):
        setattr(exp, obj_name, locals().get(obj_name))
    elif obj_name in locals():
        setattr(exp, obj_name, locals().get(obj_name))
    else:
        print(f"Object {obj_name} not found in the locals environment.")

## parameter names to create scenarios from
scen_df = create_scenarios_csv(exp, sweep_list)
exp.nexps = len(scen_df)  # * seeds ## not needed when included in sweep_list
save_exp_scen(exp, scen_df, save_dirs=[exp.job_directory, exp.sim_out_dir])


def set_param_fn(config):
    """
    This function is a callback that is passed to emod-api.config to set config parameters, including the malaria defaults.
    """
    import emodpy_malaria.malaria_config as conf
    config = conf.set_team_defaults(config, manifest)
    config.parameters.x_Base_Population = pop_size / 1000
    config.parameters.Birth_Rate_Dependence = 'FIXED_BIRTH_RATE'
    config.parameters.Maternal_Antibodies_Type = 'CONSTANT_INITIAL_IMMUNITY'
    config.parameters.Simulation_Duration = sim_dur_years * 365

    if entomology_mode == 'dynamic':
        conf.add_species(config, manifest, ["gambiae"])  # , "arabiensis", "funestus"
        ## TO DO enable seasonality sweep via habitat multiplier
        seasonality_type = 'example'
        config.parameters.Air_Temperature_Filename = os.path.join('climate',f'{seasonality_type}_air_temperature_daily.bin')
        config.parameters.Land_Temperature_Filename = os.path.join('climate',f'{seasonality_type}_air_temperature_daily.bin')
        config.parameters.Rainfall_Filename = os.path.join('climate',f'{seasonality_type}_rainfall_daily.bin')
        config.parameters.Relative_Humidity_Filename = os.path.join('climate',f'{seasonality_type}_relative_humidity_daily.bin')

    if emod_serialize:
        config.parameters.Serialized_Population_Writing_Type = "TIMESTEP"
        config.parameters.Serialization_Time_Steps = [sim_dur_years * 365]
        config.parameters.Serialization_Mask_Node_Write = 0
        config.parameters.Serialization_Precision = "REDUCED"
    # Read from burnin
    if emod_burnin_id and not emod_serialize:
        config.parameters.Serialized_Population_Reading_Type = "READ"
        config.parameters.Serialization_Mask_Node_Read = 0
        config.parameters.Serialization_Time_Steps = [burnin * 365]
    return config


##--------------------
def build_campaign(seasonality=None, EIR_scale_factor=None, cm_cov=0.5, cm_clinical_adult=None, cm_severe=None,
                   cm_start=1):
    camp = build_standard_campaign_object(manifest)
    treatment_camp(camp, cm_start=cm_start, cm_clinical_U5=cm_cov)
    if EIR_scale_factor is not None:
        set_inputEIR_seasonality(camp, EIR_scale_factor, seasonality)
    return camp


def update_campaign_multiple_parameters_ser(simulation, df, cm_cov, cm_start, x: int):
    path = df["serialized_file_path"][x]
    seed = int(df["Run_Number"][x])
    if entomology_mode == 'forced':
        eir = float(df["EIR_scale_factor"][x])
        season = float(df["seasonality"][x])
        eir_dic = {"EIR_scale_factor": eir, "seasonality": season}
        build_campaign_partial = partial(build_campaign, seasonality=season, EIR_scale_factor=eir, cm_cov=cm_cov,
                                         cm_start=cm_start)
    else:
        lhs = float(df["x_Temporary_Larval_Habitat"][x])
        eir_dic = {"x_Temporary_Larval_Habitat": lhs, "seasonality": 'perennial'}  ## FIXME, enable seasonality sweep via habitat multiplier
        build_campaign_partial = partial(build_campaign, cm_cov=cm_cov, cm_start=cm_start)
    simulation.task.create_campaign_from_callback(build_campaign_partial)

    if emod_serialize:
        simulation.task.set_parameter("Serialized_Population_Filenames", df["Serialized_Population_Filenames"][x])
        simulation.task.set_parameter('Serialized_Population_Path', os.path.join(path, 'output'))
        simulation.task.set_parameter('Run_Number', seed)

    return {**eir_dic, **{"cm_cov": cm_cov, "Run_Number": seed}}


def update_campaign_multiple_parameters(simulation, cm_cov, cm_start):
    build_camp_partial = partial(build_campaign, cm_cov=cm_cov, cm_start=cm_start)
    rdic = {"cm_clinical_U5": cm_cov, 'cm_start': cm_start}
    simulation.task.create_campaign_from_callback(build_camp_partial)
    return rdic


def update_campaign_multiple_parameters_wEIR(simulation, cm_cov, cm_start, EIR_scale_factor, season):
    update_mab(simulation, mAb_vs_EIR(EIR_scale_factor))  ### eir default = 1
    build_camp_partial = partial(build_campaign, seasonality=season, EIR_scale_factor=EIR_scale_factor, cm_cov=cm_cov,
                                 cm_start=cm_start)
    rdic = {"EIR_scale_factor": EIR_scale_factor, "seasonality": season, "cm_clinical_U5": cm_cov, 'cm_start': cm_start}
    simulation.task.create_campaign_from_callback(build_camp_partial)
    return rdic


##--------------------

def update_eir_scale(simulation, value, svalue):
    build_campaign_partial = partial(build_campaign, EIR_scale_factor=value, seasonality=svalue)
    simulation.task.create_campaign_from_callback(build_campaign_partial)
    return {"EIR_scale_factor": value, "seasonality": svalue}


def sweep_burnin_simulations(simulation, df, x: int, entomology_mode='dynamic'):
    path = df["serialized_file_path"][x]
    seed = int(df["Run_Number"][x])

    simulation.task.config.parameters.Serialized_Population_Path = os.path.join(path, "output")
    simulation.task.config.parameters.Serialized_Population_Filenames = df["Serialized_Population_Filenames"][x]
    simulation.task.config.parameters.Run_Number = seed

    if entomology_mode == 'dynamic':
        simulation.task.config.parameters.x_Temporary_Larval_Habitat = float(df["x_Temporary_Larval_Habitat"][x])
        transm_spec = ['x_Temporary_Larval_Habitat', float(df["x_Temporary_Larval_Habitat"][x])]
    else:
        update_eir_scale(simulation, float(df["EIR_scale_factor"][x]), float(df["seasonality"][x]))
        transm_spec = ['EIR_scale_factor', float(df["EIR_scale_factor"][x])]  ## FIXME

    return {
        "Serialized_Population_Path": os.path.join(df["serialized_file_path"][x], "output"),
        "Serialized_Population_Filenames": df["Serialized_Population_Filenames"][x],
        "Run_Number": seed,
        transm_spec[0]: transm_spec[1]
    }


def submit_create_run_EMOD(exp):
    """
    This function is designed to be a parameterized version of the sequence of things we do
    every time we run an emod experiment.
    """
    selected_platform = exp.selected_platform
    now_str = dt.now().strftime("%Y_%m_%d_%H_%M_%S")
    suite.uid = suite.name
    exp_name = exp.exp_name
    emod_burnin_id = exp.emod_burnin_id

    # Set platform and associated values, such as the maximum number of jobs to run at one time
    platform = Platform(selected_platform, job_directory=os.path.join(manifest.job_directory),
                        partition='normal', time='10:00:00', account='p30781', modules=['singularity'],
                        max_running_jobs=500)  # SUITEname

    # create EMODTask
    print("Creating EMODTask (from files)...")

    task = EMODTask.from_default2(
        config_path="config.json",
        eradication_path=manifest.eradication_path,
        campaign_builder=build_campaign,
        schema_path=manifest.schema_file,
        param_custom_cb=set_param_fn,
        ep4_custom_cb=None,
        demog_builder=build_demog,
        plugin_report=None
    )

    # Set the singularity image to be used when running this experiment
    task.set_sif(manifest.SIF_PATH, platform)
    if entomology_mode =='dynamic':
       task.common_assets.add_directory(os.path.join(manifest.input_dir, "example_weather"), relative_path="climate")

    # Create experiment from builder
    builder = SimulationBuilder()

    # Create burnin df, retrieved from burnin ID (defined above)
    if emod_burnin_id:
        burnin_df = build_burnin_df(emod_burnin_id, platform, burnin * 365)
        builder.add_sweep_definition(partial(sweep_burnin_simulations, df=burnin_df, entomology_mode=entomology_mode),
                                     range(len(burnin_df.index)))

    # builder.add_sweep_definition(update_eir_scale, eir)
    builder.add_sweep_definition(partial(set_param, param='Run_Number'), range(num_seeds))
    if entomology_mode == 'dynamic':
        builder.add_sweep_definition(partial(set_param, param='x_Temporary_Larval_Habitat'), lhs)
        builder.add_multiple_parameter_sweep_definition(update_campaign_multiple_parameters,
                                                        dict(cm_cov=access, cm_start=[1]))
    else:
        builder.add_multiple_parameter_sweep_definition(update_campaign_multiple_parameters_wEIR,
                                                        dict(cm_cov=access, cm_start=[1],
                                                             EIR_scale_factor=eir,
                                                             season=seasonality))

    add_annual_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year, num_year=sim_dur_years)
    if not emod_serialize:
        add_monthly_reports(task, manifest, age_bins=agebins, sim_start_year=sim_start_year, num_year=sim_dur_years)

    # Create experiment from builder and run
    # experiment = Experiment.from_task(task, name=exp_name)
    experiment = Experiment.from_builder(builder, task, name=exp_name)
    # experiment.uid = f'{exp_name}_{now_str}'
    suite.add_experiment(experiment)
    experiment.run(wait_until_done=False, platform=platform)

    # Additional step to schedule analyzer
    experiment.hpc = exp.hpc
    experiment.analyzer = exp.emod_analyzer
    experiment.job_directory = exp.job_directory
    experiment.emod_serialize = exp.emod_serialize
    experiment.start_end = [sim_start_year, sim_start_year + sim_dur_years - 1]
    submit_analyze_EMOD(experiment, platform)

    print(f"Experiment submission {experiment.uid} succeeded.")


if __name__ == '__main__':

    print(
        f'Running simulations for {", ".join(models_to_run)}: {len(sweep_list)} varying parameters: {", ".join(sweep_list)}')

    if 'EMOD' in models_to_run:
        submit_create_run_EMOD(exp)

    if 'OpenMalaria' in models_to_run:
        from OpenMalaria.utils import *

        submit_run_OpenMalaria(exp, scen_df)  ## Includes creating XML files

    # if 'OpenMalaria' and 'EMOD' in models_to_run:
    #    #submit_combine_results(exp)  ## only combined benchmarking.csv, do csvs need to be combined per default?
    #    submit_run_pyscript(exp, pyscript='benchmark_plots.py', shname='run_benchmark_plots.sh', job_id='job_id_EMODanalyze')
