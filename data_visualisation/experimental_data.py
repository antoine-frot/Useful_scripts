#!/usr/bin/env python3
"""
Experimental Data for Computational Chemistry Analysis
=======================================================

This module provides experimental data and configurations for computational chemistry
analysis, specifically for absorption and fluorescence properties of various molecules.

The data includes:
- Absorption and fluorescence wavelengths (in nm)
- Experimental oscillator strengths
- Experimental dissymmetry factors (g-factors)

Additionally, the module provides:
- A mapping of molecule names to display-friendly names for tables and plots
- A list of molecules specific to Denis' Boranil-BINOL dataset
"""

import numpy as np
from constants import nm_to_eV

# Configuration
MOLECULES_DATA = [
    {
        "name": "Boranil_CH3+RBINOL_H",
        "absorption_wavelength": 396,   # in nm
        "fluorescence_wavelength": 473, # in nm
        "exp_abs_osc": 42,              # 10^3 M-1 cm-1
        "exp_fluo_osc": "<1\\%",        
        "exp_gabs": -5.5,                # 10-4
        "exp_glum": 0,              # 10-4
    },
    {
        "name": "Boranil_I+RBINOL_H",
        "absorption_wavelength": 401,
        "fluorescence_wavelength": 464,
        "exp_abs_osc": 45,
        "exp_fluo_osc": "<1\\%",
        "exp_gabs": -4.0,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_CF3+RBINOL_H",
        "absorption_wavelength": 401,
        "fluorescence_wavelength": 467,
        "exp_abs_osc": 43,
        "exp_fluo_osc": "<1\\%",
        "exp_gabs": -4.5,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_SMe+RBINOL_H",
        "absorption_wavelength": 402,
        "fluorescence_wavelength": 487,
        "exp_abs_osc": 49,
        "exp_fluo_osc": "<1\\%",
        "exp_gabs": -2.5,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_CN+RBINOL_H",
        "absorption_wavelength": 411,
        "fluorescence_wavelength": 467,
        "exp_abs_osc": 46,
        "exp_fluo_osc": "<1\\%",
        "exp_gabs": -3.5,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_NO2+RBINOL_H",
        "absorption_wavelength": 422,
        "fluorescence_wavelength": 472,
        "exp_abs_osc": 34,
        "exp_fluo_osc": "<1\\%",
        "exp_gabs": -2.0,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_NH2+RBINOL_CN",
        "absorption_wavelength": 406,
        "fluorescence_wavelength": 520,
        "exp_abs_osc": 44,
        "exp_fluo_osc": 0.03,
        "exp_gabs": -7.5,
        "exp_glum": 2.5,
    },
    {                                                                           
        "name": "Boranil_I+RBINOL_CN",                                          
        "absorption_wavelength": 407,                                           
        "fluorescence_wavelength": 464,                                         
        "exp_abs_osc": 41.0,                                                    
        "exp_fluo_osc": 0.14,                                                   
        "exp_gabs": -6.4,                                                        
        "exp_glum": 0,
    },   
    {
        "name": "Boranil_CN+RBINOL_CN",
        "absorption_wavelength": 416,
        "fluorescence_wavelength": 466,
        "exp_abs_osc": 60,
        "exp_fluo_osc": 0.12,
        "exp_gabs": -5.3,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_NO2+RBINOL_CN",
        "absorption_wavelength": 426,
        "fluorescence_wavelength": 479,
        "exp_abs_osc": 50.0,
        "exp_fluo_osc": 0.23,
        "exp_gabs": -3.2,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_CO2H+RBINOL_CN",
        "absorption_wavelength": 412,
        "fluorescence_wavelength": 464,
        "exp_abs_osc": 43.4,
        "exp_fluo_osc": 0.33,
        "exp_gabs": -5.0,
        "exp_glum": 0,
    },
    {
        "name": "BODIPY+F2",
        "absorption_wavelength": np.nan,
        "fluorescence_wavelength": np.nan, 
        "exp_abs_osc": np.nan,
        "exp_fluo_osc": np.nan,
        "exp_gabs": np.nan,
        "exp_glum": np.nan,
    },
    {
        "name": "BODIPY+RBinol_H",
        "absorption_wavelength": 525, # not clearly said on the article
        "fluorescence_wavelength": 570, 
        "exp_abs_osc": 60,
        "exp_fluo_osc": 0.47,
        "exp_gabs": -8.4,
        "exp_glum": 7.0,
    },
    {
        "name": "BODIPY+RBinol_Br", # the value in the diffrent article seems to be very different
        "absorption_wavelength": 527,
        "fluorescence_wavelength": 547, 
        "exp_abs_osc": 74,
        "exp_fluo_osc": 0.69,
        "exp_gabs": -9.0,
        "exp_glum": -6.0,
    },
    {
        "name": "Boranil_NH2+F2",
        "absorption_wavelength": 405,
        "fluorescence_wavelength": 528,
        "exp_abs_osc": 48,
        "exp_fluo_osc": 0.02,
        "exp_gabs": 0,
        "exp_glum": 0,
    },
    {
        "name": "Boranil_NO2+F2",
        "absorption_wavelength": 427,
        "fluorescence_wavelength": 474,
        "exp_abs_osc": 66,
        "exp_fluo_osc": 0.60,
        "exp_gabs": 0,
        "exp_glum": 0,
    },
    {
        "name": "R_BN_CF",
        "absorption_wavelength": 400,
        "fluorescence_wavelength": 495,
        "exp_abs_osc": np.nan,
        "exp_fluo_osc": np.nan,
        "exp_gabs": 7.4,
        "exp_glum": -10.0, # Toluene
    },
    {
        "name": "Helicene_minus_laure_7",
        "absorption_wavelength": 375,
        "fluorescence_wavelength": 440,
        "exp_abs_osc": np.nan,
        "exp_fluo_osc": 0.05,
        "exp_gabs": np.nan,
        "exp_glum": 140,
    },
    {
        "name": "benzothiazole_monofluoroborate_R",
        "absorption_wavelength": 360,
        "fluorescence_wavelength": 530,
        "exp_abs_osc": 31.6,
        "exp_fluo_osc": 0.3, # CH2Cl2
        "exp_gabs": 2.79, # calculated by boris
        "exp_glum": 2,
    },
    {
        "name": "RRhydrindanone",
        "absorption_wavelength": 340,
        "fluorescence_wavelength": 410,
        "exp_abs_osc": 24.0,
        "exp_fluo_osc": 0.001,
        "exp_gabs": np.nan,
        "exp_glum": -350,
    },
    {
        "name": "Helicene6",
        "absorption_wavelength": 324,
        "fluorescence_wavelength": np.nan,
        "exp_abs_osc": 28.3,
        "exp_fluo_osc": np.nan,
        "exp_gabs": 9.2,
        "exp_glum": np.nan,
    },
#    {
#    {
#        "name": "",
#        "absorption_wavelength":,
#        "fluorescence_wavelength":,
#        "exp_abs_osc":,
#        "exp_fluo_osc":,
#        "exp_gabs":, 
#    },
]

