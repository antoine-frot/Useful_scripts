def get_nroots(file_path):
    """Extract nroots value from file containing '> nroots' pattern"""
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if '> nroots' in line:
                    parts = line.strip().split()
                    try:
                        idx = parts.index('nroots')
                        return int(parts[idx + 1])
                    except (ValueError, IndexError):
                        pass
        return None
    except IOError:
        return None

