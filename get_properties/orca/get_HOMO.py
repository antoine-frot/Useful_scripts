#!/usr/bin/env python3
import re

def get_HOMO(file_path):
    """Extract HOMO orbital number from the number of electrons."""
    try:
        with open(file_path, 'r') as f:
            for line in f:
                electron_match = re.match(r' Number of Electrons\s+NEL\s+\.\.\.\.\s+(\d+)', line)
                if electron_match:
                    try:
                        HOMO = int(int(electron_match.group(1))/2)
                        return HOMO - 1 # Starting index is zero
                    except (ValueError, IndexError):
                        pass
        return None
    except IOError:
        return None
