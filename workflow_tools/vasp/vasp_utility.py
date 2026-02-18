import re
import sys

def is_spin_polarized(filename="OUTCAR"):
    """Check if the VASP calculation is spin-polarized by reading OUTCAR."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
            # Search for ISPIN pattern in OUTCAR
            match = re.search(r'ISPIN\s*=\s*(\d+)', content)
            if match:
                ispin = int(match.group(1))
                if ispin == 2:
                    return True
                else:
                    return False
            else:
                print(f"Error: ISPIN not found in {filename}")
                sys.exit(1)
    except FileNotFoundError:
        print(f"Error: {filename} file not found")
        sys.exit(1)
        
def extract_nbands_and_nkpts(filename="OUTCAR"):
    """Extract NBANDS and NKPTS values from OUTCAR file."""
    try:
        with open(filename, 'r') as f:
            content = f.read()
            # Search for NBANDS pattern in OUTCAR
            match = re.search(r'NBANDS\s*=\s*(\d+)', content)
            if match:
                nbands = int(match.group(1))
            else:
                print(f"Error: NBANDS not found in {filename}")
                sys.exit(1)

            match = re.search(r'NKPTS\s*=\s*(\d+)', content)
            if match:
                nkpts = int(match.group(1))
            else:
                print(f"Error: NKPTS not found in {filename}")
                sys.exit(1)

            return nbands, nkpts
    except FileNotFoundError:
        print(f"Error: {filename} file not found")
        sys.exit(1)
