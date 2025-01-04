# Getting help


## Issues

If you have any issues with using MultiMalModPy, please report them on the repository:

<a href="https://github.com/ahadi-analytics/MultiMalModPy/issues/new"><button class="btn btn-primary btn-lg" type="submit"><i class="fab fa-github fa-2x"></i> Report Issue</button></a>
<a href="https://github.com/ahadi-analytics/MultiMalModPy/issues"><button class="btn btn-primary btn-lg" type="submit"> Active Issues <i class="fab fa-github fa-2x"></i></button></a>


## FAQ  
Coming soon...  


## Troubleshooting 

- No results in simulation outputs
    - analyzer did not run correctly -> try rerunning by submitting corresponding sbatch file, or copy command in
      terminal
        - slurm job id dependency not satisfied
        - error in analyzer script
    - simulation failed -> check log/error files
        - simulations cancelled due to memory or time limit issue
        - simulation had not been submitted due to errors in the input files
    - ...
