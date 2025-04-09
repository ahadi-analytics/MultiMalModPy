# generate_and_run.ps1

# Step 1: Generate scripts using Docker
docker run -it -v C:\Users\mrung\Documents\MultiMalModPy:/mnt/c/projects/MultiMalModPy mmmpy_local:rocky8 /bin/bash -c "source /opt/envs/mmmpy_container/bin/activate && cd /mnt/c/projects/MultiMalModPy && python launch_sim.py --models OpenMalaria --test"

# Step 2: Run the generated scripts
$simDir = "C:\Users\mrung\Documents\MultiMalModPy\simulations_local\experiments\20250315_TEST\sims_dynamic_perennial_11_36_19"
Set-Location $simDir

# Run the simulation
& "$simDir\jobs_OpenMalaria_simplerun.ps1"

# Wait for completion (you might need to adjust this logic based on how your scripts work)
Start-Sleep -Seconds 60

# Run analysis
& "$simDir\run_analyze_OpenMalaria.ps1"
& "$simDir\plot_relationship.ps1"
& "$simDir\plot_timeseries.ps1"
& "$simDir\plot_agecurves.ps1"