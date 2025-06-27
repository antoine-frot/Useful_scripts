#!/usr/bin/env python3
"""
Data Extraction Script for Computational Chemistry Outputs

This script extracts absorption and fluorescence data from quantum chemistry output files.
It then prints two LaTeX tables:
 - A comparison table (with multirow entries for molecule names)
 - A metrics summary table comparing computed energies to experimental values
"""

import os
import argparse
from re import M
from data_visualisation.experimental_data import MOLECULES_DATA, exp_data, MOLECULE_NAME_MAPPING, DENIS_MOLECULES  # Experimental data
from get_properties.electronic_transition_parser import parse_file, get_solvatation_correction # Parsing functions
from data_visualisation.make_plots import generate_plot_experiment_computed, generate_plot_experiment_multiple_computed, generate_plot_computed_multiple_computed
from data_visualisation.latex_table import generate_latex_table, generate_latex_metrics_table
import json

# Methods for ground state optimization
METHODS_OPTIMIZATION_GROUND = ['']

# Methods for excited state optimization
METHODS_OPTIMIZATION_EXCITED = ['',
                                "-OPTES@MO62Xtddft",
                                "-OPTES@wB97X-D3tddft"
                                ]

# Methods for absorption and fluorescence calculations
ALL_FUNCTIONALS = ["B3LYP", "B3LYPtddft", "PBE0", "PBE0tddft", "MO62X", "MO62Xtddft",
                   "CAM-B3LYP", "CAM-B3LYPtddft", "wB97", "wB97X-D3", "wB97X-D3tddft",
                   "B2PLYP", "B2PLYPtddft", "CIS", "CISD", "ADC2_COSMO", "CC2", "CC2_COSMO"]

TDDFT_FUNCTIONALS =["PBE0tddft",
                    "B3LYPtddft",
                    "wB97X-D3tddft",
                    "CAM-B3LYPtddft",
                    "MO62Xtddft",
                    #"B2PLYPtddft"
                    ]

TDADFT_FUNCTIONALS = ["PBE0",
                      "B3LYP",
                      "wB97X-D3",
                      "CAM-B3LYP",
                      "MO62X",
                      "B2PLYP"
                      ]

POSTHF_FUNCTIONALS = [#"CIS", 
                      "CISD", 
                      "ADC2_COSMO", 
                      #"CC2", 
                      "CC2_COSMO"]

ACCURATE_FUNCTIONALS = ["wB97X-D3tddft",
                        "CAM-B3LYPtddft",
                        "MO62Xtddft", 
                        "B2PLYPtddft", 
                        "CISD",
                        "ADC2_COSMO",
                        "CC2_COSMO"]

PRESENTED_FUNCTIONALS = ["B3LYPtddft", "PBE0tddft", "wB97X-D3tddft", "CAM-B3LYPtddft", "MO62Xtddft", "CISD", "B2PLYPtddft", "CC2_COSMO", "ADC2_COSMO"]
HYBRID_FUNCTIONALS = ["B3LYPtddft", "PBE0tddft"]
RS_META_FUNCTIONALS = ["wB97X-D3tddft", "CAM-B3LYPtddft", "MO62Xtddft"]
POSTHF_LIGHT = ["CISD", "B2PLYPtddft"] 
POSTHF_HEAVY = ["CC2_COSMO", "ADC2_COSMO"]

