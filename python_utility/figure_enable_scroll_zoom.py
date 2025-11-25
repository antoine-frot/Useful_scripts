"""
Use: call this function with a matplotlib figure just before plt.show()
to enable scroll-to-zoom functionality.
"""
def enable_scroll_zoom(figure):
    """
    Adds scroll-to-zoom functionality to a matplotlib figure.
    """
    def zoom_fun(event):
        base_scale = 1.1
        # Get the current axis under the mouse
        ax = event.inaxes
        if ax is None:
            return
        
        # Determine scale factor (Zoom In or Out)
        if event.button == 'up':
            scale_factor = 1 / base_scale
        elif event.button == 'down':
            scale_factor = base_scale
        else:
            scale_factor = 1

        # Get current limits
        cur_xlim = ax.get_xlim()
        cur_ylim = ax.get_ylim()
        
        # Get cursor position (we want to zoom relative to cursor)
        xdata = event.xdata
        ydata = event.ydata

        # Calculate new limits for X
        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        relx = (cur_xlim[1] - xdata) / (cur_xlim[1] - cur_xlim[0])
        ax.set_xlim([xdata - new_width * (1 - relx), xdata + new_width * relx])

        # Calculate new limits for Y
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor
        rely = (cur_ylim[1] - ydata) / (cur_ylim[1] - cur_ylim[0])
        ax.set_ylim([ydata - new_height * (1 - rely), ydata + new_height * rely])

        # Redraw the figure
        ax.figure.canvas.draw()

    # Connect the function to the scroll event
    figure.canvas.mpl_connect('scroll_event', zoom_fun)
