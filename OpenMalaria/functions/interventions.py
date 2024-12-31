

# Currently SMC is not supported

# def write_smc_deployment(scenario, row):
#     # smc_start, smc_end, smc_months=None, smc_day=1
#     """
#     Updates a scenario template with seasonal malaria chemoprevention (SMC) deployment details.
#
#     This function replaces placeholder values in a scenario template with specific dates
#     and coverage levels for SMC interventions. The replacements depend on the `eir`
#     (entomological inoculation rate) value in the provided row. The function handles
#     predefined `eir` values (e.g., 4, 8, 32) and maps them to specific SMC deployment
#     schedules.
#
#     Args:
#         scenario (str): A template string representing the scenario configuration,
#             containing placeholders (e.g., `@smc_1_1@`, `@smc_coverage@`) to be replaced
#             with specific values.
#         row (pd.Series): A Pandas Series object containing:
#             - `eir` (int): The entomological inoculation rate, which determines the SMC schedule.
#             - `smc_coverage` (float): The coverage level for SMC interventions.
#
#     Returns:
#         str: The updated scenario string with placeholders replaced by specific dates
#         and the `smc_coverage` value.
#
#     Raises:
#         KeyError: If `eir` or `smc_coverage` is missing in the input row.
#
#     Notes:
#         - The function supports specific `eir` values (4, 8, and 32). If the `eir` value
#           is not among these, the placeholders will remain unchanged.
#         - Placeholders such as `@smc_1_1@`, `@smc_1_2@`, ..., `@smc_5_4@` represent dates for
#           SMC rounds, while `@smc_coverage@` represents the coverage value.
#
#     """
#     if int(row['eir']) == 4:
#         scenario = scenario.replace('@smc_1_1@', '2001-01-01')
#         scenario = scenario.replace('@smc_1_2@', '2001-02-01')
#         scenario = scenario.replace('@smc_1_3@', '2001-03-01')
#         scenario = scenario.replace('@smc_1_4@', '2001-04-01')
#         scenario = scenario.replace('@smc_2_1@', '2002-01-01')
#         scenario = scenario.replace('@smc_2_2@', '2002-02-01')
#         scenario = scenario.replace('@smc_2_3@', '2002-03-01')
#         scenario = scenario.replace('@smc_2_4@', '2002-04-01')
#         scenario = scenario.replace('@smc_3_1@', '2003-01-01')
#         scenario = scenario.replace('@smc_3_2@', '2003-02-01')
#         scenario = scenario.replace('@smc_3_3@', '2003-03-01')
#         scenario = scenario.replace('@smc_3_4@', '2003-04-01')
#         scenario = scenario.replace('@smc_4_1@', '2004-01-01')
#         scenario = scenario.replace('@smc_4_2@', '2004-02-01')
#         scenario = scenario.replace('@smc_4_3@', '2004-03-01')
#         scenario = scenario.replace('@smc_4_4@', '2004-04-01')
#         scenario = scenario.replace('@smc_5_1@', '2005-01-01')
#         scenario = scenario.replace('@smc_5_2@', '2005-02-01')
#         scenario = scenario.replace('@smc_5_3@', '2005-03-01')
#         scenario = scenario.replace('@smc_5_4@', '2005-04-01')
#     if int(row['eir']) == 8:
#         scenario = scenario.replace('@smc_1_1@', '2001-01-01')
#         scenario = scenario.replace('@smc_1_2@', '2001-02-01')
#         scenario = scenario.replace('@smc_1_3@', '2001-03-01')
#         scenario = scenario.replace('@smc_1_4@', '2001-04-01')
#         scenario = scenario.replace('@smc_2_1@', '2002-01-01')
#         scenario = scenario.replace('@smc_2_2@', '2002-02-01')
#         scenario = scenario.replace('@smc_2_3@', '2002-03-01')
#         scenario = scenario.replace('@smc_2_4@', '2002-04-01')
#         scenario = scenario.replace('@smc_3_1@', '2003-01-01')
#         scenario = scenario.replace('@smc_3_2@', '2003-02-01')
#         scenario = scenario.replace('@smc_3_3@', '2003-03-01')
#         scenario = scenario.replace('@smc_3_4@', '2003-04-01')
#         scenario = scenario.replace('@smc_4_1@', '2004-01-01')
#         scenario = scenario.replace('@smc_4_2@', '2004-02-01')
#         scenario = scenario.replace('@smc_4_3@', '2004-03-01')
#         scenario = scenario.replace('@smc_4_4@', '2004-04-01')
#         scenario = scenario.replace('@smc_5_1@', '2005-01-01')
#         scenario = scenario.replace('@smc_5_2@', '2005-02-01')
#         scenario = scenario.replace('@smc_5_3@', '2005-03-01')
#         scenario = scenario.replace('@smc_5_4@', '2005-04-01')
#     if int(row['eir']) == 32:
#         scenario = scenario.replace('@smc_1_1@', '2000-12-01')
#         scenario = scenario.replace('@smc_1_2@', '2001-01-01')
#         scenario = scenario.replace('@smc_1_3@', '2001-02-01')
#         scenario = scenario.replace('@smc_1_4@', '2001-03-01')
#         scenario = scenario.replace('@smc_2_1@', '2001-12-01')
#         scenario = scenario.replace('@smc_2_2@', '2002-01-01')
#         scenario = scenario.replace('@smc_2_3@', '2002-02-01')
#         scenario = scenario.replace('@smc_2_4@', '2002-03-01')
#         scenario = scenario.replace('@smc_3_1@', '2002-12-01')
#         scenario = scenario.replace('@smc_3_2@', '2003-01-01')
#         scenario = scenario.replace('@smc_3_3@', '2003-02-01')
#         scenario = scenario.replace('@smc_3_4@', '2003-03-01')
#         scenario = scenario.replace('@smc_4_1@', '2003-12-01')
#         scenario = scenario.replace('@smc_4_2@', '2004-01-01')
#         scenario = scenario.replace('@smc_4_3@', '2004-02-01')
#         scenario = scenario.replace('@smc_4_4@', '2004-03-01')
#         scenario = scenario.replace('@smc_5_1@', '2004-12-01')
#         scenario = scenario.replace('@smc_5_2@', '2005-01-01')
#         scenario = scenario.replace('@smc_5_3@', '2005-02-01')
#         scenario = scenario.replace('@smc_5_4@', '2005-03-01')
#     scenario = scenario.replace('@smc_coverage@', str(row['smc_coverage']))
#     return scenario