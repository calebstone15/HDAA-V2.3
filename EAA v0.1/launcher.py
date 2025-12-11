# launcher.py
# Main launcher for ERPL Testing Analysis App

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os

# Get the directory of this script for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


class ERPLLauncher(tk.Tk):
    """Main launcher window for ERPL Testing Analysis App"""
    
    def __init__(self):
        super().__init__()
        self.title("ERPL Testing Analysis App")
        self.geometry("800x600")
        
        # Track current page for navigation
        self.current_page = "launcher"
        
        # Store references to child windows
        self.child_windows = {}
        
        self._build_widgets()
        
    def _build_widgets(self):
        """Build the launcher UI"""
        # Main container
        self.main_container = tk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header with logo
        header_frame = tk.Frame(self.main_container)
        header_frame.pack(side=tk.TOP, fill=tk.X, pady=30)
        
        # Try to load logo
        try:
            logo_path = os.path.join(SCRIPT_DIR, "ERPL Logo Downscaled.png")
            if os.path.exists(logo_path):
                logo_image = Image.open(logo_path)
                logo_image = logo_image.resize((200, 62), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                logo_label = tk.Label(header_frame, image=self.logo_photo)
                logo_label.pack(pady=10)
        except Exception as e:
            print(f"Could not load logo: {e}")
            
        # Title
        title_label = tk.Label(
            self.main_container,
            text="ERPL Testing Analysis App",
            font=("Arial", 28, "bold")
        )
        title_label.pack(pady=20)
        
        # Subtitle
        subtitle_label = tk.Label(
            self.main_container,
            text="Select a tool to get started",
            font=("Arial", 14),
            fg="gray"
        )
        subtitle_label.pack(pady=10)
        
        # Buttons frame
        buttons_frame = tk.Frame(self.main_container)
        buttons_frame.pack(pady=40)
        
        # Button style
        btn_width = 25
        btn_height = 2
        btn_font = ("Arial", 12)
        
        # Hotfire Data Analysis App button
        hotfire_btn = tk.Button(
            buttons_frame,
            text="📊 Hotfire Data Analysis App",
            font=btn_font,
            width=btn_width,
            height=btn_height,
            cursor="hand2",
            command=self._open_hotfire_app
        )
        hotfire_btn.pack(pady=10)
        
        # CdA Calculator button
        cda_btn = tk.Button(
            buttons_frame,
            text="🔢 CdA Calculator",
            font=btn_font,
            width=btn_width,
            height=btn_height,
            cursor="hand2",
            command=self._open_cda_calculator
        )
        cda_btn.pack(pady=10)
        
        # Draco Pressure Loss Calculator button
        draco_btn = tk.Button(
            buttons_frame,
            text="⚙️ Draco Pressure Loss Calculator",
            font=btn_font,
            width=btn_width,
            height=btn_height,
            cursor="hand2",
            command=self._open_draco_calculator
        )
        draco_btn.pack(pady=10)
        
        # Footer
        footer_frame = tk.Frame(self.main_container)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        
        footer_label = tk.Label(
            footer_frame,
            text="Developed by Caleb Stone",
            font=("Arial", 10),
            fg="gray"
        )
        footer_label.pack()
        
    def _open_hotfire_app(self):
        """Open the Hotfire Data Analysis App"""
        self.withdraw()  # Hide launcher
        self.current_page = "hotfire"
        
        if "hotfire" not in self.child_windows or not self.child_windows["hotfire"].winfo_exists():
            hotfire_window = HotfireAnalyzerAppWrapper(self)
            self.child_windows["hotfire"] = hotfire_window
        else:
            self.child_windows["hotfire"].deiconify()
            
    def _open_cda_calculator(self):
        """Open the CdA Calculator"""
        from cda_calculator import CdACalculatorWindow
        
        self.withdraw()  # Hide launcher
        self.current_page = "cda"
        
        if "cda" not in self.child_windows or not self.child_windows["cda"].winfo_exists():
            cda_window = CdACalculatorWindow(self)
            self.child_windows["cda"] = cda_window
        else:
            self.child_windows["cda"].deiconify()
            
    def _open_draco_calculator(self):
        """Open the Draco Pressure Loss Calculator"""
        self.withdraw()  # Hide launcher
        self.current_page = "draco"
        
        if "draco" not in self.child_windows or not self.child_windows["draco"].winfo_exists():
            draco_window = DracoPressureLossWindow(self)
            self.child_windows["draco"] = draco_window
        else:
            self.child_windows["draco"].deiconify()
            
    def show_launcher(self):
        """Show the launcher window"""
        self.current_page = "launcher"
        self.deiconify()


class NavigationMixin:
    """Mixin class to add home navigation button to windows"""
    
    def _add_navigation(self, parent_frame, launcher):
        """Add home navigation button"""
        nav_frame = tk.Frame(parent_frame)
        nav_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.launcher = launcher
        
        # Home button only
        home_btn = tk.Button(
            nav_frame,
            text="🏠 Home",
            font=("Arial", 12),
            cursor="hand2",
            command=self._go_home
        )
        home_btn.pack(side=tk.LEFT, padx=20)
            
    def _go_home(self):
        """Return to launcher"""
        self.withdraw()
        self.launcher.show_launcher()


class HotfireAnalyzerAppWrapper(tk.Toplevel, NavigationMixin):
    """Wrapper for the Hotfire Analyzer App with navigation"""
    
    def __init__(self, launcher):
        super().__init__(launcher)
        self.launcher = launcher
        self.title("Hotfire Data Analyzer")
        self.geometry("1200x950")
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Import and setup the original app content
        from context import AnalyzerContext
        from handlers import (load_csv, plot_isp, plot_thrust, plot_chamber_pressure,
                            plot_of_ratio, plot_fuel_weight, plot_oxidizer_weight,
                            generate_all, plot_ve_from_isp, plot_c_star, test_data, custom_plot)
        import instructions
        
        self.ctx = AnalyzerContext()
        self.time_splicing_var = tk.BooleanVar()
        
        # Add navigation at the top
        nav_container = tk.Frame(self)
        nav_container.pack(side=tk.TOP, fill=tk.X)
        self._add_navigation(nav_container, launcher)
        
        # Build the original app widgets
        self._build_hotfire_widgets(load_csv, plot_isp, plot_thrust, plot_chamber_pressure,
                                   plot_of_ratio, plot_fuel_weight, plot_oxidizer_weight,
                                   generate_all, plot_ve_from_isp, plot_c_star, test_data,
                                   custom_plot, instructions)
        
    def _build_hotfire_widgets(self, load_csv, plot_isp, plot_thrust, plot_chamber_pressure,
                               plot_of_ratio, plot_fuel_weight, plot_oxidizer_weight,
                               generate_all, plot_ve_from_isp, plot_c_star, test_data,
                               custom_plot, instructions):
        """Build the hotfire analyzer UI (same as original main.py)"""
        # Frame for the logo and title
        banner_frame = tk.Frame(self)
        banner_frame.pack(side=tk.TOP, fill=tk.X, pady=20)

        # Add logo to the top-left
        try:
            logo_path = os.path.join(SCRIPT_DIR, "ERPL Logo Downscaled.png")
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((240, 75), Image.Resampling.LANCZOS)
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(banner_frame, image=logo_photo)
            logo_label.image = logo_photo
            logo_label.pack(side=tk.LEFT, padx=10)
        except FileNotFoundError:
            print("Error: Logo file not found.")

        # Title and developer credit
        title_frame = tk.Frame(banner_frame)
        title_frame.pack(side=tk.LEFT, padx=150, anchor=tk.CENTER)

        title_label = tk.Label(title_frame, text="Hotfire Data Analysis App", font=("Arial", 30, "bold"))
        title_label.pack(side=tk.TOP, pady=0)

        developer_label = tk.Label(title_frame, text="Developed by Caleb Stone", font=("Arial", 12))
        developer_label.pack(side=tk.TOP)

        # Instructions button
        instructions_button = tk.Button(banner_frame, text="Instructions", command=lambda: instructions.run(self))
        instructions_button.pack(side=tk.RIGHT, padx=50)

        # Top frame for file-related actions
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, pady=10)

        tk.Button(top, text="Load CSV", command=lambda: load_csv.run(self)).pack(side=tk.LEFT, padx=100)
        
        self.file_label = tk.Label(top, text="No file", fg="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Sliders frame
        sliders = tk.Frame(self)
        sliders.pack(side=tk.TOP, fill=tk.X, pady=10)

        downsample_frame = tk.Frame(sliders)
        downsample_frame.pack(side=tk.LEFT, padx=275)
        tk.Label(downsample_frame, text="Downsample").pack(side=tk.LEFT)
        self.downsampling_slider = tk.Scale(downsample_frame, from_=1, to=100, orient=tk.HORIZONTAL)
        self.downsampling_slider.set(10)
        self.downsampling_slider.pack(side=tk.LEFT)

        tk.Label(sliders, text="Extra Data %").pack(side=tk.LEFT, padx=5)
        self.extra_data_slider = tk.Scale(sliders, from_=0, to=3, resolution=0.1, orient=tk.HORIZONTAL)
        self.extra_data_slider.set(0)
        self.extra_data_slider.pack(side=tk.LEFT)

        # Quick plots title
        tk.Label(self, text="Quick Plots", font=("Arial", 20, "bold")).pack(side=tk.TOP, pady=10)

        # Plot buttons
        plots = tk.Frame(self)
        plots.pack(side=tk.TOP, pady=20)

        tk.Button(plots, text="Thrust", command=lambda: plot_thrust.run(self)).pack(side=tk.LEFT, padx=3)
        tk.Button(plots, text="Chamber Pressure", command=lambda: plot_chamber_pressure.run(self)).pack(side=tk.LEFT, padx=3)
        tk.Button(plots, text="O/F Ratio", command=lambda: plot_of_ratio.run(self)).pack(side=tk.LEFT, padx=3)
        tk.Button(plots, text="Fuel Tank Weight", command=lambda: plot_fuel_weight.run(self)).pack(side=tk.LEFT, padx=3)
        tk.Button(plots, text="Oxidizer Tank Weight", command=lambda: plot_oxidizer_weight.run(self)).pack(side=tk.LEFT, padx=3)

        plots2 = tk.Frame(self)
        plots2.pack(side=tk.TOP, pady=10)

        tk.Button(plots2, text="Exhaust Velocity from Isp", command=lambda: plot_ve_from_isp.run(self)).pack(side=tk.LEFT, padx=3)
        tk.Button(plots2, text="Specific Impulse", command=lambda: plot_isp.run(self)).pack(side=tk.LEFT, padx=3)
        tk.Button(plots2, text="C* actual", command=lambda: plot_c_star.run(self)).pack(side=tk.LEFT, padx=3)

        # Bottom frame
        bottom = tk.Frame(self)
        bottom.pack(side=tk.BOTTOM, fill=tk.X, pady=50)

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
        explanation_label.pack(side=tk.BOTTOM, pady=5)

        tk.Button(bottom, text="Test Data", command=lambda: test_data.run(self)).pack(side=tk.BOTTOM, pady=10)
        tk.Button(bottom, text="Generate All Plots", command=lambda: generate_all.run(self)).pack(side=tk.BOTTOM, pady=20)
        tk.Button(bottom, text="Custom Plot", command=lambda: custom_plot.run(self)).pack(side=tk.BOTTOM, pady=10, padx=50)

        # Time splicing frame
        time_splicing_frame = tk.Frame(bottom)
        time_splicing_frame.pack(side=tk.TOP, pady=10, anchor=tk.CENTER)

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

        # Bridge UI names
        self.custom_splice_var = self.time_splicing_var
        self.custom_splice_start = self.start_time_entry
        self.custom_splice_end = self.end_time_entry

        self.apply_splice_btn = tk.Button(
            time_splicing_frame,
            text="Apply Splice",
            command=self._recalc_metrics,
            state=tk.DISABLED
        )
        self.apply_splice_btn.pack(side=tk.LEFT, padx=10)

        self.custom_splice_var.trace_add("write", self._recalc_metrics)
        self.custom_splice_start.bind("<Return>", self._recalc_metrics)
        self.custom_splice_end.bind("<Return>", self._recalc_metrics)

        def _sync_apply_state(*_):
            if self.custom_splice_var.get():
                self.apply_splice_btn.config(state=tk.NORMAL)
            else:
                self.apply_splice_btn.config(state=tk.DISABLED)
        _sync_apply_state()
        self.custom_splice_var.trace_add("write", _sync_apply_state)

        # Metrics text widget
        self.metrics_text = tk.Text(self, height=6, state=tk.DISABLED, bg=self.cget("bg"), relief=tk.FLAT)
        self.metrics_text.pack(fill=tk.X, padx=5, pady=5)
        
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

    def display_metrics(self):
        """Display metrics in the text widget"""
        self.metrics_text.config(state=tk.NORMAL)
        self.metrics_text.delete("1.0", tk.END)
        for k, v in self.ctx.metrics.items():
            self.metrics_text.insert(tk.END, f"{k}: {v}\n")
        self.metrics_text.config(state=tk.DISABLED)

    def _recalc_metrics(self, *_):
        """Recalculate metrics when slice controls change"""
        tgt = getattr(self.ctx, "last_target_thrust", None)
        if tgt is None:
            return
        from utils import compute_metrics
        compute_metrics(self, tgt)
        self.display_metrics()
        
    def _on_close(self):
        """Handle window close"""
        self.withdraw()
        self.launcher.show_launcher()


class DracoPressureLossWindow(tk.Toplevel, NavigationMixin):
    """Draco Pressure Loss Calculator window (placeholder)"""
    
    def __init__(self, launcher):
        super().__init__(launcher)
        self.launcher = launcher
        self.title("Draco Pressure Loss Calculator")
        self.geometry("800x600")
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Add navigation
        nav_container = tk.Frame(self)
        nav_container.pack(side=tk.TOP, fill=tk.X)
        self._add_navigation(nav_container, launcher)
        
        self._build_placeholder()
        
    def _build_placeholder(self):
        """Build placeholder UI"""
        content_frame = tk.Frame(self)
        content_frame.pack(expand=True, fill=tk.BOTH)
        
        # Title
        title_label = tk.Label(
            content_frame,
            text="Draco Pressure Loss Calculator",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=50)
        
        # Placeholder text
        placeholder_label = tk.Label(
            content_frame,
            text="🚧 Coming Soon 🚧\n\nThis feature is under development.",
            font=("Arial", 16),
            fg="gray"
        )
        placeholder_label.pack(pady=50)
        
    def _on_close(self):
        """Handle window close"""
        self.withdraw()
        self.launcher.show_launcher()


# Entry point
if __name__ == "__main__":
    app = ERPLLauncher()
    app.mainloop()
