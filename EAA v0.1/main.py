# main.py

# Importing necessary modules for GUI creation and functionality
import tkinter as tk
from tkinter.ttk import Progressbar
from context import AnalyzerContext  # Custom context class for managing application state
from handlers import (load_csv, plot_isp, plot_thrust, plot_chamber_pressure,  # Importing various handlers for specific tasks
                      plot_of_ratio, plot_fuel_weight,
                      plot_oxidizer_weight, generate_all, plot_ve_from_isp, plot_c_star,
                      test_data, custom_plot)
from PIL import Image, ImageTk

import instructions  # Ensure PIL is imported

# Main application class inheriting from tkinter's Tk class
class HotfireAnalyzerApp(tk.Tk):
    def __init__(self):
        super().__init__()  # Initialize the parent class (Tk)
        self.ctx = AnalyzerContext()  # Create an instance of AnalyzerContext to manage app state and metrics
        self.time_splicing_var = tk.BooleanVar()  # Initialize the time splicing variable
        self.title("Hotfire Data Analyzer")  # Set the window title
        self.geometry("1200x900")  # Set the window size
        self._build_widgets()  # Call the method to build the UI components

    # Method to build the user interface
    def _build_widgets(self):
        # Frame for the logo and title
        banner_frame = tk.Frame(self)
        banner_frame.pack(side=tk.TOP, fill=tk.X, pady=20)

        # Add logo to the top-left
        try:
            logo_image = Image.open('/Users/calebstone/Downloads/HDAA V2/ERPL Logo Downscaled.png')
            logo_image = logo_image.resize((240, 75), Image.Resampling.LANCZOS)  # Resize the logo to smaller dimensions
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(banner_frame, image=logo_photo)
            logo_label.image = logo_photo  # Keep a reference to avoid garbage collection
            logo_label.pack(side=tk.LEFT, padx=10)
        except FileNotFoundError:
            print("Error: Logo file not found.")

        # Title and developer credit
        title_frame = tk.Frame(banner_frame)
        title_frame.pack(side=tk.LEFT, padx=150, anchor=tk.CENTER)  # Center the title frame

        title_label = tk.Label(title_frame, text="Hotfire Data Analysis App", font=("Arial", 30, "bold"))
        title_label.pack(side=tk.TOP, pady=0)  # Title at the top

        developer_label = tk.Label(title_frame, text="Developed by Caleb Stone", font=("Arial", 12))
        developer_label.pack(side=tk.TOP)  # Developer credit below the title

        # Add Instructions button
        instructions_button = tk.Button(banner_frame, text="Instructions", command=lambda: instructions.run(self))
        instructions_button.pack(side=tk.RIGHT, padx=50)  # Place the Instructions button

        # Top frame for file-related actions
        top = tk.Frame(self)  # Create a frame at the top of the window
        top.pack(side=tk.TOP, fill=tk.X, pady=10)  # Pack the frame with padding

        # Buttons for file-related actions
        tk.Button(top, text="Load CSV", command=lambda: load_csv.run(self)).pack(side=tk.LEFT, padx=100)  # Button to load CSV
        
        # Label to display the currently loaded file
        self.file_label = tk.Label(top, text="No file", fg="white")  # Default text is "No file"
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Sliders frame for user input
        sliders = tk.Frame(self)  # Create a frame for sliders
        sliders.pack(side=tk.TOP, fill=tk.X, pady=10)

        # Sub-frame for Downsample slider and label
        downsample_frame = tk.Frame(sliders)
        downsample_frame.pack(side=tk.LEFT, padx=275)
        tk.Label(downsample_frame, text="Downsample").pack(side=tk.LEFT)  # Label for downsampling slider
        self.downsampling_slider = tk.Scale(downsample_frame, from_=1, to=100, orient=tk.HORIZONTAL)  # Slider for downsampling
        self.downsampling_slider.set(10)  # Default value is 10
        self.downsampling_slider.pack(side=tk.LEFT)

        # Extra Data slider and label
        tk.Label(sliders, text="Extra Data %").pack(side=tk.LEFT, padx=5)  # Label for extra data slider
        self.extra_data_slider = tk.Scale(sliders, from_=0, to=3, resolution=0.1, orient=tk.HORIZONTAL)  # Slider for extra data
        self.extra_data_slider.set(0)  # Default value is 0
        self.extra_data_slider.pack(side=tk.LEFT)

        # Title for quick plots
        tk.Label(self, text="Quick Plots", font=("Arial", 20, "bold")).pack(side=tk.TOP, pady=10)

        # Plot buttons frame for generating specific plots
        plots = tk.Frame(self)  # Create a frame for plot buttons
        plots.pack(side=tk.TOP, pady=20)

        tk.Button(plots, text="Thrust", command=lambda: plot_thrust.run(self)).pack(side=tk.LEFT, padx=3)  # Button for thrust plot
        tk.Button(plots, text="Chamber Pressure", command=lambda: plot_chamber_pressure.run(self)).pack(side=tk.LEFT, padx=3)  # Button for chamber pressure plot
        tk.Button(plots, text="O/F Ratio", command=lambda: plot_of_ratio.run(self)).pack(side=tk.LEFT, padx=3)  # Button for O/F ratio plot
        tk.Button(plots, text="Fuel Tank Weight", command=lambda: plot_fuel_weight.run(self)).pack(side=tk.LEFT, padx=3)  # Button for fuel weight plot
        tk.Button(plots, text="Oxidizer Tank Weight", command=lambda: plot_oxidizer_weight.run(self)).pack(side=tk.LEFT, padx=3)  # Button for oxidizer weight plot

        plots2 = tk.Frame(self)  # Create a second frame for additional plot buttons
        plots2.pack(side=tk.TOP, pady=10)

        tk.Button(plots2, text="Exhaust Velocity from Isp", command=lambda: plot_ve_from_isp.run(self)).pack(side=tk.LEFT, padx=3)  # Button for exhaust velocity from ISP
        tk.Button(plots2, text="Specific Impulse", command=lambda: plot_isp.run(self)).pack(side=tk.LEFT, padx=3)  # ISP calculation
        tk.Button(plots2, text="C* actual", command=lambda: plot_c_star.run(self)).pack(side=tk.LEFT, padx=3)  # C star button

        # Bottom frame for additional actions
        bottom = tk.Frame(self)  # Create a frame for bottom buttons
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=50)  # Move the frame to the bottom of the window

        # Explanation label below the Test Data button
        explanation_label = tk.Label(
            bottom,
            text=(
                "This program uses thrust data to slice other data. Once thrust hits 50% of the target, "
                "that data is then included. If you are getting errors or the data does not look right, "
                "use the Test Data button to ensure you actually hit 50% of your target thrust."
            ),
            wraplength=800,
            justify="center",
            fg="gray")
        explanation_label.pack(side=tk.BOTTOM, pady=5)  # Ensure it is below the Test Data button

        tk.Button(bottom, text="Test Data", command=lambda: test_data.run(self)).pack(side=tk.BOTTOM, pady=10, )  # Button to test data
        tk.Button(bottom, text="Generate All Plots", command=lambda: generate_all.run(self)).pack(side=tk.BOTTOM, pady=20)  # Button to generate all plots
        tk.Button(bottom, text="Custom Plot", command=lambda: custom_plot.run(self)).pack(side=tk.BOTTOM, pady=10, padx=50)  # Button for custom plot

        # Add checkbox and input boxes for time-based splicing
        time_splicing_frame = tk.Frame(bottom)
        time_splicing_frame.pack(side=tk.TOP, pady=10, anchor=tk.CENTER)  # Center-align the frame

        time_splicing_checkbox = tk.Checkbutton(
            time_splicing_frame, text="Custom Time Splicing", variable=self.time_splicing_var
        )
        time_splicing_checkbox.pack(side=tk.TOP, pady=10)

        tk.Label(time_splicing_frame, text="Start Time (s):").pack(side=tk.LEFT, padx=5)
        self.start_time_entry = tk.Entry(time_splicing_frame, width=10)
        self.start_time_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(time_splicing_frame, text="End Time (s):").pack(side=tk.LEFT, padx=5)
        self.end_time_entry = tk.Entry(time_splicing_frame, width=10)
        self.end_time_entry.pack(side=tk.LEFT, padx=5)

        # --- bridge UI names so utils.compute_metrics can see them ---
        self.custom_splice_var   = self.time_splicing_var
        self.custom_splice_start = self.start_time_entry
        self.custom_splice_end   = self.end_time_entry

        self.apply_splice_btn = tk.Button(
            time_splicing_frame,
            text="Apply Splice",
            command=self._recalc_metrics,       # call the helper you added earlier
            state=tk.DISABLED                   # starts disabled until box is ticked
        )
        self.apply_splice_btn.pack(side=tk.LEFT, padx=10)

        # --- tell the GUI when to recalc ---
        self.custom_splice_var.trace_add("write", self._recalc_metrics)
        self.custom_splice_start.bind("<Return>", self._recalc_metrics)
        self.custom_splice_end.bind("<Return>",   self._recalc_metrics)

        # --- NEW: keep the Apply button enabled only when needed ----------
        def _sync_apply_state(*_):
            if self.custom_splice_var.get():
                self.apply_splice_btn.config(state=tk.NORMAL)
            else:
                self.apply_splice_btn.config(state=tk.DISABLED)
        # run once now and whenever the box toggles
        _sync_apply_state()
        self.custom_splice_var.trace_add("write", _sync_apply_state)

        # Text widget to display metrics
        self.metrics_text = tk.Text(self, height=6, state=tk.DISABLED, bg=self.cget("bg"), relief=tk.FLAT)  # Read-only text widget
        self.metrics_text.pack(fill=tk.X, padx=5, pady=5)
        
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

    # Public helper method to display metrics in the text widget
    def display_metrics(self):
        self.metrics_text.config(state=tk.NORMAL)  # Enable editing temporarily
        self.metrics_text.delete("1.0", tk.END)  # Clear existing text
        for k, v in self.ctx.metrics.items():  # Iterate through metrics in the context
            self.metrics_text.insert(tk.END, f"{k}: {v}\n")  # Insert each metric as a new line
        self.metrics_text.config(state=tk.DISABLED)  # Disable editing again

    # --- run metrics again whenever the slice controls change ---
    def _recalc_metrics(self, *_):
        tgt = getattr(self.ctx, "last_target_thrust", None)
        if tgt is None:
            return          # no CSV loaded yet
        from utils import compute_metrics
        compute_metrics(self, tgt)
        self.display_metrics()

# Entry point of the application
if __name__ == "__main__":
    HotfireAnalyzerApp().mainloop()  # Start the Tkinter event loop