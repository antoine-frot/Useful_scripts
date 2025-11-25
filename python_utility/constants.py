import scipy.constants
nm_to_eV = 1239.84193 # Conversion factor from nm to eV
eV_to_au = 27.21138602 # Conversion factor from eV to atomic units
au_to_cgs_charge = 4.80320425e-10 # Conversion factor from au to cgs
au_to_cgs_length = 0.5291772108e-8 # Conversion factor from au to cgs
eV_to_cgs = 1.602176634e-12 # Conversion factor from eV to cgs
au_to_cgs_charge_length = au_to_cgs_charge * au_to_cgs_length * 1e20 # Conversion factor from au to cgs charge length
fine_structure_constant = scipy.constants.alpha

# General constants
c = scipy.constants.c  # Speed of light in m/s
h = scipy.constants.h  # Planck's constant in J·s
h_cgs = scipy.constants.h * 1e7  # Planck's constant in CGS units (erg·s)
hbar = scipy.constants.hbar  # Reduced Planck's constant in J·s
elementary_charge = scipy.constants.e  # Elementary charge in C
elementary_charge_cgs = 4.8032047e-10 # Elementary charge in CGS units (statC)
pi = scipy.constants.pi
m_e = scipy.constants.electron_mass  # Electron mass in kg
m_e_cgs = scipy.constants.electron_mass * 1e3  # Electron mass in CGS units (g)