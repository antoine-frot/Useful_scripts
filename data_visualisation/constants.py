import scipy.constants
nm_to_eV = 1239.84193 # Conversion factor from nm to eV
eV_to_au = 27.21138602 # Conversion factor from eV to atomic units
au_to_cgs_charge = 4.80320425e-10 # Conversion factor from au to cgs
au_to_cgs_length = 0.5291772108e-8 # Conversion factor from au to cgs
au_to_cgs_charge_length = au_to_cgs_charge * au_to_cgs_length * 1e20 # Conversion factor from au to cgs charge length
fine_strucure_constant = scipy.constants.alpha