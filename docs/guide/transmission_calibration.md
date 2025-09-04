# Defining transmission intensity 
_Implementation in MultiMalModPy_

<div style="background-color: #f4f4f4; padding: 12px; border-left: 5px solid #FF6B8B; border-radius: 5px; margin: 10px 0;">
    <strong>🔍 Tip:</strong> For a detailed overview of how each model handles transmission intensity, refer to the 
    <a href="https://ahadi-analytics.github.io/MultiMalModPy/malaria_models/structure/#transmission-intensity" 
       style="color: #0073e6; text-decoration: none;">
        Transmission Intensity
    </a> section under malaria models.
</div>



In MultiMalModPy, the user can specify the level of transmission via the following two parameters in [setup_sim.py](https://github.com/ahadi-analytics/MultiMalModPy/blob/main/setup_sim.py#L62): 
- `target_output_name`    – Defines the epidemiological metric used for calibration.  
- `target_output_values`    – Specifies the target values for the selected metric.  


Example: 
``` 
target_output_name = 'prevalence_2to10'
target_output_values = [0.25]
```
In this example, the simulation is calibrated to achieve a 2-to-10-year-old malaria prevalence of 25% (0.25).  


### Matching defined transmission output targets 


The `target_calibration`  directory includes `interpolation_data.csv` for each of the models included in the framework.
This file is generated during the transmission calibration process when running: 

```
python launch_sim.py -r calibrun  
```

The table below provides an example of calibration results for EMOD, showing key epidemiological metrics related to malaria transmission.  

| input_target | seasonality | cm_clinical | simulatedEIR | prevalence_2to10 | prevalence | severe_incidence | n_total_mos_pop | clinical_incidence | clinical_incidence_U5 | models | pop_size | importation |
|--------------|-------------|--------------|--------------|-------------------|------------|-------------------|------------------|---------------------|-----------------------|--------|----------|-------------|
| 8.44553654   | perennial   | 0.45         | 0.343540425  | 0.020460788       | 0.044149221 | 0.000403342       | 56526.55781      | 0.265060585         | 0.088925115           | EMOD   | 50000    | FALSE       |
| 10.9762974   | perennial   | 0.45         | 0.932994042  | 0.05381089        | 0.106625617 | 0.000708954       | 73407.88671      | 0.636199389         | 0.235184127           | EMOD   | 50000    | FALSE       |
| 14.2654175   | perennial   | 0.45         | 1.710211503  | 0.095421294       | 0.173174509 | 0.000903154       | 95345.36855      | 0.956651654         | 0.423187833           | EMOD   | 50000    | FALSE       |
| 18.5401442   | perennial   | 0.45         | 2.573332919  | 0.138401713       | 0.224445658 | 0.001041937       | 123878.2838      | 1.113905394         | 0.624657857           | EMOD   | 50000    | FALSE       |
| 24.095821    | perennial   | 0.45         | 3.623527973  | 0.185692034       | 0.266564637 | 0001239512        | 160984.3319      | 1.22631187          | 0.853578362           | EMOD   | 50000    | FALSE       |
| 31.316293    | perennial   | 0.45         | 5.016965242  | 0.242720614       | 0.307751194 | 0.001423436       | 209179.4093      | 1.326620187         | 1.145714057           | EMOD   | 50000    | FALSE       |
| 40.7004273   | perennial   | 0.45         | 6.53350783   | 0.295704873       | 0.338061961 | 0.001647561       | 271863.5711      | 1.387121162         | 1.429262657           | EMOD   | 50000    | FALSE       |

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
- **models**: The name of the model used in the simulation (e.g., EMOD).
- **pop_size**: The size of the population used in the simulation.
- **importation**: Indicates whether importation of cases is considered (TRUE or FALSE).



### Defining your own transmission target

If you need to run simulations beyond the predefined datasets, follow this process:  

```
python launch_sim.py -r calibrun
```

By default, this runs all three models with the settings specified in setup_sim.py.  
Key parameters to configure include:  
- Population size (pop_size)  
-  Burn-in duration 
-  Seasonal profiles 
-  Case management levels 

Once the simulations complete, new `.csv` files will be generated in the `target_calibration` folder for each model.
These files are named after your most recent calibration run. 

You should review and decide whether to integrate them into your `interpolation_data.csv` files.    

#### Special Considerations for OpenMala

<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>📝 OpenMalaria Consideration:</em></strong> 
  It is recommended to discard OpenMalaria simulation outputs where the annual *Pf*PR (_Plasmodium falciparum_ prevalence in ages 2-10) exceeds 0.7, 
  as these can not be reliably simulated using OpenMalaria.
</div>  


<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>📝 EMOD Consideration 1:</em></strong> 
If your calibration simulations for EMOD did not include importation, check whether any lower xtemp simulations resulted in malaria elimination.
To do this, open the relevant simulation_outputs/EMOD/mmmpy_yr.csv file and look for cases where simulatedEIR equals 0, indicating elimination.
</div>  

<div style="background-color: #E9F2F9;  padding: 10px; border-left: 5px solid #00796b; margin: 10px 0;">
  <strong><em>📝 EMOD Consideration 2:</em></strong>
If even one of the simulations you ran resulted in elimination, remove that xtemp value from interpolation_data.csv, as it cannot reliably sustain malaria transmission. 
If the lowest level of malaria EMOD can sustain does not meet your expectations, consider adjusting the max_larval_capacity values in the habitat_setup function (EMOD/functions/EMOD_functions.py).
</div>  


### Finalizing and Running Production Simulations
Once you have finalized your `interpolation_data.csv` files, you can proceed with running production simulations.





