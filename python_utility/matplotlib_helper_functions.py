print("\nInteractive plot enabled:")
def enable_scroll_zoom(figure):
    """
    Adds advanced scroll-to-zoom functionality to a matplotlib figure.
    - Scroll: Zoom both axes (isotropic)
    - Ctrl + Scroll: Zoom X-axis only
    - Alt + Scroll: Zoom Y-axis only
    """
    print("  - Scroll: Zoom")
    print("  - Ctrl+Scroll: Zoom X")
    print("  - Alt+Scroll: Zoom Y")
    def zoom_fun(event):
        base_scale = 1.2  # Strength of the zoom
        
        # Get the current axis under the mouse
        ax = event.inaxes
        if ax is None:
            return
        
        # 1. Determine Scale Factor (Zoom In vs Out)
        if event.button == 'up':
            # Zoom In
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            # Zoom Out
            scale_factor = base_scale
        else:
            scale_factor = 1

        # 2. Determine which axes to modify based on Key Press
        # event.key returns 'control', 'alt', 'shift', or None
        zoom_x = False
        zoom_y = False

        if event.key == 'control':
            zoom_x = True   # Only X
        elif event.key == 'alt':
            zoom_y = True   # Only Y
        else:
            zoom_x = True   # Both (Default)
            zoom_y = True

        # 3. Get current cursor position (the focal point)
        xdata = event.xdata
        ydata = event.ydata

        # 4. Apply Zoom to X-Axis
        if zoom_x:
            cur_xlim = ax.get_xlim()
            new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
            # Calculate relative position of mouse within the axis
            relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
            # Update limits keeping mouse position fixed
            ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])

        # 5. Apply Zoom to Y-Axis
        if zoom_y:
            cur_ylim = ax.get_ylim()
            new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
            rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
            ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

        # 6. Redraw
        ax.figure.canvas.draw()

    # Connect the function
    figure.canvas.mpl_connect('scroll_event', zoom_fun)

def enable_keyboard_pan(figure):
    """
    Adds keyboard panning functionality to a matplotlib figure.
    - Arrow Keys
    """
    print("  - Arrows: Pan")
    def on_key(event):
        # 1. Check if the mouse is over a plot
        ax = event.inaxes
        if ax is None:
            return

        # 2. Get current limits and calculate step size (10% of screen)
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        
        x_width = xlim[1] - xlim[0]
        y_height = ylim[1] - ylim[0]
        
        padding = 0.02
        step_x = x_width * padding
        step_y = y_height * padding

        # 3. Handle Key Mappings
        key = event.key.lower() # ensure lowercase
        
        # --- LEFT ---
        if key in ['left']:
            # Move window left (subtract from limits)
            ax.set_xlim(xlim[0] - step_x, xlim[1] - step_x)
            
        # --- RIGHT ---
        elif key in ['right']:
            # Move window right (add to limits)
            ax.set_xlim(xlim[0] + step_x, xlim[1] + step_x)
            
        # --- UP ---
        elif key in ['up']: 
            # Move window up (add to limits)
            ax.set_ylim(ylim[0] + step_y, ylim[1] + step_y)
            
        # --- DOWN ---
        elif key in ['down']:
            # Move window down (subtract from limits)
            ax.set_ylim(ylim[0] - step_y, ylim[1] - step_y)

        # 4. Redraw
        ax.figure.canvas.draw()

    # Connect the function
    figure.canvas.mpl_connect('key_press_event', on_key)