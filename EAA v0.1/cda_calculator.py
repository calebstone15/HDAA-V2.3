# cda_calculator.py
# CdA Calculator for ERPL Testing Analysis App

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os


class CdACalculatorWindow(tk.Toplevel):
    """CdA Calculator with full functionality"""
    
    # Unit conversion constants
    LBS_TO_KG = 0.453592
    PSI_TO_PA = 6894.76
    CHAMBER_PRESSURE_PA = 3447380  # ~500 PSI chamber pressure
    
    def __init__(self, launcher):
        super().__init__(launcher)
        self.launcher = launcher
        self.title("CdA Calculator")
        self.geometry("1600x900")  # Wider for side-by-side panels
        
        # Handle window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Data storage
        self.df = None
        self.time_col = None
        self.pressure_col = None
        self.weight_col = None
        self.start_time = None
        self.end_time = None
        self.calculated_mdot = None
        self.calculated_cda = None  # Store calculated CdA for set pressure calc
        
        # StringVars for setpoint calculator (must be created before UI)
        self.setpoint_cda_var = tk.StringVar()
        self.setpoint_mdot_var = tk.StringVar()
        self.setpoint_rho_var = tk.StringVar(value="1000")
        self.manifold_p_var = tk.StringVar(value="500")
        
        # Add navigation
        self._add_navigation()
        
        self._build_ui()
        
    def _add_navigation(self):
        """Add home navigation button"""
        nav_frame = tk.Frame(self)
        nav_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
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
        
    def _build_ui(self):
        """Build the CdA Calculator UI with left/right panels"""
        # Main container
        container = tk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configure grid weights for equal column sizing
        container.grid_columnconfigure(0, weight=1)
        container.grid_columnconfigure(1, weight=1)
        container.grid_rowconfigure(0, weight=1)
        
        # LEFT PANEL - CdA Calculator
        left_panel = tk.LabelFrame(container, text="CdA Calculator", font=("Arial", 14, "bold"))
        left_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self._build_cda_panel(left_panel)
        
        # RIGHT PANEL - Set Pressure Calculator
        right_panel = tk.LabelFrame(container, text="Set Pressure Calculator", font=("Arial", 14, "bold"))
        right_panel.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
        self._build_setpoint_panel(right_panel)
        
    def _build_cda_panel(self, parent):
        """Build the CdA Calculator panel (left side)"""
        main_frame = tk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Equation display
        equation_frame = tk.LabelFrame(main_frame, text="Equation", font=("Arial", 11))
        equation_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(equation_frame, text="CdA = ṁ / √(2ρΔP)", font=("Arial", 16, "italic")).pack(pady=5)
        tk.Label(equation_frame, text="ṁ=flow rate, ρ=density, ΔP=pressure drop", font=("Arial", 9), fg="gray").pack(pady=2)
        
        # CSV Loading section
        csv_frame = tk.LabelFrame(main_frame, text="1. Load CSV Data", font=("Arial", 11, "bold"))
        csv_frame.pack(fill=tk.X, pady=5)
        
        csv_inner = tk.Frame(csv_frame)
        csv_inner.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Button(csv_inner, text="Load CSV", command=self._load_csv, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        self.file_label = tk.Label(csv_inner, text="No file loaded", font=("Arial", 10), fg="gray")
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Column Selection section
        col_frame = tk.LabelFrame(main_frame, text="2. Select Columns", font=("Arial", 11, "bold"))
        col_frame.pack(fill=tk.X, pady=5)
        
        col_inner = tk.Frame(col_frame)
        col_inner.pack(fill=tk.X, pady=5, padx=5)
        
        # Time column
        tk.Label(col_inner, text="Time Column:", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.time_combo = ttk.Combobox(col_inner, state="readonly", width=30)
        self.time_combo.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        self.time_combo.bind("<<ComboboxSelected>>", self._on_time_col_changed)
        
        # Pressure column
        tk.Label(col_inner, text="Pressure Column (PSI):", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.pressure_combo = ttk.Combobox(col_inner, state="readonly", width=30)
        self.pressure_combo.grid(row=1, column=1, padx=5, pady=3, sticky="w")
        self.pressure_combo.bind("<<ComboboxSelected>>", self._on_pressure_col_changed)
        
        # Tank weight column
        tk.Label(col_inner, text="Tank Weight Column (lbs):", font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.weight_combo = ttk.Combobox(col_inner, state="readonly", width=30)
        self.weight_combo.grid(row=2, column=1, padx=5, pady=3, sticky="w")
        self.weight_combo.bind("<<ComboboxSelected>>", self._on_weight_col_changed)
        
        # Time Range section
        time_frame = tk.LabelFrame(main_frame, text="3. Select Time Range", font=("Arial", 11, "bold"))
        time_frame.pack(fill=tk.X, pady=5)
        
        time_inner = tk.Frame(time_frame)
        time_inner.pack(fill=tk.X, pady=5, padx=5)
        
        tk.Button(time_inner, text="Open Plot Window to Select Times", command=self._open_plot_window, font=("Arial", 10)).pack(side=tk.LEFT, padx=10)
        
        time_display = tk.Frame(time_inner)
        time_display.pack(side=tk.LEFT, padx=20)
        
        tk.Label(time_display, text="Start:", font=("Arial", 10)).pack(side=tk.LEFT, padx=3)
        self.start_time_label = tk.Label(time_display, text="--", font=("Arial", 10, "bold"), fg="red")
        self.start_time_label.pack(side=tk.LEFT, padx=3)
        
        tk.Label(time_display, text="End:", font=("Arial", 10)).pack(side=tk.LEFT, padx=8)
        self.end_time_label = tk.Label(time_display, text="--", font=("Arial", 10, "bold"), fg="red")
        self.end_time_label.pack(side=tk.LEFT, padx=3)
        
        # Parameters section
        params_frame = tk.LabelFrame(main_frame, text="4. Input Parameters", font=("Arial", 11, "bold"))
        params_frame.pack(fill=tk.X, pady=5)
        
        params_inner = tk.Frame(params_frame)
        params_inner.pack(fill=tk.X, pady=5, padx=5)
        
        # P_high input
        tk.Label(params_inner, text="P_high (PSI):", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.p_high_var = tk.StringVar()
        self.p_high_entry = tk.Entry(params_inner, textvariable=self.p_high_var, width=12)
        self.p_high_entry.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        tk.Button(params_inner, text="Use Avg", command=lambda: self._use_avg_pressure("high"), font=("Arial", 9)).grid(row=0, column=2, padx=3)
        
        # P_low input
        tk.Label(params_inner, text="P_low (PSI):", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.p_low_var = tk.StringVar(value="14.7")
        self.p_low_entry = tk.Entry(params_inner, textvariable=self.p_low_var, width=12)
        self.p_low_entry.grid(row=1, column=1, padx=5, pady=3, sticky="w")
        
        p_low_btns = tk.Frame(params_inner)
        p_low_btns.grid(row=1, column=2, padx=3, sticky="w")
        tk.Button(p_low_btns, text="Ambient", command=self._set_ambient_pressure, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(p_low_btns, text="From CSV", command=self._select_p_low_column, font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Density input
        tk.Label(params_inner, text="Density ρ (kg/m³):", font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.rho_var = tk.StringVar(value="1000")
        self.rho_entry = tk.Entry(params_inner, textvariable=self.rho_var, width=12)
        self.rho_entry.grid(row=2, column=1, padx=5, pady=3, sticky="w")
        tk.Label(params_inner, text="(water≈1000, LOX≈1141)", font=("Arial", 9), fg="gray").grid(row=2, column=2, padx=3, sticky="w")
        
        # Calculated mdot
        tk.Label(params_inner, text="Calculated ṁ (kg/s):", font=("Arial", 10)).grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.mdot_label = tk.Label(params_inner, text="--", font=("Arial", 10, "bold"), fg="red")
        self.mdot_label.grid(row=3, column=1, padx=5, pady=3, sticky="w")
        
        # Result section
        result_frame = tk.LabelFrame(main_frame, text="5. Result", font=("Arial", 11, "bold"))
        result_frame.pack(fill=tk.X, pady=5)
        
        result_inner = tk.Frame(result_frame)
        result_inner.pack(fill=tk.X, pady=10, padx=5)
        
        tk.Button(result_inner, text="Calculate CdA", command=self._calculate_cda, font=("Arial", 12, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.result_label = tk.Label(result_inner, text="CdA = --", font=("Arial", 18, "bold"), fg="red")
        self.result_label.pack(side=tk.LEFT, padx=20)
        
        self.result_units = tk.Label(result_inner, text="m²", font=("Arial", 12), fg="gray")
        self.result_units.pack(side=tk.LEFT)
        
    def _build_setpoint_panel(self, parent):
        """Build the Set Pressure Calculator panel (right side)"""
        main_frame = tk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Equation display
        equation_frame = tk.LabelFrame(main_frame, text="Equation", font=("Arial", 11))
        equation_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(equation_frame, text="P_set = ((ṁ/CdA)²)/(2ρ) + P_manifold", font=("Arial", 14, "italic")).pack(pady=5)
        tk.Label(equation_frame, text="Calculates required tank pressure for target flow rate", font=("Arial", 9), fg="gray").pack(pady=2)
        
        # Instructions
        instr_frame = tk.Frame(main_frame)
        instr_frame.pack(fill=tk.X, pady=5)
        tk.Label(instr_frame, text="Use CdA value from left panel, or enter manually:", font=("Arial", 10), fg="gray").pack(anchor="w")
        
        # Inputs section
        inputs_frame = tk.LabelFrame(main_frame, text="Inputs", font=("Arial", 11, "bold"))
        inputs_frame.pack(fill=tk.X, pady=5)
        
        inputs_inner = tk.Frame(inputs_frame)
        inputs_inner.pack(fill=tk.X, pady=5, padx=5)
        
        # CdA input (auto-filled or manual)
        tk.Label(inputs_inner, text="CdA (m²):", font=("Arial", 10)).grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.setpoint_cda_entry = tk.Entry(inputs_inner, textvariable=self.setpoint_cda_var, width=15)
        self.setpoint_cda_entry.grid(row=0, column=1, padx=5, pady=3, sticky="w")
        tk.Button(inputs_inner, text="← Use Calculated", command=self._copy_cda_to_setpoint, font=("Arial", 9)).grid(row=0, column=2, padx=3)
        
        # Target mass flow rate
        tk.Label(inputs_inner, text="Target ṁ (kg/s):", font=("Arial", 10)).grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.setpoint_mdot_entry = tk.Entry(inputs_inner, textvariable=self.setpoint_mdot_var, width=15)
        self.setpoint_mdot_entry.grid(row=1, column=1, padx=5, pady=3, sticky="w")
        tk.Button(inputs_inner, text="← Use Calculated", command=self._copy_mdot_to_setpoint, font=("Arial", 9)).grid(row=1, column=2, padx=3)
        
        # Fluid density
        tk.Label(inputs_inner, text="Density ρ (kg/m³):", font=("Arial", 10)).grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.setpoint_rho_entry = tk.Entry(inputs_inner, textvariable=self.setpoint_rho_var, width=15)
        self.setpoint_rho_entry.grid(row=2, column=1, padx=5, pady=3, sticky="w")
        
        rho_btns = tk.Frame(inputs_inner)
        rho_btns.grid(row=2, column=2, padx=3, sticky="w")
        tk.Button(rho_btns, text="Water", command=lambda: self.setpoint_rho_var.set("1000"), font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(rho_btns, text="LOX", command=lambda: self.setpoint_rho_var.set("1141"), font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        tk.Button(rho_btns, text="RP-1", command=lambda: self.setpoint_rho_var.set("820"), font=("Arial", 9)).pack(side=tk.LEFT, padx=2)
        
        # Manifold/Chamber pressure
        tk.Label(inputs_inner, text="Manifold P (PSI):", font=("Arial", 10)).grid(row=3, column=0, sticky="e", padx=5, pady=3)
        self.manifold_p_entry = tk.Entry(inputs_inner, textvariable=self.manifold_p_var, width=15)
        self.manifold_p_entry.grid(row=3, column=1, padx=5, pady=3, sticky="w")
        tk.Label(inputs_inner, text="(downstream pressure)", font=("Arial", 9), fg="gray").grid(row=3, column=2, padx=3, sticky="w")
        
        # Calculate button
        calc_frame = tk.Frame(main_frame)
        calc_frame.pack(fill=tk.X, pady=10)
        tk.Button(calc_frame, text="Calculate Required Set Pressure", command=self._calculate_setpoint, font=("Arial", 12, "bold")).pack(pady=5)
        
        # Result section
        result_frame = tk.LabelFrame(main_frame, text="Result", font=("Arial", 11, "bold"))
        result_frame.pack(fill=tk.X, pady=5)
        
        result_inner = tk.Frame(result_frame)
        result_inner.pack(fill=tk.X, pady=15, padx=5)
        
        self.setpoint_result_label = tk.Label(result_inner, text="P_set = -- PSI", font=("Arial", 20, "bold"), fg="red")
        self.setpoint_result_label.pack()
        
        # Secondary result in Pa
        self.setpoint_result_pa = tk.Label(result_inner, text="-- Pa", font=("Arial", 12), fg="gray")
        self.setpoint_result_pa.pack(pady=5)
        
    def _load_csv(self):
        """Load a CSV file"""
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not path:
            return
            
        try:
            self.df = pd.read_csv(path, low_memory=False)
            self.file_label.config(text=f"Loaded: {os.path.basename(path)}", fg="black")
            
            # Populate column dropdowns
            columns = list(self.df.columns)
            self.time_combo.config(values=columns)
            self.pressure_combo.config(values=columns)
            self.weight_combo.config(values=columns)
            
            # Try to auto-detect columns
            for col in columns:
                col_lower = col.lower()
                if "time" in col_lower or col_lower == "t":
                    self.time_combo.set(col)
                    self.time_col = col
                elif "pressure" in col_lower or "press" in col_lower:
                    if not self.pressure_combo.get():
                        self.pressure_combo.set(col)
                        self.pressure_col = col
                elif "weight" in col_lower or "mass" in col_lower:
                    if not self.weight_combo.get():
                        self.weight_combo.set(col)
                        self.weight_col = col
                        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV: {e}")
            
    def _open_plot_window(self):
        """Open a separate window for time selection with plot"""
        if self.df is None:
            messagebox.showerror("Error", "Please load a CSV file first.")
            return
            
        time_col = self.time_combo.get()
        pressure_col = self.pressure_combo.get()
        weight_col = self.weight_combo.get()
        
        if not time_col or not pressure_col:
            messagebox.showerror("Error", "Please select Time and Pressure columns.")
            return
            
        self.time_col = time_col
        self.pressure_col = pressure_col
        self.weight_col = weight_col
        
        # Create a separate plot window
        plot_window = CdAPlotWindow(
            self, 
            self.df, 
            time_col, 
            pressure_col, 
            weight_col,
            self._on_time_selection_confirmed
        )
        
    def _on_time_selection_confirmed(self, start_time, end_time, mdot):
        """Callback when user confirms time selection in plot window"""
        self.start_time = start_time
        self.end_time = end_time
        self.calculated_mdot = mdot
        
        # Update display
        self.start_time_label.config(text=f"{start_time:.3f} s")
        self.end_time_label.config(text=f"{end_time:.3f} s")
        
        if mdot is not None:
            self.mdot_label.config(text=f"{mdot:.4f}", fg="green")
        else:
            self.mdot_label.config(text="No weight data", fg="orange")
            
    def _on_time_col_changed(self, event=None):
        """Handle time column selection change"""
        self.time_col = self.time_combo.get()
        
    def _on_pressure_col_changed(self, event=None):
        """Handle pressure column selection change"""
        self.pressure_col = self.pressure_combo.get()
        
    def _on_weight_col_changed(self, event=None):
        """Handle weight column selection change"""
        self.weight_col = self.weight_combo.get()
        
    def _copy_cda_to_setpoint(self):
        """Copy calculated CdA to setpoint calculator"""
        if self.calculated_cda is not None:
            self.setpoint_cda_var.set(f"{self.calculated_cda:.10f}")
        else:
            messagebox.showwarning("Warning", "Please calculate CdA first.")
            
    def _copy_mdot_to_setpoint(self):
        """Copy calculated mdot to setpoint calculator"""
        if self.calculated_mdot is not None:
            self.setpoint_mdot_var.set(f"{self.calculated_mdot:.4f}")
        else:
            messagebox.showwarning("Warning", "Please select a time range with weight data first.")
            
    def _calculate_setpoint(self):
        """Calculate required set pressure using formula from jacksoncda.py"""
        try:
            # Get inputs
            cda = float(self.setpoint_cda_var.get())
            mdot = float(self.setpoint_mdot_var.get())
            rho = float(self.setpoint_rho_var.get())
            manifold_p_psi = float(self.manifold_p_var.get())
            
            if cda <= 0:
                messagebox.showerror("Error", "CdA must be positive.")
                return
            if rho <= 0:
                messagebox.showerror("Error", "Density must be positive.")
                return
                
            # Convert manifold pressure to Pa
            manifold_p_pa = manifold_p_psi * self.PSI_TO_PA
            
            # Calculate required pressure drop across injector
            # From: mdot = CdA * sqrt(2 * rho * dP)
            # Solve for dP: dP = (mdot / CdA)^2 / (2 * rho)
            delta_p_pa = ((mdot / cda) ** 2) / (2 * rho)
            
            # Total set pressure = pressure drop + manifold pressure
            p_set_pa = delta_p_pa + manifold_p_pa
            
            # Convert to PSI
            p_set_psi = p_set_pa / self.PSI_TO_PA
            
            # Display results
            self.setpoint_result_label.config(text=f"P_set = {p_set_psi:.1f} PSI")
            self.setpoint_result_pa.config(text=f"({p_set_pa:.0f} Pa)")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for all inputs.")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {e}")
            
    def _use_avg_pressure(self, which):
        """Use average pressure from selected time range"""
        if self.start_time is None or self.end_time is None:
            messagebox.showwarning("Warning", "Please select start and end times first using the Plot Window.")
            return
            
        try:
            # Get numeric time data (handles datetime strings)
            time_data = self._get_numeric_time_data()
            if time_data is None:
                messagebox.showerror("Error", "Could not parse time data.")
                return
                
            pressure_data = pd.to_numeric(self.df[self.pressure_col], errors='coerce').values
            
            mask = (time_data >= self.start_time) & (time_data <= self.end_time)
            
            if not np.any(mask):
                messagebox.showerror("Error", "No data in selected time range.")
                return
                
            avg_pressure = np.nanmean(pressure_data[mask])
            
            if which == "high":
                self.p_high_var.set(f"{avg_pressure:.2f}")
            else:
                self.p_low_var.set(f"{avg_pressure:.2f}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to calculate average: {e}")
    
    def _get_numeric_time_data(self):
        """Convert time column to numeric values (handles datetime strings)"""
        time_col_data = self.df[self.time_col]
        
        # Try numeric first
        time_numeric = pd.to_numeric(time_col_data, errors='coerce')
        
        if time_numeric.isna().all():
            # Try datetime
            try:
                time_dt = pd.to_datetime(time_col_data, errors='coerce')
                if time_dt.isna().all():
                    return None
                # Convert to seconds from start
                return (time_dt - time_dt.min()).dt.total_seconds().values
            except:
                return None
        else:
            return time_numeric.values
    
    def _set_ambient_pressure(self):
        """Set P_low to ambient pressure (14.7 PSI)"""
        self.p_low_var.set("14.7")
        
    def _select_p_low_column(self):
        """Open dialog to select P_low column from CSV and compute average"""
        if self.df is None:
            messagebox.showerror("Error", "Please load a CSV file first.")
            return
            
        if self.start_time is None or self.end_time is None:
            messagebox.showwarning("Warning", "Please select start and end times first.")
            return
            
        # Create column selection dialog
        dialog = tk.Toplevel(self)
        dialog.title("Select P_low Column")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(dialog, text="Select the pressure column for P_low:", font=("Arial", 11)).pack(pady=10)
        
        columns = list(self.df.columns)
        col_var = tk.StringVar()
        col_menu = ttk.Combobox(dialog, textvariable=col_var, values=columns, state="readonly", width=35)
        col_menu.pack(pady=10)
        
        def apply_column():
            col = col_var.get()
            if not col:
                messagebox.showwarning("Warning", "Please select a column.")
                return
            try:
                # Get numeric time data (handles datetime)
                time_data = self._get_numeric_time_data()
                if time_data is None:
                    messagebox.showerror("Error", "Could not parse time data.")
                    return
                    
                p_low_data = pd.to_numeric(self.df[col], errors='coerce').values
                
                mask = (time_data >= self.start_time) & (time_data <= self.end_time)
                
                if not np.any(mask):
                    messagebox.showerror("Error", "No data in selected time range.")
                    return
                    
                avg_p_low = np.nanmean(p_low_data[mask])
                self.p_low_var.set(f"{avg_p_low:.2f}")
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to calculate: {e}")
        
        tk.Button(dialog, text="Use Average", command=apply_column, font=("Arial", 11)).pack(pady=10)
            
    def _calculate_cda(self):
        """Calculate CdA using the formula"""
        try:
            # Get inputs
            p_high_psi = float(self.p_high_var.get())
            p_low_psi = float(self.p_low_var.get())
            rho = float(self.rho_var.get())
            
            # Get mdot
            if self.calculated_mdot is None:
                messagebox.showerror("Error", "Please select time range to calculate mdot first.")
                return
                
            mdot = self.calculated_mdot  # Already in kg/s
            
            # Convert pressures to Pa
            p_high_pa = p_high_psi * self.PSI_TO_PA
            p_low_pa = p_low_psi * self.PSI_TO_PA
            
            # Calculate ΔP
            delta_p = p_high_pa - p_low_pa
            
            if delta_p <= 0:
                messagebox.showerror("Error", "P_high must be greater than P_low.")
                return
                
            if rho <= 0:
                messagebox.showerror("Error", "Density must be positive.")
                return
                
            # Calculate CdA = mdot / sqrt(2 * rho * delta_p)
            cda = mdot / np.sqrt(2 * rho * delta_p)
            
            # Store for setpoint calculator
            self.calculated_cda = cda
            
            # Display result
            self.result_label.config(text=f"CdA = {cda:.8f}")
            
            # Also show in mm² for small orifices
            cda_mm2 = cda * 1e6
            self.result_units.config(text=f"m² ({cda_mm2:.2f} mm²)")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numeric values for all parameters.")
        except Exception as e:
            messagebox.showerror("Error", f"Calculation failed: {e}")
        
    def _on_close(self):
        """Handle window close"""
        self.withdraw()
        self.launcher.show_launcher()


class CdAPlotWindow(tk.Toplevel):
    """Optimized window for plotting and time selection - uses downsampling for performance"""
    
    LBS_TO_KG = 0.453592
    MAX_PLOT_POINTS = 2000  # Maximum points to plot for performance
    
    def __init__(self, parent, df, time_col, pressure_col, weight_col, on_confirm_callback):
        super().__init__(parent)
        self.title("Select Time Range")
        self.geometry("1000x700")
        
        # Store original data for calculations (don't modify)
        self.df = df
        self.time_col = time_col
        self.pressure_col = pressure_col
        self.weight_col = weight_col
        self.on_confirm_callback = on_confirm_callback
        
        self.start_time = None
        self.end_time = None
        self.click_count = 0
        self.cid = None
        
        # Line references for cleanup
        self.start_line = None
        self.end_line = None
        self.start_line2 = None
        self.end_line2 = None
        self.fig = None
        self.ax1 = None
        self.ax2 = None
        self.canvas = None
        
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._build_ui()
        self._create_plot()
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
    def _downsample_data(self, data, max_points):
        """Downsample data array to max_points for efficient plotting"""
        n = len(data)
        if n <= max_points:
            return data, np.arange(n)
        
        # Use every nth point
        step = n // max_points
        indices = np.arange(0, n, step)
        return data[indices], indices
        
    def _build_ui(self):
        """Build the plot window UI"""
        # Instructions at top
        instructions = tk.Label(
            self,
            text="Click on the plot twice: First click = START, second click = END.\nThen click 'Confirm Selection' to use these values.",
            font=("Arial", 11),
            fg="gray"
        )
        instructions.pack(pady=10)
        
        # Time display frame
        time_frame = tk.Frame(self)
        time_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(time_frame, text="Start Time:", font=("Arial", 11)).pack(side=tk.LEFT, padx=5)
        self.start_label = tk.Label(time_frame, text="Click on plot...", font=("Arial", 11, "bold"), fg="green")
        self.start_label.pack(side=tk.LEFT, padx=10)
        
        tk.Label(time_frame, text="End Time:", font=("Arial", 11)).pack(side=tk.LEFT, padx=20)
        self.end_label = tk.Label(time_frame, text="--", font=("Arial", 11, "bold"), fg="red")
        self.end_label.pack(side=tk.LEFT, padx=10)
        
        tk.Button(time_frame, text="Reset", command=self._reset_selection, font=("Arial", 10)).pack(side=tk.RIGHT, padx=10)
        
        # Plot container
        self.plot_container = tk.Frame(self)
        self.plot_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Bottom button frame
        button_frame = tk.Frame(self)
        button_frame.pack(fill=tk.X, pady=15)
        
        tk.Button(button_frame, text="Cancel", command=self._on_close, font=("Arial", 12)).pack(side=tk.LEFT, padx=30)
        
        self.confirm_btn = tk.Button(
            button_frame, 
            text="Confirm Selection", 
            command=self._on_confirm,
            font=("Arial", 12, "bold"),
            state=tk.DISABLED
        )
        self.confirm_btn.pack(side=tk.RIGHT, padx=30)
        
    def _create_plot(self):
        """Create optimized matplotlib plot with downsampled data"""
        try:
            # Get time data - try numeric first, then datetime
            time_col_data = self.df[self.time_col]
            
            # Try to parse as numeric first
            time_numeric = pd.to_numeric(time_col_data, errors='coerce')
            
            if time_numeric.isna().all():
                # All NaN means it's probably a datetime string - parse it
                try:
                    time_dt = pd.to_datetime(time_col_data, errors='coerce')
                    if time_dt.isna().all():
                        raise ValueError("Could not parse time column as numeric or datetime")
                    # Convert to seconds from start
                    time_data = (time_dt - time_dt.min()).dt.total_seconds().values
                except Exception:
                    raise ValueError("Could not parse time column")
            else:
                time_data = time_numeric.values
            
            # Get pressure data
            pressure_data = pd.to_numeric(self.df[self.pressure_col], errors='coerce').values
            
            # Store for later use in calculations
            self.time_data_numeric = time_data.copy()
            
            # Remove NaN values for plotting
            valid_mask = ~(np.isnan(time_data) | np.isnan(pressure_data))
            time_data = time_data[valid_mask]
            pressure_data = pressure_data[valid_mask]
            
            if len(time_data) == 0:
                raise ValueError("No valid data points to plot")
            
            # Handle weight column if present
            weight_data = None
            if self.weight_col:
                weight_data = pd.to_numeric(self.df[self.weight_col], errors='coerce').values
                weight_data = weight_data[valid_mask]
            
            # Downsample for plotting
            n_points = len(time_data)
            if n_points > self.MAX_PLOT_POINTS:
                step = max(1, n_points // self.MAX_PLOT_POINTS)
                plot_indices = np.arange(0, n_points, step)
                time_plot = time_data[plot_indices]
                pressure_plot = pressure_data[plot_indices]
                if weight_data is not None:
                    weight_plot = weight_data[plot_indices]
            else:
                time_plot = time_data
                pressure_plot = pressure_data
                weight_plot = weight_data
                
            # Create figure with minimal overhead
            plt.rcParams['path.simplify'] = True
            plt.rcParams['path.simplify_threshold'] = 1.0
            plt.rcParams['agg.path.chunksize'] = 10000
            
            if self.weight_col and weight_data is not None:
                self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
            else:
                self.fig, self.ax1 = plt.subplots(1, 1, figsize=(9, 4))
                self.ax2 = None
            
            # Plot pressure
            self.ax1.plot(time_plot, pressure_plot, 'b-', linewidth=0.5, label='Pressure')
            self.ax1.set_ylabel('Pressure (PSI)', fontsize=10)
            self.ax1.set_title('Click to select start and end times', fontsize=11)
            self.ax1.grid(True, alpha=0.3)
            self.ax1.legend(loc='upper right', fontsize=9)
            
            # Plot weight if available
            if self.weight_col and self.ax2 is not None and weight_plot is not None:
                self.ax2.plot(time_plot, weight_plot, 'g-', linewidth=0.5, label='Weight')
                self.ax2.set_xlabel('Time (s)', fontsize=10)
                self.ax2.set_ylabel('Weight (lbs)', fontsize=10)
                self.ax2.grid(True, alpha=0.3)
                self.ax2.legend(loc='upper right', fontsize=9)
            else:
                self.ax1.set_xlabel('Time (s)', fontsize=10)
                
            self.fig.tight_layout()
            
            # Embed in tkinter
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_container)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
            
            # Connect click event
            self.cid = self.fig.canvas.mpl_connect('button_press_event', self._on_plot_click)
            
        except Exception as e:
            # Show error and close
            messagebox.showerror("Plot Error", f"Failed to create plot: {e}")
            self._cleanup_and_close()
        
    def _on_plot_click(self, event):
        """Handle click on plot to select time range"""
        # Check if click is within axes
        if self.ax2 is not None:
            if event.inaxes not in [self.ax1, self.ax2]:
                return
        else:
            if event.inaxes != self.ax1:
                return
            
        x_click = event.xdata
        if x_click is None:
            return
            
        self.click_count += 1
        
        if self.click_count == 1:
            # First click - set start time
            self.start_time = x_click
            self.start_label.config(text=f"{x_click:.3f} s")
            self.end_time = None
            self.end_label.config(text="--")
            self.confirm_btn.config(state=tk.DISABLED)
            
            # Remove old lines
            self._remove_lines()
            
            # Draw vertical line for start
            self.start_line = self.ax1.axvline(x=x_click, color='green', linestyle='--', linewidth=1.5)
            if self.ax2:
                self.start_line2 = self.ax2.axvline(x=x_click, color='green', linestyle='--', linewidth=1.5)
                
        elif self.click_count == 2:
            # Second click - set end time
            self.end_time = x_click
            
            # Ensure start < end
            if self.end_time < self.start_time:
                self.start_time, self.end_time = self.end_time, self.start_time
                
            self.start_label.config(text=f"{self.start_time:.3f} s")
            self.end_label.config(text=f"{self.end_time:.3f} s")
            
            # Update start line position if swapped
            if self.start_line:
                self.start_line.set_xdata([self.start_time, self.start_time])
            if self.start_line2:
                self.start_line2.set_xdata([self.start_time, self.start_time])
            
            # Draw vertical line for end
            self.end_line = self.ax1.axvline(x=self.end_time, color='red', linestyle='--', linewidth=1.5)
            if self.ax2:
                self.end_line2 = self.ax2.axvline(x=self.end_time, color='red', linestyle='--', linewidth=1.5)
            
            # Enable confirm button
            self.confirm_btn.config(state=tk.NORMAL)
            self.click_count = 0
            
        # Efficient redraw - only draw what's needed
        self.canvas.draw_idle()
        
    def _remove_lines(self):
        """Remove all selection lines from plot"""
        for line in [self.start_line, self.end_line, self.start_line2, self.end_line2]:
            if line is not None:
                try:
                    line.remove()
                except:
                    pass
        self.start_line = None
        self.end_line = None
        self.start_line2 = None
        self.end_line2 = None
        
    def _reset_selection(self):
        """Reset time selection"""
        self.start_time = None
        self.end_time = None
        self.click_count = 0
        self.start_label.config(text="Click on plot...")
        self.end_label.config(text="--")
        self.confirm_btn.config(state=tk.DISABLED)
        
        self._remove_lines()
        if self.canvas is not None:
            self.canvas.draw_idle()
        
    def _calculate_mdot(self):
        """Calculate mass flow rate from weight slope using FULL data (not downsampled)"""
        if self.start_time is None or self.end_time is None:
            return None
            
        if not self.weight_col:
            return None
            
        try:
            # Use the stored numeric time data
            if hasattr(self, 'time_data_numeric') and self.time_data_numeric is not None:
                time_data = self.time_data_numeric
            else:
                return None
                
            weight_data = pd.to_numeric(self.df[self.weight_col], errors='coerce').values
            
            mask = (time_data >= self.start_time) & (time_data <= self.end_time)
            
            if not np.any(mask) or np.sum(mask) < 2:
                return None
                
            t_slice = time_data[mask]
            w_slice = weight_data[mask]
            
            # Remove NaN values
            valid = ~(np.isnan(t_slice) | np.isnan(w_slice))
            t_slice = t_slice[valid]
            w_slice = w_slice[valid]
            
            if len(t_slice) < 2:
                return None
            
            # Calculate slope using linear regression
            slope, _ = np.polyfit(t_slice, w_slice, 1)
            
            # mdot = -slope (positive mass flow out of decreasing tank)
            mdot_lbs = -slope
            
            # Convert to kg/s
            mdot_kg = mdot_lbs * self.LBS_TO_KG
            
            return mdot_kg
            
        except Exception:
            return None
            
    def _on_confirm(self):
        """Confirm selection and close window"""
        if self.start_time is not None and self.end_time is not None:
            mdot = self._calculate_mdot()
            self.on_confirm_callback(self.start_time, self.end_time, mdot)
        self._cleanup_and_close()
        
    def _on_close(self):
        """Handle window close"""
        self._cleanup_and_close()
        
    def _cleanup_and_close(self):
        """Properly cleanup matplotlib resources before closing"""
        # Disconnect event handler first
        if self.cid is not None and self.fig is not None:
            try:
                self.fig.canvas.mpl_disconnect(self.cid)
            except:
                pass
            self.cid = None
            
        # Close figure to release memory
        if self.fig is not None:
            try:
                plt.close(self.fig)
            except:
                pass
            self.fig = None
            
        # Release grab and destroy window
        try:
            self.grab_release()
        except:
            pass
        self.destroy()

