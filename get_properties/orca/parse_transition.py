#!/usr/bin/env python3
"""
Parse transitions for a given state. Natural transition and canonical orbitals are available.

Returns:
tuple: (initial_orbital, final_orbital, contribution) or None
"""

import re
irred_rep = r'[ABETabet][0-9]?[gu]?'

def parse_nto_transitions(output_file, state):
    """Parse NTO transitions for a given state (with NTO)."""
    with open(output_file, 'r') as f:
        content = f.read()
    
    # Find the NTO section for the specific state
    pattern = f"NATURAL TRANSITION ORBITALS FOR STATE\s+{state}"
    match = re.search(pattern, content)
    
    if not match:
        print(f"Warning: NTO section for state {state} not found")
        return None
    
    # Find the next transition pattern after this line
    start_pos = match.end()
    remaining_content = content[start_pos:]
    
    match = re.search(rf'\s*(\d+)({irred_rep})\s+->\s+(\d+)({irred_rep})\s+:\s+n=\s+(\d+.\d+)', remaining_content)
    
    if match:
        return [(int(match.group(1)), str(match.group(2)), int(match.group(3)), str(match.group(4)), float(match.group(5)))]
    
    return None

def parse_canonical_transitions(output_file, state, threshold=0.2):
    """Parse transitions for a given state (with canonical orbitals)."""
    with open(output_file, 'r') as f:
        content = f.read()
    
    # Find the STATE section
    pattern = f"STATE\\s+{state}:"
    match = re.search(pattern, content)
    
    if not match:
        print(f"Warning: STATE {state} section not found")
        return None
    
    # Find all transitions
    start_pos = match.end()
    remaining_content = content[start_pos:]
    lines = remaining_content.split('\n')
    transitions = []
    for line in lines:
        if not line.strip():
            break
        
        # Look for transition pattern
        transition_match = re.search(rf'\s*(\d+)({irred_rep})\s+->\s+(\d+)({irred_rep})\s+:\s+(\d+.\d+)', line)
        if transition_match:
            initial_orbital = int(transition_match.group(1))
            irred_rep1 = str(transition_match.group(2))
            final_orbital = int(transition_match.group(3))
            irred_rep2 = str(transition_match.group(4))
            contribution = float(transition_match.group(5))
            if contribution > threshold:
                transitions.append((initial_orbital, irred_rep1, final_orbital, irred_rep2, contribution))
    
    if not transitions:
        return None
    
    return transitions
