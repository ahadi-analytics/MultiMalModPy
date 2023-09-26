# Requirements for Running MalSim R Scripts
_[malariasimulation](https://github.com/mrc-ide/malariasimulation/tree/master)_  

_Disclaimer: This repository is under active development, if something is not working, please contact us - or simply create an issue on GitHub that we can follow up on._

------------------------------------- 
The following packages are required to run the RScripts MalSim is dependent on. Make sure that you install these packages to the version of RStudio you are running in your hpc cluster. 
For Example, I (Ricky) opened up RStudio in Quest Analytics and then downloaded the following packages directly in the console using the install.packages("<package_name>") command.
Reminder malariasimulation is only compatible with R >= 4.0.0
If you have any questions please reach out.

malariasimulation
malariaEquilibrium
tidyverse
argparser
ggplot2
base
utils
tictoc

_Table: MalSim functions_

| MS/utils.py                  | MS/scaffolds               | MS/analyze_sim.py                          |
|------------------------------|----------------------------|--------------------------------------------|
| submit_create_run_MS         | ...                        | ...                                        |
|                              |                            |                                            |
|                              |                            |                                            |

Note: MS/scaffolds and MS/analyze_sim.py are currently emptpy and or not used as we are currently aiming to build all necessary functionality directly into the Rscript `malsim_csv_input_function_example.R`
which the function submit_create_run_MS in MS/utils.py calls on. Utils, scaffolds, and analyze_sim.py will become more fleshed out as it is deemed necessary.
