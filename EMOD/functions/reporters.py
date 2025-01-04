from emodpy_malaria.reporters.builtin import *


def add_daily_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                      yr_plusone=True, age_bins=[0.5, 1, 2, 5, 10, 15,20, 125], detection_threshold=0,
                        prefix='Daily_'):
    """
    Adds daily reports to the simulation task.
    Args:
        task: The simulation task object.
        manifest: The manifest object containing the necessary information.
        sim_start_year: The starting year of the simulation.
        num_year: The number of years to add monthly reports for.
        tot_year: The total number of years of the simulation.
                  If None, it is set to num_year.
        age_bins: The age bins for reporting.
        prefix: The prefix to be used for the report filenames.
    Raises:
        ValueError: If num_year is greater than tot_year.
    Returns:
        None
    """
    if tot_year is None:
        tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')

    # Write separate monthly reports for each year
    for year in range(num_year):
        sim_year = tot_year - num_year + year
        start = yr_plusone + 365 * sim_year
        desc = prefix + '%d' % (sim_year + sim_start_year)
        add_malaria_summary_report(task, manifest, start_day=start, end_day=start + 365, age_bins=age_bins,
                                   max_number_reports = 366, reporting_interval=1, filename_suffix=desc, pretty_format=False,
                                   add_true_density_vs_threshold=True, detection_threshold_true_parasite_density = detection_threshold)


def add_5daily_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                        yr_plusone=True, age_bins=[0.5, 1, 2, 5, 10, 15,20, 125], detection_threshold=0,
                        prefix='FiveDaily_'):
    """
    Adds 5 daily reports to the simulation task.
    Args:
        task: The simulation task object.
        manifest: The manifest object containing the necessary information.
        sim_start_year: The starting year of the simulation.
        num_year: The number of years to add monthly reports for.
        tot_year: The total number of years of the simulation.
                  If None, it is set to num_year.
        yr_plusone: Whether to add an extra year to the reporting.
                    If True, reports will cover num_year + 1 years.
                    If False, reports will cover num_year years.
        age_bins: The age bins for reporting.
        prefix: The prefix to be used for the report filenames.
    Raises:
        ValueError: If num_year is greater than tot_year.
    Returns:
        None
    """
    if tot_year is None:
        tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')

    # Write separate monthly reports for each year
    for year in range(num_year):
        sim_year = tot_year - num_year + year
        start = yr_plusone + 365 * sim_year
        desc = prefix + '%d' % (sim_year + sim_start_year)
        add_malaria_summary_report(task, manifest, start_day=start, end_day=start + 365 - 1, age_bins=age_bins,
                                   max_number_reports = 366, reporting_interval=5, filename_suffix=desc, pretty_format=False,
                                   add_true_density_vs_threshold=True, detection_threshold_true_parasite_density = detection_threshold)


def add_monthly_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                        yr_plusone=True, age_bins=[0.5,1, 2, 5, 10, 15,20,125], detection_threshold=0,
                        prefix='Monthly_'):
    """
    Adds monthly reports to the simulation task.
    Args:
        task: The simulation task object.
        manifest: The manifest object containing the necessary information.
        sim_start_year: The starting year of the simulation.
        num_year: The number of years to add monthly reports for.
        tot_year: The total number of years of the simulation.
                  If None, it is set to num_year.
        yr_plusone: Whether to add an extra year to the reporting.
                    If True, reports will cover num_year + 1 years.
                    If False, reports will cover num_year years.
        age_bins: The age bins for reporting.
        prefix: The prefix to be used for the report filenames.
    Raises:
        ValueError: If num_year is greater than tot_year.
    Returns:
        None
    """
    if tot_year is None:
        tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')

    # Write separate monthly reports for each year
    for year in range(num_year):
        sim_year = tot_year - num_year + year
        start = yr_plusone + 365 * sim_year
        desc = prefix + '%d' % (sim_year + sim_start_year)
        add_malaria_summary_report(task, manifest, start_day=start, end_day=start + 365 - 1, age_bins=age_bins,
                                   reporting_interval=30, filename_suffix=desc, pretty_format=False,
                                   add_true_density_vs_threshold=True, detection_threshold_true_parasite_density = detection_threshold)


def add_annual_reports(task, manifest, sim_start_year, num_year, tot_year=None,
                       yr_plusone=True, age_bins=[0.5,1, 2, 5, 10, 15, 20, 125], detection_threshold=0,
                       prefix='Annual_', ipfilter=''):
    """
    Adds annual reports to the simulation task.
    Args:
        task: The simulation task object.
        manifest: The manifest object containing the necessary information.
        sim_start_year: The starting year of the simulation.
        num_year: The number of years to add monthly reports for.
        tot_year: The total number of years of the simulation.
                  If None, it is set to num_year.
        yr_plusone: Whether to add an extra year to the reporting.
                    If True, reports will cover num_year + 1 years.
                    If False, reports will cover num_year years.
        age_bins: The age bins for reporting.
        prefix: The prefix to be used for the report filenames.
    Raises:
        ValueError: If num_year is greater than tot_year.
    Returns:
        None
    """
    if tot_year is None:
        tot_year = num_year
    if (num_year > tot_year):
        raise ValueError('num_year must be <= tot_year')
    sim_year = tot_year - num_year
    start = yr_plusone + 365 * sim_year
    desc = prefix + '%dto%d' % (sim_year + sim_start_year, tot_year + sim_start_year - 1)

    # All years in one report file
    add_malaria_summary_report(task, manifest, start_day=start, end_day=start + (num_year * 365) - 1,
                               age_bins=age_bins, reporting_interval=365, max_number_reports = (tot_year + sim_start_year) - (sim_year + sim_start_year),
                               filename_suffix=desc, pretty_format=False,
                               add_true_density_vs_threshold=True, detection_threshold_true_parasite_density = detection_threshold)
