#!/usr/bin/env python3
"""
poscar_to_maxvesta.py

Convert a VASP-style WF_REAL_*.vasp file (POSCAR-like header + real-space
wavefunction grid) into a full-featured VESTA project (.vesta) file that closely
matches the "maximal" template you provided.

This script attempts to reproduce many of the visual / style blocks from your
example .vesta file (CELLP, STRUC, BOUND, STYLE, ISURF, LIGHTx, etc.) so when
you open the produced .vesta in VESTA it will (a) load the wavefunction grid
and (b) present the same visualization defaults.

--- Input file format (required) ---
The input must be a text file structured like your example: a POSCAR-style
structure header followed by volumetric grid information. The script reads only
the header and **ignores the numeric grid data** (VESTA will load the grid from
the same file when opening the .vesta project).

Minimal required input header items (order-sensitive):
  0: TITLE line (free text)
  1: scale factor (float)
  2-4: 3 lattice vectors (three floats each)
  5: atom species line (e.g. "Ti   S" or "Ti S")
  6: atom counts line (e.g. "1    2")
  7: optional "Selective dynamics" or directly the coordinate type line
  8: coordinate type line: either "Direct"/"DIRECT"/"Cartesian"/"CART"
  9..: atomic coordinates (one per atom_count sum). Coordinates can include
       optional labels at the end; only first three floats are read.

After the coordinates the file typically contains grid metadata (e.g. "69 69 114").
This script will stop reading coordinates after reading the expected number of
atomic sites and will not attempt to parse the grid values.

--- Output ---
A .vesta file with the same basename as the input (input: "WF_REAL_B0010_... .vasp"
-> output: "WF_REAL_B0010_... .vesta"). The produced file contains many blocks
copied/templated from your provided maximal file and substitutes cell + atom
positions and the IMPORT_DENSITY line to reference the input file.

--- Usage ---
  python poscar_to_maxvesta.py <input.vasp>

--- Notes & caveats ---
* The script assumes coordinates are fractional (DIRECT). If coordinates are
  Cartesian you will need to re-run providing the "--coords-cartesian" flag so
  the script will convert them into fractional coordinates using the provided
  lattice vectors.
* The script does NOT inspect or validate the volumetric grid; it simply
  references the original input file in the IMPORT_DENSITY line. Keep the
  grid data in the same directory as the generated .vesta file when opening
  with VESTA.
* The generated .vesta attempts to mirror the template you provided but some
  visual fields are static copies (colors, lights, ISOVALUES). You can tweak
  these later in VESTA and re-save a new template.

--- Dependencies ---
* Python 3.7+
* numpy (used to compute cell lengths & angles and to convert cart -> frac if
  requested). Install with: pip install numpy

--- Author ---
Auto-generated converter for the user. Modify the TEMPLATE_* constants below
if you want to tweak colors / boundaries / isovalues globally.
"""

import sys
import os
import argparse
from math import acos, degrees
import numpy as np

# ---------------------- User-tweakable template values ---------------------
# These values below are taken from the maximal .vesta template you pasted.
TEMPLATE_BOUND = (-0.49, 1.49, -0.49, 1.49, -0.49, 1.49)
TEMPLATE_ISOVALUE = None  # Will be calculated automatically from orbital data
TEMPLATE_ISOCOLOR = (255, 255, 0)
TEMPLATE_ISOOPACITY = (127, 255)
TEMPLATE_BG = (255, 255, 255)
# End of user-tweakable block


