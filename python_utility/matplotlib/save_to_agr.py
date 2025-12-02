import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

def save_to_agr(ax, filename):
    """
    Saves the current Matplotlib axes to a Grace (.agr) file.
    Handles data export, titles, labels, and approximates colors.
    """
    ax = plt.gca() # Get current axes
    
    # --- Helper: Color Mapping (Hex -> Grace Integer) ---
    def get_grace_color_index(mpl_color):
        # 1. Convert MPL color (name/rgba) to Hex
        hex_color = mcolors.to_hex(mpl_color)
        
        # 2. Define Standard Grace Colors (RGB)
        grace_palette = {
            0: (255, 255, 255), 1: (0, 0, 0), 2: (255, 0, 0),
            3: (0, 255, 0), 4: (0, 0, 255), 5: (255, 255, 0),
            6: (165, 42, 42), 7: (190, 190, 190), 8: (238, 130, 238),
            9: (0, 255, 255), 10: (255, 0, 255), 11: (255, 165, 0),
            12: (75, 0, 130), 13: (128, 0, 0), 14: (64, 224, 208),
            15: (0, 139, 0)
        }
        
        # 3. Parse Input Hex
        hc = hex_color.lstrip('#')
        r, g, b = tuple(int(hc[i:i+2], 16) for i in (0, 2, 4))
        
        # 4. Find Closest
        best_idx = 1 # Default to black
        min_dist = float('inf')
        for idx, (gr, gg, gb) in grace_palette.items():
            dist = (r - gr)**2 + (g - gg)**2 + (b - gb)**2
            if dist < min_dist:
                min_dist = dist
                best_idx = idx
        return best_idx

    # --- Write the File ---
    with open(filename, "w") as f:
        # 1. Write Header/Titles
        f.write('@version 50121\n')
        f.write(f'@title "{ax.get_title()}"\n')
        f.write(f'@xaxis label "{ax.get_xlabel()}"\n')
        f.write(f'@yaxis label "{ax.get_ylabel()}"\n')

        # 2. Iterate through Matplotlib lines
        lines = ax.get_lines()
        labels_seen = set()
        
        for i, line in enumerate(lines):
            # Extract styling
            color_idx = get_grace_color_index(line.get_color())
            label = line.get_label()
            
            # Write Grace Styling Commands
            # Note: We use the Integer ID for color to avoid your previous syntax error
            f.write(f'@    s{i} line color {color_idx}\n')
            f.write(f'@    s{i} symbol 0\n') # No symbol by default
            
            # Handle Legend
            if label and label not in labels_seen and not label.startswith('_'):
                labels_seen.add(label)
                f.write(f'@    s{i} legend "{label}"\n')

        # 3. Write Data
        for i, line in enumerate(lines):
            x_data = line.get_xdata()
            y_data = line.get_ydata()
            
            f.write(f'@target G0.S{i}\n')
            f.write(f'@type xy\n')
            
            for x, y in zip(x_data, y_data):
                f.write(f'{x} {y}\n')
            
            f.write('&\n') # End of dataset marker

        # Auto-scale (optional command for Grace)
        f.write('@autoscale\n')