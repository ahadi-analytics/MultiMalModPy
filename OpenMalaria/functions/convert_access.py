# =============================================================================
# function_UncompAccess_5dayProb.R 
#
# R-code function to take fever recall data, eg DHS proportion of malaria fevers 
# treated and convert to 5 day probability of treatment for OpenMalaria.
#
# This code is an example of how MIS and DHS reported treatment of fever proportions 
# can be converted for use in OpenMalaria. Olivier Briet, September 2012. It uses
# data from Crowell et al., submitted in 2012 to PloS ONE.
#
# NOTES:
#  1) Input must be in percentages
#  2) pamd = ProportionAntiMalarialDrugs
#
#  Created by : Olivier Briet and Melissa Penny
#  Originally created : September 2012
#
#  Last modified : 21/11/2013
#			  by : Melissa Penny (melissa.penny@unibas.ch)
# =============================================================================

## version - converted to python

import numpy as np
from scipy.interpolate import UnivariateSpline


def convert_access(pamd):
    """
    This function performs a two-step conversion process to calculate the 5-day treatment probability
    corresponding to a given daily probability of treatment. The process involves:
    1. Interpolating the input value (`pamd`) using data from Crowell et al. (Figure 5a).
    2. Using the interpolated value to convert from a daily treatment probability to a 5-day treatment probability
       using data from Crowell et al. (Figure 7c, black line).

    The conversion process is done using cubic splines (using `UnivariateSpline`).

    Parameters:
    pamd (float): The daily probability of treatment as a percentage (between 0 and 100). This is the input value
                  to convert to a 5-day treatment probability.

    Returns:
    float: The predicted 5-day treatment probability corresponding to the input daily probability (`pamd`).

    Note:
        Currently deprecated since returned values differ from conver_access.R
    """

    # Digitized data from Crowell et al., figure 5a
    pt_x = [0, 0.005427408, 0.01492537, 0.02170963, 0.02985075, 0.04070556, 0.05291723, 0.0651289, 0.08005427,
            0.09497965, 0.1071913, 0.1180461, 0.1275441, 0.1383989, 0.1506106, 0.165536, 0.1804613, 0.1940299,
            0.2075984, 0.2211669, 0.238806, 0.256445, 0.2767978, 0.2957938, 0.3107191, 0.3242877, 0.339213,
            0.3622795, 0.3812754, 0.4029851, 0.431479, 0.4545455, 0.4776119, 0.4993216, 0.5237449, 0.5522388,
            0.5766621, 0.5956581, 0.6200814, 0.6445047, 0.6757123, 0.7001357, 0.7177748, 0.7476255, 0.78019,
            0.807327, 0.8426052, 0.8751696, 0.9104478, 0.9416554, 0.9796472, 0.9986431]

    pt_y = [0.003125, 0.0359375, 0.09375, 0.15, 0.19375, 0.24375, 0.2984375, 0.353125, 0.4078125, 0.4609375,
            0.5015625, 0.5359375, 0.56875, 0.6078125, 0.634375, 0.6546875, 0.6671875, 0.6921875, 0.7203125, 0.74375,
            0.775, 0.7953125, 0.809375, 0.8203125, 0.8328125, 0.853125, 0.8703125, 0.8890625, 0.903125, 0.9140625,
            0.91875, 0.9203125, 0.93125, 0.94375, 0.95625, 0.9640625, 0.9640625, 0.9609375, 0.9671875, 0.9796875,
            0.98125, 0.98125, 0.9875, 0.9921875, 0.99375, 0.99375, 0.9953125, 0.9984375, 1, 1, 1, 1]

    # Data from Crowell et al., figure 7c black line
    probtreat_daily = [0, 0.025, 0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2, 0.225, 0.25, 0.275, 0.3, 0.325, 0.35,
                       0.375, 0.4, 0.425, 0.45, 0.475, 0.5, 0.525, 0.55, 0.575, 0.6, 0.625, 0.65, 0.675, 0.7, 0.725,
                       0.75, 0.775, 0.8, 0.825, 0.85, 0.875, 0.9, 0.925, 0.95, 0.975, 1]
    probtreat_5daily = [0, 0.05880144, 0.1157784, 0.1733548, 0.2299865, 0.2818799, 0.329691, 0.3801282, 0.4195029,
                        0.4652633, 0.5091863, 0.5457407, 0.5781565, 0.6112154, 0.6461608, 0.668167, 0.6951173,
                        0.7227968, 0.74725, 0.7697838, 0.793149, 0.8094841, 0.8234381, 0.8405304, 0.8572314,
                        0.8700262, 0.8853289, 0.8971165, 0.908916, 0.9172805, 0.9278921, 0.9377259, 0.9457713,
                        0.9543433, 0.9645463, 0.9701525, 0.9760008, 0.983826, 0.9891665, 0.9944932, 1]

    # Create the smooth spline for sp.pamd (similar to smooth.spline in R)
    x_data_pamd = np.concatenate((np.zeros(100), pt_y, np.ones(100)))
    y_data_pamd = np.concatenate((np.zeros(100), pt_x, np.ones(100)))
    sp_pamd = UnivariateSpline(x_data_pamd, y_data_pamd, s=0.7)

    # Predict using the spline model (equivalent to predict in R)
    pred_pamd = sp_pamd(pamd / 100)

    # Conversion of daily prob of treatment to 5-daily prob of treatment
    x_data_treatment = np.concatenate((np.zeros(100), probtreat_daily, np.ones(100)))
    y_data_treatment = np.concatenate((np.zeros(100), probtreat_5daily, np.ones(100)))
    sp_onetofivedaily = UnivariateSpline(x_data_treatment, y_data_treatment, s=0.6)

    # Predict the 5-daily probability of treatment based on the previously predicted values
    pred_pamd_5daily = sp_onetofivedaily(pred_pamd)

    # Example usage of the spline, predicting for some x-values (replace 'pamd / 100' from your input)
    pred_pamd = sp_pamd(np.linspace(0, 1, 100))  # Predict over a range of values for demonstration

    return pred_pamd


