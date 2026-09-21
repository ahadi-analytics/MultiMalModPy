# Software

- **EMOD** (Epidemiological MODeling software) has been developed and is maintained by
  the [Institute for Disease Modeling (IDM)](https://www.idmod.org/), and also used by
  the [Malaria Modeling Group at Northwestern University](https://www.numalariamodeling.org/).

- **OpenMalaria** has been developed and is maintained by
  the [Global Disease Modelling team](https://www.thekids.org.au/our-research/early-environment/infection-and-vaccines/global-disease-modelling/)
  of [The Kids Reseach Institute Australia](https://www.thekids.org.au/), the Disease Modelling Unit of
  the [Swiss Tropical and Public Health Institute (Swiss TPH)](https://www.swisstph.ch/en/about/eph/disease-modelling/)
  and [sciCORE](https://scicore.unibas.ch/) of the University of Basel.

- **malariasimulation** has been developed and is maintained by
  the [Imperial College London](https://www.imperial.ac.uk/malaria-modelling/).

Table: Overview of model software and infrastructure

|                   | EMOD                                                                    			      | malariasimulation                                                                                            | OpenMalaria                                                              |                                  
|-------------------|----------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|				
| Documentation     | [idmod.org/tool/<br/>emod-malaria](https://emod.idmod.org/emodpy-malaria/) 			     | [mrc-ide.github.io/<br/>malariasimulation](https://mrc-ide.github.io/malariasimulation/index.html)               | [SwissTPH/<br/>openmalaria/wiki](https://github.com/SwissTPH/openmalaria/wiki) |						
| GitHub            | [EMOD-Hub/<br/>emodpy-malaria](https://github.com/EMOD-Hub/emodpy-malaria  ) 			     | [mrc-ide/<br/>malariasimulation](https://github.com/mrc-ide/malariasimulation)                                   | [SwissTPH/<br/>openmalaria/ ](https://github.com/SwissTPH/openmalaria/ )  	   |	     
| Accessibility     | Open source                                                             			      | Open source                                                                                                  | Open source                                                		            |  
| Language          | C++                                                                     			      | C++/R                                                                                                        | C++                                                                      |
| First published   | 2013                                                                    			      | 2010                                                                                                         | 2006-2008                                                                |
| Framework         | Python <br/>(emodpy-malaria,<br/> idmtools)                                      			      | R >= 4.0.0                                                                                                   | Python or R,<br/> varying by user                                        |                     
| OS                | Windows, <br/>Linux                                                          			     | Windows, <br/>Linux                                                                                              | Windows, <br/>Linux, <br/>(Mac OS)                                                 |          
| Default timesteps | 1 day                                                                   			      | 1 day                                                                                                        | 5  day                                                                   |                                                        
| Input file type   | json                                                                    			      | R script                                                                                                     | XML                                                                      |                                                   
| Output file type  | json                                                                    			      | stored in <br/>the R environment                                                                                 | txt                                                                      |                                     
| N input files     | 5+                                                                      			      | NA                                                                                                           | 1                                                                        |
| N output files    | custom                                                                  			      | NA                                                                                                           | 2                                                                        |
| Glossary          | [glossary](https://emod.idmod.org/emodpy-malaria/glossary/) | `help(malariasimulation)`<br/> [articles/Model](https://mrc-ide.github.io/malariasimulation/articles/Model.html) | [Terminology](https://github.com/SwissTPH/openmalaria/wiki/Terminology)  |   

