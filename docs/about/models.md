
# Malaria models 

**EMOD** (Epidemiological MODeling software) has been developed and is maintained by
the [Institute for Disease Modeling (IDM)](https://www.idmod.org/), and also used by
the [Malaria Modeling Group at Northwestern University](https://www.numalariamodeling.org/).

**OpenMalaria** has been developed and is maintained by
the [Swiss Tropical and Public Health Institute (Swiss TPH)](https://www.swisstph.ch/en/about/eph/disease-modelling/).

**malariasimulation** has been developed and is maintained by
the [Imperial College London](https://www.imperial.ac.uk/malaria-modelling/).

Table 1: Overview of model software and infrastructure

|                   | EMOD                                                                                                   | OpenMalaria                                                                         | Malariasimulation                                                                          |
|-------------------|--------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Documentation     | https://docs.idmod.org/projects/emod-malaria/en/latest/index.html                                      | https://github.com/SwissTPH/openmalaria/wiki                                        | https://github.com/mrc-ide/malariasimulation                                               |
| Accessibility     | Open source                                                                                            | Open source                                                                         | Open source (R package)                                                                    |
| Language          | C++                                                                                                    | C++                                                                                 | C++                                                                                        |
| First published   | 2013                                                                                                   | 2006-2008                                                                           |                                                                                            |
| Models            | Individual-based human model <br>Population based vector model  <br> PkPD submodel. <br> Spatial model | Individual-based human model <br>Population based vector model <br> (...) <br> <br> | Individual-based human model <br>Population based vector model <br> (...) <br> <br>        |
| Framework         | Python (emodpy, idm-tools)                                                                             | Python or R, varying by user group                                                  | R >= 4.0.0                                                                                 |                       
| OS                | Windows, Linux                                                                                         | Windows, Linux, (Mac OS)                                                            | Windows, Linux                                                                             |            
| Default timesteps | 1 day                                                                                                  | 5  day                                                                              | 1 day                                                                                      |                                                           
| Input file type   | json                                                                                                   | XML                                                                                 | R script                                                                                   |                                                       
| Output file type  | json                                                                                                   | txt                                                                                 | R script                                                                                   |                                          
| N input files     | 5+                                                                                                     | 1                                                                                   | 1                                                                                          |  
| N output files    | custom                                                                                                 | 2                                                                                   | 1                                                                                          |   
| Glossary          | https://docs.idmod.org/projects/emod-malaria/en/latest/glossary.html                                   | https://github.com/SwissTPH/openmalaria/wiki/Terminology                            | `help(malariasimulation)`, https://mrc-ide.github.io/malariasimulation/articles/Model.html |  

