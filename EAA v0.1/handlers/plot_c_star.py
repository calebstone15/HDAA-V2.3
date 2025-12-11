from utils import apply_extra_data
import numpy as np
import tkinter as tk
from tkinter import simpledialog, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def run(app):
    ctx = app.ctx
    if ctx.df is None or ctx.time_col is None or not ctx.thrust_cols or ctx.chamber_col is None:
        return

    # Prompt the user to input mdot values for fuel and oxidizer in lbs/s
    fuel_mdot = simpledialog.askfloat("Input", "Enter the mass flow rate of fuel (mdot_fuel) in lbs/s:", parent=app)
    oxidizer_mdot = simpledialog.askfloat("Input", "Enter the mass flow rate of oxidizer (mdot_oxidizer) in lbs/s:", parent=app)
    if fuel_mdot is None or oxidizer_mdot is None:
        return  # Exit if the user cancels the input

    # Calculate total mdot in lbs/s
    mdot_lbs = fuel_mdot + oxidizer_mdot

    # Convert mdot from lbs/s to slugs/s (1 slug = 32.174 lbs)
    mdot = mdot_lbs / 32.174

    # Prompt the user to input the throat area in ft^2
    throat_area = simpledialog.askfloat("Input", "Enter the throat area (in ft^2):", parent=app)
    if throat_area is None:
        return  # Exit if the user cancels the input

    # Apply extra data mask and downsample
    mask = apply_extra_data(app)
    ds = max(app.downsampling_slider.get(), 1)
    time = ctx.df[ctx.time_col][mask].iloc[::ds].values
    chamber_pressure = ctx.df[ctx.chamber_col][mask].iloc[::ds].values  # Get chamber pressure in psi

    # Convert chamber pressure from psi to lbf/ft^2 (1 psi = 144 lbf/ft^2)
    chamber_pressure_lbf_ft2 = chamber_pressure * 144

    # Calculate c* (characteristic velocity) in ft/s
    c_star_ft_s = (chamber_pressure_lbf_ft2 * throat_area) / mdot

    # Convert c* from ft/s to m/s (1 ft = 0.3048 m)
    c_star = c_star_ft_s * 0.3048

    # Create a new plot window
    plot_win = tk.Toplevel(app)
    plot_win.title("Characteristic Velocity (c*) vs Time")
    plot_win.geometry("1280x960")  # Set the window size

    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    canvas = FigureCanvasTkAgg(fig, master=plot_win)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Initial plot
    raw_line, = ax.plot(time, c_star, label="Raw Data", color="purple", alpha=0.4, linewidth=1)  # Transparent raw data
    smoothed_line, = ax.plot(time, c_star, label="Smoothed Data", color="purple", linewidth=2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Characteristic Velocity (c*) (m/s)")
    ax.set_title("Characteristic Velocity (c*) vs Time")
    ax.legend()
    ax.grid(True)  # Enable grid
    fig.tight_layout()

    # Variables to store selected points and line
    points = []
    line = None

    # Function to handle point selection
    def on_click(event):
        nonlocal line
        if event.inaxes != ax:
            return

        # Reset points if more than two are selected
        if len(points) == 2:
            points.clear()
            ax.lines = ax.lines[:-1]  # Remove the old points and line
            if line:
                line.remove()
                line = None
            canvas.draw()

        # Add the new point
        points.append((event.xdata, event.ydata))
        ax.plot(event.xdata, event.ydata, 'ro')  # Mark the selected point with red dots
        canvas.draw()

        # If two points are selected, calculate and display the average c*
        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]

            # Get the indices corresponding to the selected time range
            idx1 = np.searchsorted(time, x1)
            idx2 = np.searchsorted(time, x2)

            # Calculate the average c*
            avg_c_star = np.mean(c_star[min(idx1, idx2):max(idx1, idx2) + 1])

            # Draw a line between the two points
            line_label = f"Avg c*: {avg_c_star:.3f} m/s"
            line, = ax.plot([x1, x2], [y1, y2], 'r--', label=line_label)  # Use red dashed line

            # Draw translucent vertical lines from x1 and x2 to the average c* line
            ax.plot([x1, x1], [y1, avg_c_star], 'r-', alpha=0.3)  # Translucent line for x1
            ax.plot([x2, x2], [y2, avg_c_star], 'r-', alpha=0.3)  # Translucent line for x2

            ax.legend()
            canvas.draw()

            # Update the average c* label
            avg_c_star_lbl.config(text=f"Avg c*: {avg_c_star:.3f} m/s")
            print(f"Selected points: ({x1}, {y1}), ({x2}, {y2})")
            print(f"Calculated average c*: {avg_c_star:.3f} m/s")

    # Function to update smoothing
    def update_smoothing(val):
        window = smoothing_slider.get()
        if window > 1:
            smoothed_c_star = np.convolve(c_star, np.ones(window) / window, mode='same')
            smoothed_line.set_ydata(smoothed_c_star)
        else:
            smoothed_line.set_ydata(c_star)
        canvas.draw()

    # Function to save the plot as a PNG
    def save_plot():
        file_path = filedialog.asksaveasfilename(defaultextension=".png",
                                                 filetypes=[("PNG files", "*.png"),
                                                            ("All files", "*.*")],
                                                 title="Save Plot As")
        if file_path:
            fig.savefig(file_path)
            print(f"Plot saved to {file_path}")

    # Add smoothing slider
    smoothing_slider = tk.Scale(plot_win, from_=1, to=100, orient=tk.HORIZONTAL,
                                 label="Smoothing", command=lambda val: update_smoothing(val))
    smoothing_slider.set(1)
    smoothing_slider.place(relx=0, rely=0.9, anchor="sw")  # Bottom left corner

    # Bind the click event to the plot
    canvas.mpl_connect("button_press_event", on_click)

    # Add average c* label
    avg_c_star_lbl = tk.Label(plot_win, text="Select two points to calculate avg c*", font=("Arial", 12))
    avg_c_star_lbl.pack(pady=5)

    # Add a save button
    save_button = tk.Button(plot_win, text="Save Plot", command=save_plot)
    save_button.pack(pady=5)