METHODS_LUMINESCENCE_ABS = [f"ABS@{method}" for method in ALL_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_ACCURATE = [f"ABS@{method}" for method in ACCURATE_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_TDDFT = [f"ABS@{method}" for method in TDDFT_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_TDADFT = [f"ABS@{method}" for method in TDADFT_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_POSTHF = [f"ABS@{method}" for method in POSTHF_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_PRESENTED = [f"ABS@{method}" for method in PRESENTED_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_HYBRID = [f"ABS@{method}" for method in HYBRID_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_RS_META = [f"ABS@{method}" for method in RS_META_FUNCTIONALS]
METHODS_LUMINESCENCE_ABS_POSTHF_LIGHT = [f"ABS@{method}" for method in POSTHF_LIGHT]
METHODS_LUMINESCENCE_ABS_POSTHF_HEAVY = [f"ABS@{method}" for method in POSTHF_HEAVY]
METHODS_LUMINESCENCE_ABS_GROUPS = [METHODS_LUMINESCENCE_ABS_HYBRID, METHODS_LUMINESCENCE_ABS_RS_META, METHODS_LUMINESCENCE_ABS_POSTHF_LIGHT, METHODS_LUMINESCENCE_ABS_POSTHF_HEAVY]

METHODS_LUMINESCENCE_FLUO = [f"FLUO@{method}" for method in ALL_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_ACCURATE = [f"FLUO@{method}" for method in ACCURATE_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_TDDFT = [f"FLUO@{method}" for method in TDDFT_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_TDADFT = [f"FLUO@{method}" for method in TDADFT_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_POSTHF = [f"FLUO@{method}" for method in POSTHF_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_PRESENTED = [f"FLUO@{method}" for method in PRESENTED_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_HYBRID = [f"FLUO@{method}" for method in HYBRID_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_RS_META = [f"FLUO@{method}" for method in RS_META_FUNCTIONALS]
METHODS_LUMINESCENCE_FLUO_POSTHF_LIGHT = [f"FLUO@{method}" for method in POSTHF_LIGHT]
METHODS_LUMINESCENCE_FLUO_POSTHF_HEAVY = [f"FLUO@{method}" for method in POSTHF_HEAVY]
METHODS_LUMINESCENCE_FLUO_GROUPS = [METHODS_LUMINESCENCE_FLUO_HYBRID, METHODS_LUMINESCENCE_FLUO_RS_META, METHODS_LUMINESCENCE_FLUO_POSTHF_LIGHT, METHODS_LUMINESCENCE_FLUO_POSTHF_HEAVY]


def main(generate_plots, store_data):
    """Main function to coordinate data collection and LaTeX table generation."""
    warnings_list = [] # Store the warning messages

    json_file = "computed_transitions_data"
    # Data storage structure: molecule -> method -> calculation type -> {energy, wavelength, oscillator}
    dic_abs = {data["name"]: {method_optimization: {method_luminescence: {} for method_luminescence in METHODS_LUMINESCENCE_ABS} for method_optimization in METHODS_OPTIMIZATION_GROUND} for data in MOLECULES_DATA}
    dic_fluo = {data["name"]: {method_optimization: {method_luminescence: {} for method_luminescence in METHODS_LUMINESCENCE_FLUO} for method_optimization in METHODS_OPTIMIZATION_EXCITED} for data in MOLECULES_DATA}
    if store_data:
        # Generate new data if store_data is True
        print("Collecting computational data...")
        for data in MOLECULES_DATA:
            molecule = data["name"]
            abs_solvant_correction = get_solvatation_correction(molecule, "", "ABS@MO62Xtddft", warnings_list)
            for method_optimization in METHODS_OPTIMIZATION_GROUND:
                for method_luminescence in METHODS_LUMINESCENCE_ABS:
                    if method_luminescence == "ABS@CC2":
                        abs_result = parse_file(molecule, method_optimization, method_luminescence, abs_solvant_correction)
                    else: 
                        abs_result = parse_file(molecule, method_optimization, method_luminescence)
                    if abs_result:
                        dic_abs[molecule][method_optimization][method_luminescence] = abs_result
                    else:
                        print(f"⚠️️ No absorbance data found for {molecule} with optimization {method_optimization} and luminescence {method_luminescence}.")
            fluo_solvant_correction = get_solvatation_correction(molecule, "", "FLUO@MO62Xtddft", warnings_list)
            for method_optimization in METHODS_OPTIMIZATION_EXCITED:
                for method_luminescence in METHODS_LUMINESCENCE_FLUO:
                    if method_luminescence == "FLUO@CC2":
                        fluo_result = parse_file(molecule, method_optimization, method_luminescence, fluo_solvant_correction)
                    else:
                        fluo_result = parse_file(molecule, method_optimization, method_luminescence)
                    if fluo_result:
                        dic_fluo[molecule][method_optimization][method_luminescence] = fluo_result
                    else:
                        print(f"⚠️️ No fluorescence data found for {molecule} with optimization {method_optimization} and luminescence {method_luminescence}.")
            with open(f"{json_file}_abs.json", "w") as f:
                json.dump(dic_abs, f)
            with open(f"{json_file}_fluo.json", "w") as f:
                json.dump(dic_fluo, f)
    else:
        # Load data from JSON files if not generating new data
        print("Loading computational data from JSON files...")
        if not os.path.exists(f"{json_file}_abs.json") or not os.path.exists(f"{json_file}_fluo.json"):
            print(f"⚠️️ Data files {json_file}_abs and {json_file}_fluo do not exist. Please add the flag --store_data/-s to generate them.")
        with open(f"{json_file}_abs.json", "r") as f:
            dic_abs = json.load(f)
        with open(f"{json_file}_fluo.json", "r") as f:
            dic_fluo = json.load(f)

    # Remove all .tex file in the output directory
    output_dir = "latex_tables"
    #if not os.path.exists(output_dir):
    #    os.makedirs(output_dir)
    #for f in os.listdir(output_dir):
    #    if f.endswith('.tex'):
    #        os.remove(os.path.join(output_dir, f))
    output_dir_plots = "plot_comparison"
    #if generate_plots:
    #    for f in os.listdir(output_dir_plots):
    #        if f.endswith('.pdf'):
    #            os.remove(os.path.join(output_dir_plots, f))

    METHODS_ABS = {'': METHODS_LUMINESCENCE_ABS, '_ACCURATE': METHODS_LUMINESCENCE_ABS_ACCURATE}
    METHODS_FLUO = {'': METHODS_LUMINESCENCE_FLUO, '_ACCURATE': METHODS_LUMINESCENCE_FLUO_ACCURATE}
    
    # Print LaTeX tables
    for methods_type in ['', '_ACCURATE']:
        abs_luminescence_methods = METHODS_ABS[methods_type]
        fluo_luminescence_methods = METHODS_FLUO[methods_type]
        for luminescence_type in ['Absorption', 'Fluorescence']:
            if luminescence_type == 'Absorption':
                computed_data = dic_abs
                methods_optimization = METHODS_OPTIMIZATION_GROUND
                methods_luminescence = abs_luminescence_methods
            else:
                computed_data = dic_fluo
                methods_optimization = METHODS_OPTIMIZATION_EXCITED
                methods_luminescence = fluo_luminescence_methods
            
            generate_latex_table(exp_data,
                                luminescence_type=luminescence_type,
                                computed_data=computed_data, 
                                methods_optimization=methods_optimization,
                                methods_luminescence=methods_luminescence,
                                gauges=['length'],
                                properties=['energy', 'wavelength', 'oscillator_strength'], 
                                molecule_name_mapping=MOLECULE_NAME_MAPPING, 
                                caption=f"{luminescence_type} data for the studied molecules.", 
                                label=f"{luminescence_type}_{methods_type.lower()}data",
                                output_dir=output_dir,
                                output_filename=f"{luminescence_type}_data{methods_type.lower()}.tex")

            generate_latex_table(exp_data,
                                luminescence_type=luminescence_type,
                                computed_data=computed_data, 
                                methods_optimization=methods_optimization,
                                methods_luminescence=methods_luminescence,
                                gauges=['length', 'velocity'],
                                dissymmetry_variants=['strength'],
                                properties=['energy', 'rotational_strength', 'dipole_strength', 'dissymmetry_factor'], 
                                molecule_name_mapping=MOLECULE_NAME_MAPPING, 
                                caption=f"{luminescence_type} chiroptical (strength) data for the studied molecules.", 
                                label=f"{luminescence_type}_chiroptical_strength{methods_type.lower()}_data",
                                output_dir=output_dir,
                                output_filename=f"{luminescence_type}_chiroptical_strength_data{methods_type.lower()}.tex")

            generate_latex_table(exp_data,
                                luminescence_type=luminescence_type,
                                computed_data=computed_data, 
                                methods_optimization=methods_optimization,
                                methods_luminescence=methods_luminescence,
                                gauges=['length'],
                                dissymmetry_variants=['vector'],
                                properties=['energy', 'D2', 'M2', 'angle_length', 'dissymmetry_factor'], 
                                molecule_name_mapping=MOLECULE_NAME_MAPPING, 
                                caption=f"{luminescence_type} chiroptical (vector,length) data for the studied molecules.", 
                                label=f"{luminescence_type}_chiroptical_vector_length{methods_type.lower()}_data",
                                output_dir=output_dir,
                                output_filename=f"{luminescence_type}_chiroptical_vector_length_data{methods_type.lower()}.tex")

            generate_latex_table(exp_data,
                                luminescence_type=luminescence_type,
                                computed_data=computed_data, 
                                methods_optimization=methods_optimization,
                                methods_luminescence=methods_luminescence,
                                gauges=['velocity'],
                                dissymmetry_variants=['vector'],
                                properties=['energy', 'P2', 'M2', 'angle_velocity', 'dissymmetry_factor'], 
                                molecule_name_mapping=MOLECULE_NAME_MAPPING, 
                                caption=f"{luminescence_type} chiroptical (vector, velocity) data for the studied molecules.", 
                                label=f"{luminescence_type}_chiroptical_vector_velocity{methods_type.lower()}_data",
                                output_dir=output_dir,
                                output_filename=f"{luminescence_type}_chiroptical_vector_velocity_data{methods_type.lower()}.tex")

            for prop in ['energy', 'dissymmetry_factor']:
                gauges = ['length', 'velocity'] if prop == 'dissymmetry_factor' else [None]
                dissymmetry_variants = ['strength', 'vector'] if prop == 'dissymmetry_factor' else [None]
                for gauge in gauges:
                    for dissymmetry_variant in dissymmetry_variants:
                        if gauge is None and dissymmetry_variant is None:
                            output_filename = f"{luminescence_type}_{prop}{methods_type.lower()}_metric.tex"
                            caption = f"{luminescence_type} {' '.join(prop.split('_'))} data."
                            label = f"{luminescence_type}_{prop}{methods_type.lower()}_metric"
                        else:
                            output_filename = f"{luminescence_type}_{prop}_{gauge}_{dissymmetry_variant}{methods_type.lower()}_metric.tex"
                            caption = f"{luminescence_type} {' '.join(prop.split('_'))} data ({gauge}, {dissymmetry_variant})."
                            label = f"{luminescence_type}_{prop}_{gauge}_{dissymmetry_variant}{methods_type.lower()}_metric"
                        generate_latex_metrics_table(exp_data=exp_data,
                                                    luminescence_type=luminescence_type,
                                                    computed_data=computed_data,
                                                    methods_optimization=methods_optimization,
                                                    methods_luminescence=methods_luminescence,
                                                    gauge=gauge,
                                                    dissymmetry_variant=dissymmetry_variant,
                                                    prop=prop,
                                                    molecules=DENIS_MOLECULES,
                                                    output_filename=output_filename,
                                                    output_dir=output_dir,
                                                    caption=caption,
                                                    label=label,
                                                    warnings_list=warnings_list)
                        
    if generate_plots: 
        print("Generating plots...")
        for luminescence_type in ['Absorption', 'Fluorescence']:
            if luminescence_type == 'Absorption':
                computed_data = dic_abs
                methods_optimization = METHODS_OPTIMIZATION_GROUND
                methods_luminescence = METHODS_LUMINESCENCE_ABS_PRESENTED
            else:
                computed_data = dic_fluo
                methods_optimization = METHODS_OPTIMIZATION_EXCITED
                methods_luminescence = METHODS_LUMINESCENCE_FLUO_PRESENTED
            for prop in ['energy', 'dissymmetry_factor']:
                gauges = ['length', 'velocity'] if prop == 'dissymmetry_factor' else [None]
                dissymmetry_variants = ['strength', 'vector'] if prop == 'dissymmetry_factor' else [None]
                for gauge in gauges:
                    for dissymmetry_variant in dissymmetry_variants:
                        generate_plot_experiment_computed(exp_data=exp_data,
                                                    luminescence_type=luminescence_type,
                                                    computed_data=computed_data,
                                                    methods_optimization=methods_optimization,
                                                    methods_luminescence=methods_luminescence,
                                                    gauge=gauge,
                                                    dissymmetry_variant=dissymmetry_variant,
                                                    prop=prop,
                                                    molecules=DENIS_MOLECULES,
                                                    output_dir=output_dir_plots,
                                                    )
                        for method_optimization in methods_optimization:
                            generate_plot_experiment_multiple_computed(exp_data=exp_data,
                                                            luminescence_type=luminescence_type,
                                                            computed_data=computed_data,
                                                            methods_optimization=[method_optimization],
                                                            methods_luminescence=methods_luminescence,
                                                            gauge=gauge,
                                                            dissymmetry_variant=dissymmetry_variant,
                                                            prop=prop,
                                                            molecules=DENIS_MOLECULES,
                                                            output_dir=output_dir_plots,
                                                            )
                            methods_luminescence_groups = METHODS_LUMINESCENCE_ABS_GROUPS if luminescence_type == 'Absorption' else METHODS_LUMINESCENCE_FLUO_GROUPS
                            for methods_luminescence in methods_luminescence_groups:
                                generate_plot_experiment_multiple_computed(exp_data=exp_data,
                                                                luminescence_type=luminescence_type,
                                                                computed_data=computed_data,
                                                                methods_optimization=[method_optimization],
                                                                methods_luminescence=methods_luminescence,
                                                                gauge=gauge,
                                                                dissymmetry_variant=dissymmetry_variant,
                                                                prop=prop,
                                                                molecules=DENIS_MOLECULES,
                                                                output_dir=output_dir_plots,
                                                                output_filebasename="_".join(methods_luminescence).replace("'",'').replace('[','').replace(']','')
                                                                )

        generate_plot_computed_multiple_computed(main_method_optimization="",
                                                main_method_luminescence="ABS@CC2_COSMO",
                                                luminescence_type='Absorption',
                                                computed_data=dic_abs,
                                                methods_optimization=[""],
                                                methods_luminescence=METHODS_LUMINESCENCE_ABS_PRESENTED,
                                                prop='energy',
                                                molecules=DENIS_MOLECULES,
                                                output_dir=output_dir_plots,
                                                output_filebasename="CC2_ref")

        generate_plot_computed_multiple_computed(main_method_optimization="",
                                                main_method_luminescence="FLUO@CC2_COSMO",
                                                luminescence_type='Fluorescence',
                                                computed_data=dic_fluo,
                                                methods_optimization=[""],
                                                methods_luminescence=METHODS_LUMINESCENCE_FLUO_PRESENTED,
                                                prop='energy',
                                                molecules=DENIS_MOLECULES,
                                                output_dir=output_dir_plots,
                                                output_filebasename="CC2_ref")
        
    all_tables = "all_tables.tex"
    tex_files = sorted(f for f in os.listdir(output_dir) if f.endswith('.tex') and f != all_tables)
    with open(os.path.join(output_dir, all_tables), 'w') as outfile:
        for fname in tex_files:
            filepath = os.path.join(output_dir, fname)
            outfile.write(f"\\input{{{filepath}}}\n")
            outfile.write("\\newpage\n")
    print(f"All tables have been compiled into {all_tables}.")

    # Print unique warning messages
    seen_warnings = set()
    for warning in warnings_list:
        if warning not in seen_warnings:
            print(warning)
            seen_warnings.add(warning)
    #generate_comparison_plots()
    #print(f"Plots done")

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Generate LaTeX tables and optionally plots for computational chemistry data.")
    parser.add_argument("--plots", "-p", action="store_true", default=False, help="Generate plots alongside LaTeX tables.")
    parser.add_argument("--store_data", "-s", action="store_true", default=False, help="Store collected data in JSON files.")
    args = parser.parse_args()
    main(generate_plots=args.plots, store_data=args.store_data)
    print("Done.")
