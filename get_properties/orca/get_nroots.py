#!/usr/bin/env python3
def get_nroots(file_path):
    """Extract nroots value from file containing '> nroots' pattern"""
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if 'nroots' in line.lower():
                    parts = line.strip().split()
                    try:
                        idx = [part.lower() for part in parts].index('nroots')
                        return int(parts[idx + 1])
                    except (ValueError, IndexError):
                        pass
        return None
    except IOError:
        return None

