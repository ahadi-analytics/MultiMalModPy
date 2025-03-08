# Software

- **EMOD** (Epidemiological MODeling software) has been developed and is maintained by
the [Institute for Disease Modeling (IDM)](https://www.idmod.org/), and also used by
the [Malaria Modeling Group at Northwestern University](https://www.numalariamodeling.org/).  

-  **OpenMalaria** has been developed and is maintained by
the [Global Disease Modelling team](https://www.thekids.org.au/our-research/early-environment/infection-and-vaccines/global-disease-modelling/) of [The Kids Reseach Institute Australia](https://www.thekids.org.au/), the Disease Modelling Unit of the [Swiss Tropical and Public Health Institute (Swiss TPH)](https://www.swisstph.ch/en/about/eph/disease-modelling/) and [sciCORE](https://scicore.unibas.ch/) of the University of Basel.

-  **malariasimulation** has been developed and is maintained by
the [Imperial College London](https://www.imperial.ac.uk/malaria-modelling/).  

Table: Overview of model software and infrastructure

|                   | EMOD                                                                 | OpenMalaria                                              | malariasimulation                                                                          |
|-------------------|----------------------------------------------------------------------|----------------------------------------------------------|--------------------------------------------------------------------------------------------|
| Documentation     | https://docs.idmod.org/projects/emod-malaria/en/latest/index.html    | https://github.com/SwissTPH/openmalaria/wiki             | https://mrc-ide.github.io/malariasimulation/index.html                                     |
| GitHub            | https://github.com/EMOD-Hub/emodpy-malaria                           | https://github.com/SwissTPH/openmalaria/                 | https://github.com/mrc-ide/malariasimulation                                               |
| Accessibility     | Open source                                                          | Open source                                              | Open source                                                                                |
| Language          | C++                                                                  | C++                                                      | C++/R                                                                                      |
| First published   | 2013                                                                 | 2006-2008                                                | 2010                                                                                       |
| Framework         | Python (emodpy-malaria, idm-tools)                                   | Python or R, varying by user group                       | R >= 4.0.0                                                                                 |                       
| OS                | Windows, Linux                                                       | Windows, Linux, (Mac OS)                                 | Windows, Linux                                                                             |            
| Default timesteps | 1 day                                                                | 5  day                                                   | 1 day                                                                                      |                                                           
| Input file type   | json                                                                 | XML                                                      | R script                                                                                   |                                                       
| Output file type  | json                                                                 | txt                                                      | stored in the R environment                                                                |                                          
| N input files     | 5+                                                                   | 1                                                        | NA                                                                                         |  
| N output files    | custom                                                               | 2                                                        | NA                                                                                         |   
| Glossary          | https://docs.idmod.org/projects/emod-malaria/en/latest/glossary.html | https://github.com/SwissTPH/openmalaria/wiki/Terminology | `help(malariasimulation)`, https://mrc-ide.github.io/malariasimulation/articles/Model.html |  

