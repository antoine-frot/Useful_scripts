import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Oklab Conversion Logic (D65 whitepoint) ---
# Oklab is used because it is perceptually uniform. 
# Euclidean distances in this space correspond to perceptual differences.

def srgb_to_linear(rgb):
    """Converts sRGB to Linear RGB."""
    return np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)

def linear_to_srgb(rgb):
    """Converts Linear RGB to sRGB."""
    rgb = np.clip(rgb, 0, 1) # Clamp to valid range
    return np.where(rgb <= 0.0031308, 12.92 * rgb, 1.055 * (rgb ** (1 / 2.4)) - 0.055)

def rgb_to_oklab(rgb_srgb):
    """Converts standard sRGB (0-1) to Oklab (L, a, b)."""
    # 1. Linearize sRGB
    rgb_linear = srgb_to_linear(rgb_srgb)
    
    # 2. Linear RGB to LMS (approximate cone responses)
    m1 = np.array([
        [0.4122214708, 0.5363325363, 0.0514459929],
        [0.2119034982, 0.6806995451, 0.1073969566],
        [0.0883024619, 0.2817188376, 0.6299787005]
    ])
    lms = np.dot(rgb_linear, m1.T)
    
    # 3. Non-linear transform (cube root)
    lms_prime = np.cbrt(lms)
    
    # 4. LMS to Oklab
    m2 = np.array([
        [0.2104542553, 0.7936177850, -0.0040720468],
        [1.9779984951, -2.4285922050, 0.4505937099],
        [0.0259040371, 0.7827717662, -0.8086757660]
    ])
    return np.dot(lms_prime, m2.T)

def oklab_to_rgb(oklab):
    """Converts Oklab (L, a, b) to standard sRGB (0-1)."""
    # 1. Oklab to LMS
    m2_inv = np.array([
        [1.0, 0.3963377774, 0.2158037573],
        [1.0, -0.1055613458, -0.0638541728],
        [1.0, -0.0894841775, -1.2914855480]
    ])
    lms_prime = np.dot(oklab, m2_inv.T)
    
    # 2. Cube
    lms = lms_prime ** 3
    
    # 3. LMS to Linear RGB
    m1_inv = np.array([
        [4.0767416621, -3.3077115913, 0.2309699292],
        [-1.2684380046, 2.6097574011, -0.3413193965],
        [-0.0041960863, -0.7034186147, 1.7076147010]
    ])
    rgb_linear = np.dot(lms, m1_inv.T)
    
    # 4. Linear RGB to sRGB
    return linear_to_srgb(rgb_linear)

def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return np.array([int(hex_code[i:i+2], 16) for i in (0, 2, 4)]) / 255.0

def rgb_to_hex(rgb):
    rgb = (np.clip(rgb, 0, 1) * 255).astype(int)
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

# --- Generation Logic ---

def find_max_chroma(L, h, tolerance=0.001, max_iterations=50):
    """
    Find maximum chroma for given lightness L and hue h that stays within sRGB gamut.
    Uses binary search.
    
    Args:
        L: Lightness in Oklab (0-1)
        h: Hue angle in radians
        tolerance: Convergence tolerance for binary search
        max_iterations: Maximum search iterations
    
    Returns:
        float: Maximum chroma value
    """
    c_min = 0.0
    c_max = 0.5  # Start with reasonable upper bound
    
    # First, find an upper bound that's definitely outside gamut
    while c_max < 2.0:  # Safety limit
        a = c_max * np.cos(h)
        b = c_max * np.sin(h)
        rgb = oklab_to_rgb(np.array([L, a, b]))
        if np.any(rgb < 0) or np.any(rgb > 1):
            break
        c_max *= 2
    
    # Binary search for maximum in-gamut chroma
    for _ in range(max_iterations):
        c_mid = (c_min + c_max) / 2
        a = c_mid * np.cos(h)
        b = c_mid * np.sin(h)
        rgb = oklab_to_rgb(np.array([L, a, b]))
        
        if np.all(rgb >= 0) and np.all(rgb <= 1):
            # In gamut, try higher chroma
            c_min = c_mid
        else:
            # Out of gamut, try lower chroma
            c_max = c_mid
        
        if c_max - c_min < tolerance:
            break
    
    return c_min

