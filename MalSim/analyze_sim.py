import os
import argparse
import pickle
import datetime
import time
import pandas as pd
import numpy as np
import sys


sys.path.append('../')
import manifest
from benchmark_plots import *

#TODO ADD FUNCTIONS THAT WILL CONVERT MALSIM VALUES TO APPROPRIATE VALUES
#TO COMPARE TO EMOD AND OPENMALARIA
def parse_args():
    """
    Parses command-line arguments for simulation specifications.
    """
    # Set the description for the argument parser
    description = "Simulation specifications"
    parser = argparse.ArgumentParser(description=description)

    # Add the required argument for the job directory
    parser.add_argument(
        "-o",
        "--output_dir",
        type=str,
        required=True,
        help="Output Directory of exp.obj")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    wdir = args.output_dir
    exp_tags = ['eir', 'cm_clinical', 'seasonality']
      
    emodom = ['MalSim']
    sweepvar = 'eir'
    monthly_trends(wdir, emodom, channel='clinical_incidence', sweepvar=sweepvar)
    #monthly_trends(wdir, emodom, channel='severe_incidence', sweepvar=sweepvar)
    #monthly_trends(wdir, emodom, channel='prevalence', sweepvar=sweepvar)
    #monthly_trends(wdir, emodom, channel='prevalence_2to10', sweepvar=sweepvar)
    # monthly_trends(wdir, emodom=emodom, channel='simulatedEIR', sweepvar=sweepvar)
  
    sweepvar = 'cm_clinical'
    #prevalence2to10_to_incidence(wdir, emodom, channel='prevalence', y_lim=1)
    prevalence2to10_to_incidence(wdir, emodom, channel='clinical_incidence', y_lim=2000)
    prevalence2to10_to_incidence(wdir, emodom, channel='severe_incidence', y_lim=150)
    eir_to_prevalence2to10(wdir, emodom, sweepvar=sweepvar, eir_val='initial_EIR')
    eir_to_prevalence2to10(wdir, emodom, sweepvar=sweepvar, eir_val='initial_EIR')
    #input_to_simulated_eir(wdir, emodom, sweepvar=sweepvar)
