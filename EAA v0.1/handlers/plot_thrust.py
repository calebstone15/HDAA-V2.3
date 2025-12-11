# handlers/plot_thrust.py
import numpy as np
from utils import apply_extra_data
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


def run(app):
    ctx = app.ctx
    if ctx.df is None or ctx.time_col is None or not ctx.thrust_cols:
        return
    mask = apply_extra_data(app)
    ds = max(app.downsampling_slider.get(), 1)
    time = ctx.df[ctx.time_col][mask].iloc[::ds].values
    thrust = ctx.df.loc[mask, ctx.thrust_cols].sum(axis=1).iloc[::ds].values

    # Create a new plot window
    plot_win = tk.Toplevel(app)
    plot_win.title("Thrust vs Time")
    plot_win.geometry("1280x960")  # Set the window size

    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    canvas = FigureCanvasTkAgg(fig, master=plot_win)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Initial plot
    raw_line, = ax.plot(time, thrust, label="Raw Data", color="blue", alpha=0.4, linewidth=1)  # Transparent raw data
    smoothed_line, = ax.plot(time, thrust, label="Smoothed Data", color="blue", linewidth=2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Thrust (lbf)")
    ax.set_title("Thrust vs Time")
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
            ax.lines = ax.lines[:-1]  # Remove the old blue points and line
            if line:
                line.remove()
                line = None
            canvas.draw()

        # Add the new point
        points.append((event.xdata, event.ydata))
        ax.plot(event.xdata, event.ydata, 'ro')  # Mark the selected point with red dots
        canvas.draw()

        # If two points are selected, calculate and display the average thrust
        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]

            # Get the indices corresponding to the selected time range
            idx1 = np.searchsorted(time, x1)
            idx2 = np.searchsorted(time, x2)

            # Calculate the average thrust
            avg_thrust = np.mean(thrust[min(idx1, idx2):max(idx1, idx2) + 1])

            # Draw a line between the two points
            line_label = f"Avg Thrust: {avg_thrust:.3f} lbf"
            line, = ax.plot([x1, x2], [y1, y2], 'r--', label=line_label)  # Use red dashed line

            # Draw translucent vertical lines from x1 and x2 to the average thrust line
            ax.plot([x1, x1], [y1, avg_thrust], 'r-', alpha=0.3)  # Translucent line for x1
            ax.plot([x2, x2], [y2, avg_thrust], 'r-', alpha=0.3)  # Translucent line for x2

            ax.legend()
            canvas.draw()

            # Update the average thrust label
            avg_thrust_lbl.config(text=f"Avg Thrust: {avg_thrust:.3f} lbf")
            print(f"Selected points: ({x1}, {y1}), ({x2}, {y2})")
            print(f"Calculated average thrust: {avg_thrust:.3f} lbf")

    # Function to update smoothing
    def update_smoothing(val):
        window = smoothing_slider.get()
        if window > 1:
            smoothed_thrust = np.convolve(thrust, np.ones(window) / window, mode='same')
            smoothed_line.set_ydata(smoothed_thrust)
        else:
            smoothed_line.set_ydata(thrust)
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

    # Add average thrust label
    avg_thrust_lbl = tk.Label(plot_win, text="Select two points to calculate avg thrust", font=("Arial", 12))
    avg_thrust_lbl.pack(pady=5)

    # Add a save button
    save_button = tk.Button(plot_win, text="Save Plot", command=save_plot)
    save_button.pack(pady=5)
