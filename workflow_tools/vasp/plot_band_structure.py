import numpy as np 
import matplotlib.pyplot as plt 
import argparse

def main(input_file, min_energy, max_energy):
    # Load the BAND.dat file (skip the header lines) 
    data = np.loadtxt(input_file, skiprows=3) 

    # Extract columns 
    k_path = data[:, 0]  # K-Path (1/Å) 
    band_up = data[:, 1]  # Spin-Up Band structure (eV) 
    band_down = data[:, 2]  # Spin-Down Band structure (eV) 
    print(data[175:186,:])

    # Create figure with scientific styling 
    plt.figure(figsize=(7, 5), dpi=300) 
    plt.plot(k_path, band_up, label="Spin Up", color="blue", linewidth=0.5) 
    plt.plot(k_path, band_down, label="Spin Down", color="red", linewidth=0.5) 

    # Add Fermi level as a horizontal dashed line 
    plt.axhline(0, color="black", linestyle="--", linewidth=1.5, label="Fermi Level") 

    # Labels and title 
    plt.xlabel("Wave Vector (1/Å)", fontsize=14, fontweight="bold") 
    plt.ylabel("Energy (eV)", fontsize=14, fontweight="bold") 
    plt.title("Electronic Band Structure", fontsize=16, fontweight="bold") 

    # Aesthetics: nice scientific style 
    plt.legend(fontsize=12, loc="upper right", frameon=False) 
    plt.grid(True, linestyle="--", alpha=0.5) 
    plt.tick_params(axis='both', which='major', labelsize=12) 
    plt.xlim(min(k_path), max(k_path))  # Adjust x-axis limits 
    if min_energy is None:
        min_energy = min(band_down) * 1.1
    if max_energy is None:
        max_energy = max(band_up) * 1.1
    plt.ylim(min_energy, max_energy)

    # Save the figure as a high-quality PNG 
    plt.savefig("BAND_Scientific.png", format="png", dpi=300, bbox_inches="tight") 

    # Show the plot 
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot VASP band structure from BAND.dat")
    parser.add_argument("--input", default="BAND.dat", help="Input BAND.dat file")
    parser.add_argument("--min_energy", type=float, default=None, help="Minimum energy for y-axis")
    parser.add_argument("--max_energy", type=float, default=None, help="Maximum energy for y-axis")
    args = parser.parse_args()
    main(args.input, args.min_energy, args.max_energy)
