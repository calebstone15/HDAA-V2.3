# handlers/plot_oxidizer_weight.py
import numpy as np
from utils import apply_extra_data
import tkinter as tk
from tkinter import filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def run(app):
    ctx = app.ctx
    if ctx.df is None or ctx.oxidizer_col is None:
        return
    mask = apply_extra_data(app)
    ds = max(app.downsampling_slider.get(), 1)
    time = ctx.df[ctx.time_col][mask].iloc[::ds].values
    weight = ctx.df[ctx.oxidizer_col][mask].iloc[::ds].values

    # Create a new plot window
    plot_win = tk.Toplevel(app)
    plot_win.title("Oxidizer Tank Weight")
    plot_win.geometry("1280x960")  # Set the window size

    fig, ax = plt.subplots(figsize=(8, 4), dpi=100)
    canvas = FigureCanvasTkAgg(fig, master=plot_win)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # Initial plot
    raw_line, = ax.plot(time, weight, label="Raw Data", color="orange", alpha=0.4, linewidth=1)  # Transparent raw data
    smoothed_line, = ax.plot(time, weight, label="Smoothed Data", color="orange", linewidth=2)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Weight (lbf)")
    ax.set_title("Oxidizer Tank Weight")
    ax.legend()
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
        ax.plot(event.xdata, event.ydata, 'ro')  # Mark the selected point
        canvas.draw()

        # If two points are selected, calculate and display the slope
        if len(points) == 2:
            x1, y1 = points[0]
            x2, y2 = points[1]
            slope = (y2 - y1) / (x2 - x1)

            # Draw a line between the two points
            line_label = f"Mdot Oxidizer: {abs(slope):.3f} lbf/s"
            line, = ax.plot([x1, x2], [y1, y2], 'r--', label=line_label)
            ax.legend()
            canvas.draw()

            # Update the slope label
            mdot_lbl.config(text=f"mdot: {abs(slope):.3f} lbf/s")
            print(f"Selected points: ({x1}, {y1}), ({x2}, {y2})")
            print(f"Calculated slope (mdot): {slope:.3f} lbf/s")

    # Function to update smoothing
    def update_smoothing(val):
        window = smoothing_slider.get()
        if window > 1:
            smoothed_weight = np.convolve(weight, np.ones(window) / window, mode='same')
            smoothed_line.set_ydata(smoothed_weight)
        else:
            smoothed_line.set_ydata(weight)
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

    # Add slope label
    mdot_lbl = tk.Label(plot_win, text="Select two points to calculate mdot", font=("Arial", 12))
    mdot_lbl.pack(pady=5)

    # Add a save button
    save_button = tk.Button(plot_win, text="Save Plot", command=save_plot)
    save_button.pack(pady=5)
