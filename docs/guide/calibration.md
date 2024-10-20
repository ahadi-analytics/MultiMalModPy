# Calibration



The `target_calibration`  directory includes `interpolation_data.csv` for each of the models included in the framework.
The `interpolation_data.csv` data is generated via the transmission calibration, when running via `calib_run` further
described in the User Guide under [Transmission calibration](../guide/calibration.md).

The table below summarizes the results from an epidemiological simulation model,
detailing various metrics related to malaria incidence and prevalence on the example for EMOD.

| input_target | seasonality | cm_clinical | simulatedEIR | prevalence_2to10 | prevalence | severe_incidence | n_total_mos_pop | clinical_incidence | clinical_incidence_U5 | modelname | pop_size | importation |
|--------------|-------------|--------------|--------------|-------------------|------------|-------------------|------------------|---------------------|-----------------------|-----------|----------|-------------|
| 8.44553654   | perennial   | 0.45         | 0.343540425  | 0.020460788       | 0.044149221 | 0.000403342       | 56526.55781      | 0.265060585         | 0.088925115           | EMOD      | 50000    | FALSE       |
| 10.9762974   | perennial   | 0.45         | 0.932994042  | 0.05381089        | 0.106625617 | 0.000708954       | 73407.88671      | 0.636199389         | 0.235184127           | EMOD      | 50000    | FALSE       |
| 14.2654175   | perennial   | 0.45         | 1.710211503  | 0.095421294       | 0.173174509 | 0.000903154       | 95345.36855      | 0.956651654         | 0.423187833           | EMOD      | 50000    | FALSE       |
| 18.5401442   | perennial   | 0.45         | 2.573332919  | 0.138401713       | 0.224445658 | 0.001041937       | 123878.2838      | 1.113905394         | 0.624657857           | EMOD      | 50000    | FALSE       |
| 24.095821    | perennial   | 0.45         | 3.623527973  | 0.185692034       | 0.266564637 | 0001239512        | 160984.3319      | 1.22631187          | 0.853578362           | EMOD      | 50000    | FALSE       |
| 31.316293    | perennial   | 0.45         | 5.016965242  | 0.242720614       | 0.307751194 | 0.001423436       | 209179.4093      | 1.326620187         | 1.145714057           | EMOD      | 50000    | FALSE       |
| 40.7004273   | perennial   | 0.45         | 6.53350783   | 0.295704873       | 0.338061961 | 0.001647561       | 271863.5711      | 1.387121162         | 1.429262657           | EMOD      | 50000    | FALSE       |

**Column Descriptions**

- **input_target**: The transmission target input value for the simulation.
- **seasonality**: The seasonality type, indicating the transmission pattern (e.g., perennial).
- **cm_clinical**: The clinical case management rate.
- **simulatedEIR**: The estimated entomological inoculation rate based on the simulation.
- **prevalence_2to10**: Prevalence of malaria in children aged 2 to 10 years.
- **prevalence**: Overall prevalence of malaria in the population.
- **severe_incidence**: The incidence rate of severe malaria cases.
- **n_total_mos_pop**: Total number of mosquitoes in the population.
- **clinical_incidence**: Overall clinical incidence rate of malaria.
- **clinical_incidence_U5**: Clinical incidence rate of malaria in children under 5 years old.
- **modelname**: The name of the model used in the simulation (e.g., EMOD).
- **pop_size**: The size of the population used in the simulation.
- **importation**: Indicates whether importation of cases is considered (TRUE or FALSE).