def convert_access_lookup(pamd):
    """
    Access Lookup function that returns the probability of access based on the input 'pamd'.

    The function uses a dictionary to perform a lookup of the given 'pamd' value and returns the corresponding
    probability of access. The 'pamd' value is used to find the nearest index in the dictionary of ivals and
    pvals, and the corresponding probability value is returned.

    Parameters:
    pamd (float): The input parameter for which the access probability is to be calculated. The value of 'pamd'
                  should be between 0 and 100.

    Returns:
    float: The corresponding 5-day treatment probability based on the input `pamd`.

    Raises:
    ValueError: If the input `pamd` is outside the allowed range (0 to 1, in increments of 0.01).
    """

    probtreat_daily = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
                       21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38,
                       39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
                       57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74,
                       75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92,
                       93, 94, 95, 96, 97, 98, 99, 100]

    probtreat_5daily = [7.934353e-05, 3.655052e-03, 7.259242e-03, 1.089065e-02, 1.454715e-02, 1.821375e-02,
                        2.185895e-02, 2.545025e-02, 2.895516e-02, 3.234127e-02, 3.558067e-02, 3.870637e-02,
                        4.179515e-02, 4.492462e-02, 4.817231e-02, 5.161556e-02, 5.531544e-02, 5.926860e-02,
                        6.345559e-02, 6.785690e-02, 7.245236e-02, 7.721322e-02, 8.210456e-02, 8.709143e-02,
                        9.213899e-02, 9.721381e-02, 1.022998e-01, 1.073931e-01, 1.124904e-01, 1.175883e-01,
                        1.226833e-01, 1.277816e-01, 1.329135e-01, 1.381124e-01, 1.434117e-01, 1.488444e-01,
                        1.544396e-01, 1.601931e-01, 1.660799e-01, 1.720749e-01, 1.781534e-01, 1.842907e-01,
                        1.904703e-01, 1.966911e-01, 2.029544e-01, 2.092610e-01, 2.156120e-01, 2.220045e-01,
                        2.284170e-01, 2.348223e-01, 2.411937e-01, 2.475042e-01, 2.537213e-01, 2.598108e-01,
                        2.657407e-01, 2.715380e-01, 2.773034e-01, 2.831406e-01, 2.891962e-01, 2.957379e-01,
                        3.030474e-01, 3.113960e-01, 3.209671e-01, 3.317720e-01, 3.437782e-01, 3.566707e-01,
                        3.699061e-01, 3.828218e-01, 3.949100e-01, 4.061192e-01, 4.164699e-01, 4.261829e-01,
                        4.355614e-01, 4.448962e-01, 4.544731e-01, 4.645689e-01, 4.754909e-01, 4.875557e-01,
                        5.010331e-01, 5.159051e-01, 5.318855e-01, 5.483645e-01, 5.644357e-01, 5.793443e-01,
                        5.929385e-01, 6.057272e-01, 6.184566e-01, 6.318566e-01, 6.465634e-01, 6.629652e-01,
                        6.812664e-01, 7.013116e-01, 7.223719e-01, 7.436717e-01, 7.665125e-01, 7.933986e-01,
                        8.262853e-01, 8.660768e-01, 9.114032e-01, 9.580364e-01, 9.984184e-01]

    # Create the dictionary mapping daily values to 5-day treatment probabilities
    data_dict = dict(zip(probtreat_daily, probtreat_5daily))

    if pamd in probtreat_daily:
        return data_dict.get(pamd)
    else:
        raise ValueError(
            "cm_clinical outside of OpenMalaria's convert_access lookup range, values must be between 0 and 1 in intervals of 0.01")