def calculate_default_isovalue(inp_path):
    """Calculate default isovalue from orbital data, similar to VESTA's logic.
    
    Reads the volumetric data and calculates an appropriate isovalue based on
    the data distribution (typically a small percentage of the maximum value).
    """
    try:
        with open(inp_path, 'r') as f:
            lines = f.readlines()
        
        # Find where the grid data starts (after coordinates)
        data_start = 0
        coord_mode_found = False
        atom_count = 0
        
        for i, line in enumerate(lines):
            if line.strip().upper().startswith(('DIRECT', 'CARTESIAN')):
                coord_mode_found = True
                continue
            
            if coord_mode_found and not atom_count:
                # Count atoms from species line
                try:
                    counts_line = list(map(int, lines[6].split()))
                    atom_count = sum(counts_line)
                except:
                    print("Warning: Could not parse atom counts for isovalue calculation")
                    sys.exit(1)
                continue
            
            if coord_mode_found and atom_count > 0:
                # Skip coordinate lines
                atom_count -= 1
                if atom_count == 0:
                    # Next line should be grid dimensions
                    data_start = i + 2
                    break
        
        if data_start == 0:
            raise ValueError("Could not find grid data start")
        
        # Read volumetric data
        data_values = []
        for line in lines[data_start:]:
            values = line.strip().split()
            for val in values:
                try:
                    data_values.append(abs(float(val)))  # Use absolute values
                except ValueError:
                    continue
        
        if not data_values:
            raise ValueError("No valid data values found")
        
        data_array = np.array(data_values)
        
        # Calculate isovalue similar to VESTA's default logic:
        # Use a small percentage of maximum value, but ensure it's reasonable
        max_val = np.max(data_array)
        mean_val = np.mean(data_array)
        std_val = np.std(data_array)
        
        # VESTA-like calculation: typically 1-5% of max, but adjusted by statistics
        candidate_iso = max_val * 0.02  # 2% of maximum
        
        # Adjust based on data distribution
        if candidate_iso < mean_val + 2 * std_val:
            candidate_iso = mean_val + 2 * std_val
        
        # Ensure it's not too small
        if candidate_iso < max_val * 1e-6:
            candidate_iso = max_val * 1e-4
        
        return candidate_iso
        
    except Exception as e:
        print(f"Warning: Could not calculate isovalue from {inp_path}: {e}")
        sys.exit(1)


def parse_poscar_header(lines):
    """Parse POSCAR-like header from lines (list of stripped lines).

    Returns: dict with keys: title, scale, a,b,c (vectors), species (list),
    counts (list), coords (list of [x,y,z]), coord_type ("Direct"/"Cartesian").

    Raises ValueError on malformed input.
    """
    if len(lines) < 9:
        raise ValueError("Input too short to be a POSCAR-like file")

    title = lines[0]
    scale = float(lines[1])
    a = np.array(list(map(float, lines[2].split())))
    b = np.array(list(map(float, lines[3].split())))
    c = np.array(list(map(float, lines[4].split())))

    species = lines[5].split()
    counts = list(map(int, lines[6].split()))
    total_atoms = sum(counts)

    # Read next lines until we encounter "Direct"/"DIRECT"/"Cartesian"/"CART"
    # Sometimes the coordinate type is on line 7, sometimes 8; we'll search.
    idx = 7
    coord_type = None
    # If lines[7] is 'DIRECT' or 'Cartesian' then coordinates start at 8.
    if lines[7].upper().startswith('D'):
        coord_type = 'Direct'
        coords_start = 8
    elif lines[7].upper().startswith('C'):
        coord_type = 'Cartesian'
        coords_start = 8
    else:
        # maybe there's an empty line or extra token; check lines[8]
        if lines[8].upper().startswith('D'):
            coord_type = 'Direct'
            coords_start = 9
        elif lines[8].upper().startswith('C'):
            coord_type = 'Cartesian'
            coords_start = 9
        else:
            # fallback: assume DIRECT and start at line 8
            coord_type = 'Direct'
            coords_start = 8

    coords = []
    for i in range(coords_start, coords_start + total_atoms):
        parts = lines[i].split()
        if len(parts) < 3:
            raise ValueError(f"Not enough coordinate entries on line: {lines[i]}")
        coords.append([float(parts[0]), float(parts[1]), float(parts[2])])

    return {
        'title': title,
        'scale': scale,
        'a': a * scale,
        'b': b * scale,
        'c': c * scale,
        'species': species,
        'counts': counts,
        'coords': coords,
        'coord_type': coord_type,
    }