def generate_variants(initial_hex_colors, n_variants_per_color, spread=0.2, luminescence_min=0.2, luminescence_max=0.95):
    """
    Generates variants for each initial color.
    
    Args:
        initial_hex_colors: List of hex color codes
        n_variants_per_color: Either an integer (same for all colors) or 
                             a list of integers (one per color)
        spread: Lightness spread around base color
        luminescence_min: Minimum lightness value
        luminescence_max: Maximum lightness value
    
    Returns:
        dict: { 'initial_hex': [list_of_generated_hex_codes] }
    """
    # Handle both single integer and list inputs
    if isinstance(n_variants_per_color, int):
        n_variants_list = [n_variants_per_color] * len(initial_hex_colors)
    else:
        n_variants_list = n_variants_per_color
        if len(n_variants_list) != len(initial_hex_colors):
            raise ValueError(f"Length of n_variants_per_color ({len(n_variants_list)}) "
                           f"must match initial_hex_colors ({len(initial_hex_colors)})")
    
    results = {}
    
    for hex_code, n_variants in zip(initial_hex_colors, n_variants_list):
        if n_variants == 1:
            results[hex_code] = [hex_code]
            continue
        
        # 1. Convert Base to Oklab
        base_rgb = hex_to_rgb(hex_code)
        base_oklab = rgb_to_oklab(base_rgb)
        L, a, b = base_oklab
        
        # 2. Calculate Polar Coordinates (Chroma and Hue)
        C = np.sqrt(a**2 + b**2)
        h = np.arctan2(b, a)
        
        generated_group = []
        
        # 3. Define lightness range
        global_spread = spread * (n_variants - 1)
        if global_spread > (luminescence_max - luminescence_min):
            l_min = luminescence_min
            l_max = luminescence_max
        else:
            l_min = max(luminescence_min, L - global_spread/2)
            l_max = min(luminescence_max, L + global_spread/2)
            if l_max - l_min != global_spread:
                if l_min == luminescence_min:
                    l_max = l_min + global_spread
                else:
                    l_min = l_max - global_spread

        l_levels = np.linspace(l_min, l_max, n_variants)
        
        for new_L in l_levels:
            # Find maximum chroma at this lightness and hue
            max_C = find_max_chroma(new_L, h)
            
            # Scale the original chroma proportionally, but cap at max_C
            # Preserve chroma ratio relative to the base color's maximum chroma
            base_max_C = find_max_chroma(L, h)
            if base_max_C > 0:
                chroma_ratio = C / base_max_C
                new_C = min(chroma_ratio * max_C, max_C * 0.95)  # Use 95% of max for safety
            else:
                new_C = 0
            
            # Convert back to Cartesian Oklab
            new_a = new_C * np.cos(h)
            new_b = new_C * np.sin(h)
            
            new_rgb = oklab_to_rgb(np.array([new_L, new_a, new_b]))
            generated_group.append(rgb_to_hex(new_rgb))
            
        results[hex_code] = generated_group
        
    return results

def visualize_palette(palette_dict):
    """Visualizes the generated colors."""
    n_groups = len(palette_dict)
    max_variants = max(len(variants) for variants in palette_dict.values())
    
    fig, ax = plt.subplots(figsize=(max_variants, n_groups))
    ax.set_axis_off()
    
    for row_idx, (seed, variants) in enumerate(palette_dict.items()):
        # Draw seed indicator (optional, though seed is usually part of the variants logic)
        for col_idx, color in enumerate(variants):
            # Check if this variant is the seed (approx)
            is_seed = (color.lower() == seed.lower())
            
            rect = patches.Rectangle(
                (col_idx, n_groups - row_idx - 1), 1, 1, 
                linewidth=0, 
                edgecolor='none', 
                facecolor=color
            )
            ax.add_patch(rect)
            
            # Label
            text_color = 'white' if int(color[1:3], 16) < 128 else 'black'
            ax.text(
                col_idx + 0.5, n_groups - row_idx - 0.5, 
                color, 
                ha='center', va='center', fontsize=8, color=text_color
            )
            
    ax.set_xlim(0, max_variants)
    ax.set_ylim(0, n_groups)
    plt.tight_layout()
    plt.show()

# --- Execution ---

if __name__ == "__main__":
    # 1. Define m Initial Colors (Hex)
    initial_colors = ["#A8089E", # Mn
                    "#FE0300", # O
                    "#86E074"] # Lithuium

    # 2. Generate n variants per group
    # Can be a single integer or a list of integers
    n_variants = [2, 3, 1]  # Different number of variants for each color
    # n_variants = 5  # Or use a single integer for all colors
    palette = generate_variants(initial_colors, n_variants)

    # 3. Visualize
    visualize_palette(palette)