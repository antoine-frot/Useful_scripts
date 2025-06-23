def get_orbital_label(orbital_idx, homo_idx):
    """Convert orbital index to HOMO/LUMO notation."""
    if orbital_idx == homo_idx:
        return "HOMO"
    elif orbital_idx < homo_idx:
        diff = homo_idx - orbital_idx
        return f"HOMO-{diff}"
    else:
        diff = orbital_idx - homo_idx
        return f"LUMO+{diff}" if diff > 1 else "LUMO"