def lattice_lengths_angles(a, b, c):
    """Return [|a|, |b|, |c|, alpha(deg), beta(deg), gamma(deg)]
    where alpha = angle between b and c, beta between a and c, gamma between a and b.
    """
    def angle(u, v):
        cosv = np.dot(u, v) / (np.linalg.norm(u) * np.linalg.norm(v))
        cosv = max(-1.0, min(1.0, cosv))
        return degrees(acos(cosv))

    la = np.linalg.norm(a)
    lb = np.linalg.norm(b)
    lc = np.linalg.norm(c)
    alpha = angle(b, c)
    beta = angle(a, c)
    gamma = angle(a, b)
    return [la, lb, lc, alpha, beta, gamma]


def cartesian_to_fractional(coords_cart, a, b, c):
    """Convert Nx3 cartesian coords to fractional using matrix [a b c].
    returns list of [x_frac, y_frac, z_frac]
    """
    M = np.vstack([a, b, c]).T  # 3x3
    Minv = np.linalg.inv(M)
    fracs = [Minv.dot(np.array(pt)) for pt in coords_cart]
    return [[float(x) for x in pt] for pt in fracs]


def generate_vesta_content(parsed, inp_basename, inp_path=None):
    """Generate the .vesta content string using the template blocks.
    The template mirrors the maximal VESTA file you provided with substitutions.
    """
    title = parsed['title']
    a, b, c = parsed['a'], parsed['b'], parsed['c']
    cell = lattice_lengths_angles(a, b, c)

    # Flatten species and per-atom entries to a list of atom labels
    species = parsed['species']
    counts = parsed['counts']
    labels = []
    for s, n in zip(species, counts):
        for i in range(n):
            labels.append(s)

    coords = parsed['coords']

    # craft STRUC block lines
    struc_lines = []
    for idx, (lab, coord) in enumerate(zip(labels, coords), start=1):
        x, y, z = coord
        # Use 6-decimal fractional formatting
        struc_lines.append( f"  {idx:2d} {lab:<4} {lab}{idx} 1.0000 {x:10.6f} {y:10.6f} {z:10.6f}    1a       1" )
        struc_lines.append("                            0.000000   0.000000   0.000000  0.00")

    # Build big template by concatenation. Many blocks below are static copies
    # from your maximal file, with cell/structure/import substitutions.

    lines = []
    lines.append("#VESTA_FORMAT_VERSION 3.5.4\n")
    lines.append("CRYSTAL\n\n")
    lines.append("TITLE\n")
    lines.append(title + "\n\n")
    lines.append("IMPORT_DENSITY 1\n")
    lines.append(f"+1.000000 {inp_basename}\n\n")

    # Minimal GROUP / SYMOP / TRAN blocks (copied from your template)
    lines.append("GROUP\n1 1 P 1\nSYMOP\n 0.000000  0.000000  0.000000  1  0  0   0  1  0   0  0  1   1\n -1.0 -1.0 -1.0  0 0 0  0 0 0  0 0 0\nTRANM 0\n 0.000000  0.000000  0.000000  1  0  0   0  1  0   0  0  1\n")
    lines.append("LTRANSL\n -1\n 0.000000  0.000000  0.000000  0.000000  0.000000  0.000000\n")
    lines.append("LORIENT\n -1   0   0   0   0\n 1.000000  0.000000  0.000000  1.000000  0.000000  0.000000\n 0.000000  0.000000  1.000000  0.000000  0.000000  1.000000\n")
    lines.append("LMATRIX\n 1.000000  0.000000  0.000000  0.000000\n 0.000000  1.000000  0.000000  0.000000\n 0.000000  0.000000  1.000000  0.000000\n 0.000000  0.000000  0.000000  1.000000\n 0.000000  0.000000  0.000000\n")

    # CELLP block using computed cell parameters
    lines.append("CELLP\n")
    lines.append(f"  {cell[0]:8.6f}   {cell[1]:8.6f}   {cell[2]:8.6f}  {cell[3]:8.6f}  {cell[4]:8.6f} {cell[5]:8.6f}\n")
    lines.append("  0.000000   0.000000   0.000000   0.000000   0.000000   0.000000\n")

    # STRUC block
    lines.append("STRUC\n")
    lines.extend([ln + "\n" for ln in struc_lines])
    lines.append("  0 0 0 0 0 0 0\n")

    # THERI block (thermal factors) default zero for each atom
    lines.append("THERI 1\n")
    for i in range(1, len(labels)+1):
        lines.append(f"  {i:2d}        {labels[i-1]}{i}  0.000000\n")
    lines.append("  0 0 0\n")

    # SHAPE, BOUND (substitute your boundary)
    lines.append("SHAPE\n  0       0       0       0   0.000000  0   192   192   192   192\n")
    b = TEMPLATE_BOUND
    lines.append("BOUND\n")
    lines.append(f"   {b[0]:8.6f}      {b[1]:8.6f}      {b[2]:8.6f}      {b[3]:8.6f}      {b[4]:8.6f}      {b[5]:8.6f}\n")
    lines.append("  0   0   0   0  0\n")

    # SBOND, SITET, VECTR, VECTT, SPLAN blocks (copied)
    lines.append("SBOND\n  1    Ti     S    0.00000    2.74646  0  1  1  0  1  0.250  2.000 127 127 127\n  0 0 0 0\n")
    lines.append("SITET\n")
    for i in range(1, len(labels)+1):
        # use per-type coloring approximations from template
        if labels[i-1].upper().startswith('TI'):
            lines.append(f"  {i:2d}        {labels[i-1]}{i}  1.4700 120 202 255 120 202 255 204  0\n")
        else:
            lines.append(f"  {i:2d}        {labels[i-1]}{i}  1.0400 255 250   0 255 250   0 204  0\n")
    lines.append("  0 0 0 0 0 0\n")
    lines.append("VECTR\n 0 0 0 0 0\nVECTT\n 0 0 0 0 0\nSPLAN\n  0   0   0   0\n")

    # Many visual style blocks directly copied (LIGHTS, STYLE, ISURF, etc.)
    lines.append("LBLAT\n -1\nLBLSP\n -1\nDLATM\n -1\nDLBND\n -1\nDLPLY\n -1\nPLN2D\n  0   0   0   0\n")
    lines.append("ATOMT\n")
    lines.append("  1         Ti  1.4700 120 202 255 120 202 255 204\n  2          S  1.0400 255 250   0 255 250   0 204\n  0 0 0 0 0 0\n")

    lines.append("SCENE\n-0.044781  0.998904  0.013619  0.000000\n 0.395203  0.030234 -0.918096  0.000000\n-0.917502 -0.035730 -0.396123  0.000000\n 0.000000  0.000000  0.000000  1.000000\n  0.000   0.000\n  0.000\n  1.000\nHBOND 0 2\n\n")

    lines.append("STYLE\nDISPF 37753794\nMODEL   0  1  0\nSURFS   0  1  1\nSECTS  32  1\nFORMS   0  1\nATOMS   0  0  1\nBONDS   1\nPOLYS   1\nVECTS 1.000000\n")
    lines.append("FORMP\n  1  1.0   0   0   0\nATOMP\n 24  24   0  50  2.0   0\nBONDP\n  1  16  0.250  2.000 127 127 127\nPOLYP\n 204 1  1.000 180 180 180\n")

    lines.append("ISURF\n")
    
    # Calculate isovalue if not provided as template constant
    if TEMPLATE_ISOVALUE is None and inp_path:
        isovalue = calculate_default_isovalue(inp_path)
    else:
        isovalue = TEMPLATE_ISOVALUE or 7.09285e-06
    
    lines.append(f"  1   0 {isovalue:.8e} {TEMPLATE_ISOCOLOR[0]} {TEMPLATE_ISOCOLOR[1]}   {TEMPLATE_ISOCOLOR[2]} {TEMPLATE_ISOOPACITY[0]} {TEMPLATE_ISOOPACITY[1]}\n  0   0   0   0\n")
    lines.append("TEX3P\n  1  0.00000E+00  1.00000E+00\n")
    lines.append("SECTP\n  1 -9.12572E-06  1.68851E-05  0.00000E+00  0.00000E+00  0.00000E+00  0.00000E+00\n")
    lines.append("CONTR\n 0.1 -1 1 1 10 -1 2 5\n 2 1 2 1\n   0   0   0\n   0   0   0\n   0   0   0\n   0   0   0\n")
    lines.append("HKLPP\n 192 1  1.000 255   0 255\nUCOLP\n   0   1  1.000   0   0   0\nCOMPS 1\nLABEL 1    12  1.000 0\nPROJT 0  0.962\n")
    lines.append("BKGRC\n 255 255 255\nDPTHQ 1 -0.5000  3.5000\n")

    # LIGHT blocks copied
    for lid in range(4):
        lines.append(f"LIGHT{lid}\n 1.000000  0.000000  0.000000  0.000000\n 0.000000  1.000000  0.000000  0.000000\n 0.000000  0.000000  1.000000  0.000000\n 0.000000  0.000000  0.000000  1.000000\n 0.000000  0.000000 20.000000  0.000000\n 0.000000  0.000000 -1.000000\n")
        if lid == 0:
            lines.append("  26  26  26 255\n 179 179 179 255\n 255 255 255 255\n")
        else:
            lines.append("   0   0   0   0\n   0   0   0   0\n   0   0   0   0\n")

    lines.append("SECCL 0\n\nTEXCL 0\n\nATOMM\n 204 204 204 255\n  25.600\n")
    lines.append("BONDM\n 255 255 255 255\n 128.000\nPOLYM\n 255 255 255 255\n 128.000\nSURFM\n   0   0   0 255\n 128.000\nFORMM\n 255 255 255 255\n 128.000\nHKLPM\n 255 255 255 255\n 128.000\n")

    return ''.join(lines)