# Mapping of original names to display names in plots and tables
MOLECULE_NAME_MAPPING = {
    "Boranil_CH3+RBINOL_H": "CH3+H",
    "Boranil_I+RBINOL_H": "I+H",
    "Boranil_CF3+RBINOL_H": "CF3+H",
    "Boranil_SMe+RBINOL_H": "SMe+H",
    "Boranil_CN+RBINOL_H": "CN+H",
    "Boranil_NO2+RBINOL_H": "NO2+H",
    "Boranil_I+RBINOL_CN": "I+CN",
    "Boranil_NH2+RBINOL_CN": "NH2+CN",
    "Boranil_CN+RBINOL_CN": "CN+CN",
    "Boranil_NO2+RBINOL_CN": "NO2+CN",
    "BODIPY+RBinol_H": "BODIPY+H",
    "BODIPY+RBinol_Br": "BODIPY+Br",
    "Boranil_NH2+F2": "NH2+F2",
    "Boranil_NO2+F2": "NO2+F2",
    "R_BN_CF": "R-BN-CF",
    "Helicene_minus_laure_7": "Helicene laure",
    "benzothiazole_monofluoroborate_R": "Olivier Bore",
    "RRhydrindanone": "Hyndrindanone",
    "Helicene6": "Helicene6"
}

# Boranil-BINOL of Denis
DENIS_MOLECULES = [
    "Boranil_CH3+RBINOL_H",
    "Boranil_I+RBINOL_H",
    "Boranil_CF3+RBINOL_H",
    "Boranil_SMe+RBINOL_H",
    "Boranil_CN+RBINOL_H",
    "Boranil_NO2+RBINOL_H",
    "Boranil_NH2+RBINOL_CN",
    "Boranil_I+RBINOL_CN",
    "Boranil_CN+RBINOL_CN",
    "Boranil_NO2+RBINOL_CN"
]

# Build experimental data dictionary for each molecule
exp_data = {}
for data in MOLECULES_DATA:
    molecule = data["name"]
    exp_data[molecule] = {
        'Absorption': {
            'energy': nm_to_eV / data["absorption_wavelength"],
            'wavelength' : data["absorption_wavelength"],
            'oscillator_strength': data["exp_abs_osc"],
            'dissymmetry_factor': data["exp_gabs"]
        },
        'Fluorescence': {
            'energy': nm_to_eV / data["fluorescence_wavelength"],
            'wavelength' : data["fluorescence_wavelength"],
            'oscillator_strength': data["exp_fluo_osc"],
            'dissymmetry_factor': data["exp_glum"]
        },
        '0-0': (nm_to_eV / data["fluorescence_wavelength"] + nm_to_eV / data["absorption_wavelength"])/2,
    }