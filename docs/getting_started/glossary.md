# Glossary


**Burnin-in**  
&nbsp;&nbsp;&nbsp;&nbsp;  A time period used to warm up the model, reaching equilibrium or initializing population immunity or the vector model. 
Outputs are typically not monitored during this phase, and handling varies across models.

**experiment ID**  
&nbsp;&nbsp;&nbsp;&nbsp;  A unique identifier assigned to each simulation in EMOD.

**Entomological mode**  
&nbsp;&nbsp;&nbsp;&nbsp; Specifies the vector model to use, determining whether the simulation employs forced or dynamic 
<span title="A measure of the number of infectious mosquito bites received by an individual in a specific area over a given period" style="color: #007BFF; text-decoration: underline; cursor: pointer;">EIR (Entomological Inoculation Rate)</span>.

**manifest**  
&nbsp;&nbsp;&nbsp;&nbsp;  The Python script where user-specific configurations, such as paths and installed software versions, are defined (term adopted from IDMTools).

**Monitoring period**  
&nbsp;&nbsp;&nbsp;&nbsp;  Period of the simulation during which transmission dynamics and disease states are tracked and recorded in the output.


**MultiMalModPy**  
 Multi-Malaria-Modeling Framework


**Pickup** 
&nbsp;&nbsp;&nbsp;&nbsp;  A phase where the simulation "picks up" from a previously saved state, referred to as serialization,
which captures the system's state after the burn-in period. This allows the simulation to continue from that point without 
needing to repeat the burn-in. The state is saved in the form of serialized files that can be used in subsequent runs.
Simulation outcomes are typically monitored from this phase onward.

**scen_df / scenario csv**  
&nbsp;&nbsp;&nbsp;&nbsp;  A CSV file containing all unique parameter combinations for a simulation scenario. Generated in `launch_sim.py`.

**serialization**  
&nbsp;&nbsp;&nbsp;&nbsp;  Saves the population state at a specific time, allowing simulations to start from that point instead of re-running the burn-in period.

**Sweeps**  
&nbsp;&nbsp;&nbsp;&nbsp;  The sweep defines all combinations of parameter values to simulate every possible scenario.

**Target output**  
&nbsp;&nbsp;&nbsp;&nbsp; Target output name and values refer to the outcome metrics used to adjust and set the transmission intensity in the simulation.

**Transmission intensity**  
&nbsp;&nbsp;&nbsp;&nbsp; Malaria transmission intensity can be expressed by entomological inoculation rate or a temporal larval habitat multiplier (EMOD only).