def convert_file(inp_path, out_path=None, coords_cartesian=False):
    """Convert a single file and write the .vesta file.

    coords_cartesian: if True, treat input coords as Cartesian and convert to
    fractional using lattice vectors.
    """
    with open(inp_path, 'r') as f:
        raw_lines = [ln.rstrip('\n') for ln in f]

    # Strip trailing empty lines and keep useful lines for header parsing
    stripped = [ln.strip() for ln in raw_lines if ln.strip() != '']

    parsed = parse_poscar_header(stripped)

    if coords_cartesian or parsed['coord_type'] == 'Cartesian':
        parsed['coords'] = cartesian_to_fractional(parsed['coords'], parsed['a'], parsed['b'], parsed['c'])

    inp_basename = os.path.basename(inp_path)
    if not out_path:
        out_path = os.path.splitext(inp_path)[0] + '.vesta'

    content = generate_vesta_content(parsed, inp_basename, inp_path)
    with open(out_path, 'w') as f:
        f.write(content)

    return out_path


def main():
    p = argparse.ArgumentParser(description='Convert POSCAR-like WF_REAL_*.vasp to a maximal .vesta file')
    p.add_argument('input', nargs='?', help='Input .vasp file (POSCAR-like + grid).')
    p.add_argument('--cart', action='store_true', help='Treat input coordinates as CARTESIAN and convert to fractional')
    args = p.parse_args()

    if not args.input:
        p.print_help()
        sys.exit(1)
    if not os.path.exists(args.input):
        print(f'File not found: {args.input}')
        sys.exit(1)
    out = convert_file(args.input, coords_cartesian=args.cart)
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
