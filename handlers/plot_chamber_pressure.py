# handlers/plot_chamber_pressure.py
import numpy as np
from utils import apply_extra_data
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def run(app):
    ctx = app.ctx
    if ctx.df is None or ctx.time_col is None or ctx.chamber_col is None:
        return
    mask = apply_extra_data(app)
    ds = max(app.downsampling_slider.get(), 1)
    time = ctx.df[ctx.time_col][mask].iloc[::ds].values
    press = ctx.df[ctx.chamber_col][mask].iloc[::ds].values

    # Create a new plot window
    plot_win = tk.Toplevel(app)
    plot_win.title("Chamber Pressure vs Time")
    plot_win.geometry("1280x960")  # Set the window size

    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    canvas = FigureCanvasTkAgg(fig, master=plot_win)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Initial plot
    raw_line, = ax.plot(time, press, label="Raw Data", color="red", alpha=0.4, linewidth=1)  # Transparent raw data
    smoothed_line, = ax.plot(time, press, label="Smoothed Data", color="red", linewidth=2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Pressure (psi)")
    ax.set_title("Chamber Pressure vs Time")
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
            ax.lines = ax.lines[:-1]  # Remove the old red points and line
            if line:
                line.remove()
                line = None
            canvas.draw()

        # Add the new point
        points.append((event.xdata, event.ydata))
        ax.plot(event.xdata, event.ydata, 'bo')  # Mark the selected point with blue dots
        canvas.draw()

        # If two points are selected, calculate and display the average chamber pressure
        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]

            # Get the indices corresponding to the selected time range
            idx1 = np.searchsorted(time, x1)
            idx2 = np.searchsorted(time, x2)

            # Calculate the average chamber pressure
            avg_pressure = np.mean(press[min(idx1, idx2):max(idx1, idx2) + 1])

            # Draw a line between the two points
            line_label = f"Avg Pressure: {avg_pressure:.3f} psi"
            line, = ax.plot([x1, x2], [y1, y2], 'b--', label=line_label)  # Use blue dashed line

            # Draw translucent vertical lines from x1 and x2 to the average pressure line
            ax.plot([x1, x1], [y1, avg_pressure], 'b-', alpha=0.3)  # Translucent line for x1
            ax.plot([x2, x2], [y2, avg_pressure], 'b-', alpha=0.3)  # Translucent line for x2

            ax.legend()
            canvas.draw()

            # Update the average pressure label
            avg_pressure_lbl.config(text=f"Avg Pressure: {avg_pressure:.3f} psi")
            print(f"Selected points: ({x1}, {y1}), ({x2}, {y2})")
            print(f"Calculated average chamber pressure: {avg_pressure:.3f} psi")

    # Function to update smoothing
    def update_smoothing(val):
        window = smoothing_slider.get()
        if window > 1:
            smoothed_press = np.convolve(press, np.ones(window) / window, mode='same')
            smoothed_line.set_ydata(smoothed_press)
        else:
            smoothed_line.set_ydata(press)
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

    # Add average pressure label
    avg_pressure_lbl = tk.Label(plot_win, text="Select two points to calculate avg chamber pressure", font=("Arial", 12))
    avg_pressure_lbl.pack(pady=5)

    # Add a save button
    save_button = tk.Button(plot_win, text="Save Plot", command=save_plot)
    save_button.pack(pady=5)
