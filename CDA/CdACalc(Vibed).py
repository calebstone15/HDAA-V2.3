import tkinter as tk
from tkinter import filedialog, messagebox, font

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

# --- Constants ---
# Densities in kg/m^3
FLUID_DENSITIES = {
    "Water": 1000,
    "Ethanol": 789,
    "LOX (Liquid Oxygen)": 1141,
    "IPA (Isopropyl Alcohol)": 786,
    "LN2 (Liquid Nitrogen)": 808,
}

# --- Global Variables ---
df = None  # Holds the loaded DataFrame
time_col_sec = "Time (s)" # Name of the new seconds column

# --- Plotting-specific globals ---
plot_window = None
plot_canvas = None
plot_fig = None
plot_ax1 = None
plot_ax2 = None
plot_markers = [] # List to store markers (lines and text)

# --- Core Functions ---

def load_csv():
    """
    Opens a file dialog to select a CSV, loads it into the global
    DataFrame, and populates the column selection dropdowns.
    """
    global df
    file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return  # User canceled

    try:
        df = pd.read_csv(file_path)
        file_label.config(text=file_path.split('/')[-1]) # Show filename
        
        # Get column names
        column_names = list(df.columns)
        
        # Clear old menu items
        time_menu['menu'].delete(0, 'end')
        pressure_menu['menu'].delete(0, 'end')
        mdot_menu['menu'].delete(0, 'end')
        
        # Add new menu items
        for col in column_names:
            time_menu['menu'].add_command(label=col, command=lambda value=col: time_var.set(value))
            pressure_menu['menu'].add_command(label=col, command=lambda value=col: pressure_var.set(value))
            mdot_menu['menu'].add_command(label=col, command=lambda value=col: mdot_var.set(value))
            
        # Set default selections
        if column_names:
            time_var.set(column_names[0])
            pressure_var.set(column_names[0])
            mdot_var.set(column_names[0])
            
        plot_button.config(state=tk.NORMAL) # Enable plotting
            
    except Exception as e:
        messagebox.showerror("Error Loading CSV", f"Failed to read file: {e}")
        df = None
        file_label.config(text="No file loaded")
        plot_button.config(state=tk.DISABLED)

def on_plot_click(event):
    """
    Handles click events on the plot canvas to add time markers.
    """
    global plot_ax1, plot_ax2, plot_canvas, plot_markers
    
    # Do nothing if the plot components aren't ready
    if not all([event.inaxes, plot_ax1, plot_ax2, plot_canvas]):
        return
        
    if event.inaxes not in [plot_ax1, plot_ax2]:
        return

    time_val = event.xdata
    
    # Draw vertical lines
    line1 = plot_ax1.axvline(time_val, color='g', linestyle='--', linewidth=1)
    line2 = plot_ax2.axvline(time_val, color='g', linestyle='--', linewidth=1)
    
    # Add text annotation
    # Place text relative to the axes to avoid it being off-screen
    y_range = plot_ax1.get_ylim()
    text_y = y_range[0] + 0.9 * (y_range[1] - y_range[0]) # 90% up from bottom
    
    text_obj = plot_ax1.text(time_val + (plot_ax1.get_xlim()[1] * 0.005), #Slight offset
                             text_y, 
                             f" T={time_val:.3f}s", 
                             color='white', backgroundcolor='black',
                             fontsize=9, ha='left')
    
    # Store markers to be cleared later
    plot_markers.append(line1)
    plot_markers.append(line2)
    plot_markers.append(text_obj)
    
    plot_canvas.draw()

def clear_markers():
    """
    Removes all user-added markers from the plot.
    """
    global plot_markers, plot_canvas
    if not plot_markers:
        return
        
    for marker in plot_markers:
        try:
            marker.remove()
        except ValueError:
            pass # Marker may have already been removed
            
    plot_markers.clear()
    
    if plot_canvas:
        plot_canvas.draw()

def plot_data():
    """
    Converts selected columns, normalizes time, and plots Pressure/Mdot vs. Time
    in a new, separate window.
    """
    global df, time_col_sec
    global plot_window, plot_canvas, plot_fig, plot_ax1, plot_ax2, plot_markers
    
    if df is None:
        messagebox.showwarning("No Data", "Please load a CSV file first.")
        return

    # Get selected column names
    time_col = time_var.get()
    pressure_col = pressure_var.get()
    mdot_col = mdot_var.get()

    if not all([time_col, pressure_col, mdot_col]):
        messagebox.showwarning("Missing Selections", "Please select all three columns.")
        return

    try:
        # --- 1. Time Conversion ---
        # More robust time conversion logic
        try:
            # Try to infer format first (e.g., '2023-10-27 14:30:05.123')
            time_datetime = pd.to_datetime(df[time_col], infer_datetime_format=True)
            t0 = time_datetime.iloc[0]
            df[time_col_sec] = (time_datetime - t0).dt.total_seconds()
        except (ValueError, TypeError):
            # If that fails, try the 'HH:MM:SS.sss' format
            try:
                time_datetime = pd.to_datetime(df[time_col], format='%H:%M:%S.%f')
                t0 = time_datetime.iloc[0]
                df[time_col_sec] = (time_datetime - t0).dt.total_seconds()
            except (ValueError, TypeError):
                # If that fails, try to treat it as a numeric column (already in seconds)
                try:
                    df[time_col_sec] = pd.to_numeric(df[time_col])
                    # Normalize to start from 0
                    df[time_col_sec] = df[time_col_sec] - df[time_col_sec].iloc[0]
                except (ValueError, TypeError):
                    # If all fail, raise a more informative error
                    raise ValueError(f"Time column '{time_col}' could not be converted. \n"
                                     "Please ensure it is a standard date/time format, \n"
                                     "'HH:MM:SS.sss' format, or already numeric seconds.")

        # --- 2. Data Conversion (Pressure & Mdot) ---
        df[pressure_col] = pd.to_numeric(df[pressure_col], errors='coerce')
        df[mdot_col] = pd.to_numeric(df[mdot_col], errors='coerce')
        
        # --- NEW: Ask for Unit Conversion ---
        # User requested this be removed. We will assume PSI and convert in
        # the calculate_cda function.
        pressure_units_label = " (PSI)" # Assume PSI for plot

        # Check for conversion errors (NaNs)
        if df[pressure_col].isna().any() or df[mdot_col].isna().any():
            messagebox.showwarning("Data Error", "Pressure or Mdot column contains non-numeric data.")
            # Drop rows where conversion failed for plotting
            plot_df = df.dropna(subset=[time_col_sec, pressure_col, mdot_col])
        else:
            plot_df = df
            
        if plot_df.empty:
            messagebox.showerror("Plot Error", "No valid data to plot after conversion.")
            return

        # --- 3. Plotting ---
        
        # If a plot window already exists, destroy it
        if plot_window:
            try:
                plot_window.destroy()
            except tk.TclError:
                pass # Window already closed
        
        # Clear old markers
        plot_markers.clear()

        # Create a new Toplevel window for the plot
        plot_window = tk.Toplevel(root)
        plot_window.title(f"Plots for {file_label.cget('text')}")
        plot_window.geometry("800x600")

        # Initialize the figure and axes
        # --- THIS LINE WAS THE BUG ---
        # It was: plot_ax1, (plot_ax1, plot_ax2) = plt.subplots(...)
        # It should be:
        plot_fig, (plot_ax1, plot_ax2) = plt.subplots(2, 1, sharex=True, figsize=(10, 6))
        # --- END FIX ---

        plot_fig.suptitle("Pressure and Mass Flow Rate vs. Time")
        
        # Plot Pressure
        plot_ax1.plot(plot_df[time_col_sec], plot_df[pressure_col], label=pressure_col, color='b')
        plot_ax1.set_ylabel(f"Pressure ({pressure_col}){pressure_units_label}")
        plot_ax1.legend(loc='upper right')
        plot_ax1.grid(True)

        # Plot Mdot
        plot_ax2.plot(plot_df[time_col_sec], plot_df[mdot_col], label=mdot_col, color='r')
        plot_ax2.set_ylabel(f"Mdot ({mdot_col})")
        plot_ax2.set_xlabel(time_col_sec)
        plot_ax2.legend(loc='upper right')
        plot_ax2.grid(True)

        plot_fig.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout for suptitle

        # Embed the figure in the Tkinter Toplevel window
        plot_canvas = FigureCanvasTkAgg(plot_fig, master=plot_window)
        plot_canvas.draw()
        plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Add the Matplotlib navigation toolbar
        toolbar = NavigationToolbar2Tk(plot_canvas, plot_window)
        toolbar.update()
        plot_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Connect the click event handler
        plot_canvas.mpl_connect('button_press_event', on_plot_click)
        
        # Enable calculation
        calc_button.config(state=tk.NORMAL)

    except Exception as e:
        messagebox.showerror("Plotting Error", f"Failed to process and plot data: {e}")

def calculate_cda():
    """
    Calculates the average CdA based on user inputs for time splice,
    fluid density, and ambient pressure.
    """
    if df is None:
        messagebox.showwarning("No Data", "Please load and plot data first.")
        return

    # --- 1. Get Inputs ---
    try:
        start_time = float(start_time_entry.get())
        end_time = float(end_time_entry.get())
        p_ambient = float(p_ambient_entry.get())
    except ValueError:
        messagebox.showerror("Input Error", "Start Time, End Time, and Ambient Pressure must be numbers.")
        return

    fluid_name = fluid_var.get()
    density = FLUID_DENSITIES.get(fluid_name)
    pressure_col = pressure_var.get()
    mdot_col = mdot_var.get()

    # --- 2. Validate Inputs ---
    if start_time >= end_time:
        messagebox.showerror("Input Error", "Start Time must be less than End Time.")
        return
        
    if not density:
        messagebox.showerror("Input Error", "Please select a valid fluid.")
        return

    # --- 3. Splice Data ---
    spliced_df = df[
        (df[time_col_sec] >= start_time) & (df[time_col_sec] <= end_time)
    ].copy() # Use .copy() to avoid SettingWithCopyWarning

    if spliced_df.empty:
        messagebox.showwarning("No Data", "No data found in the specified time range.")
        return

    # --- 4. Calculate CdA ---
    # Equation: mdot = CdA * sqrt(2 * rho * delta_p)
    # Rearranged: CdA = mdot / sqrt(2 * rho * delta_p)
    
    # --- NEW LOGIC (as per user request) ---
    # 1. Average the spliced data for pressure and mdot
    # 2. Calculate a single Delta P from the average pressure
    # 3. Calculate a single CdA from the averages
    
    try:
        # --- 1. Calculate Averages ---
        avg_pressure = spliced_df[pressure_col].mean()
        avg_mdot = spliced_df[mdot_col].mean()

        # --- 2. Calculate Delta P ---
        # Per user: "it should be ducer - ambient"
        # This assumes flow is from transducer (e.g. tank) to ambient.
        
        # --- NEW: Convert avg_pressure from PSI to Pa ---
        avg_pressure_pa = avg_pressure * 6894.76
        
        delta_p = avg_pressure_pa - p_ambient
        
        if delta_p <= 0:
            messagebox.showwarning("Calculation Error", 
                                   f"Average pressure in range ({avg_pressure:.2f} PSI / {avg_pressure_pa:.2f} Pa) "
                                   f"is not greater than ambient pressure ({p_ambient} Pa).")
            return
            
        # --- 3. Get Absolute Mdot ---
        # Use absolute value to handle both positive flow meters
        # and negative load cells (decreasing mass)
        mdot_abs = abs(avg_mdot)
        
        if mdot_abs == 0:
            messagebox.showwarning("Calculation Error", "Average Mdot in range is 0.")
            return

        # --- 4. Calculate Final CdA ---
        # CdA = mdot / sqrt(2 * rho * delta_p)
        denominator = np.sqrt(2 * density * delta_p)
        
        if denominator == 0:
            messagebox.showwarning("Calculation Error", "Calculation denominator is zero (check density or delta_p).")
            return
            
        avg_cda = mdot_abs / denominator
        
        # Display the result
        result_label.config(text=f"{avg_cda:.5e} m^2")
        
    except Exception as e:
        messagebox.showerror("Calculation Error", f"An error occurred during calculation: {e}")

# --- GUI Setup ---
root = tk.Tk()
root.title("CdA Calculator")
root.geometry("1000x800")

# Set a slightly larger default font
default_font = font.nametofont("TkDefaultFont")
default_font.configure(size=11)

# --- Top Frame (File & Column Selection) ---
top_frame = tk.Frame(root, bd=2, relief=tk.RIDGE, padx=5, pady=5)
top_frame.pack(side=tk.TOP, fill=tk.X, pady=5, padx=5)

# Row 0: File Loading
load_button = tk.Button(top_frame, text="Load CSV File", command=load_csv)
load_button.grid(row=0, column=0, padx=5, pady=5, sticky="w")
file_label = tk.Label(top_frame, text="No file loaded", relief=tk.SUNKEN, anchor="w", width=40)
file_label.grid(row=0, column=1, columnspan=2, padx=5, sticky="ew")

# Row 1: Column Labels
tk.Label(top_frame, text="Time Column:").grid(row=1, column=0, padx=5, sticky="e")
tk.Label(top_frame, text="Pressure Column:").grid(row=1, column=1, padx=5, sticky="e")
tk.Label(top_frame, text="Mdot Column:").grid(row=1, column=2, padx=5, sticky="e")

# Row 2: Column Dropdowns
time_var = tk.StringVar(root)
time_menu = tk.OptionMenu(top_frame, time_var, " (Load CSV first) ")
time_menu.grid(row=2, column=0, padx=5, sticky="ew")

pressure_var = tk.StringVar(root)
pressure_menu = tk.OptionMenu(top_frame, pressure_var, " (Load CSV first) ")
pressure_menu.grid(row=2, column=1, padx=5, sticky="ew")

mdot_var = tk.StringVar(root)
mdot_menu = tk.OptionMenu(top_frame, mdot_var, " (Load CSV first) ")
mdot_menu.grid(row=2, column=2, padx=5, sticky="ew")

# Row 3: Plot Button
plot_button = tk.Button(top_frame, text="Confirm Columns & Plot Data", command=plot_data, state=tk.DISABLED, bg="#D4EDDA")
plot_button.grid(row=3, column=0, columnspan=3, pady=10, padx=5, sticky="ew")

# Configure grid expansion
top_frame.grid_columnconfigure(0, weight=1)
top_frame.grid_columnconfigure(1, weight=1)
top_frame.grid_columnconfigure(2, weight=1)

# --- Plot Frame (Matplotlib) ---
# This section has been removed. The plot is now created in a Toplevel window.

# --- Bottom Frame (Splicing & Calculation) ---
bottom_frame = tk.Frame(root, bd=2, relief=tk.RIDGE, padx=5, pady=5)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5, padx=5)

# Row 0: Splicing Inputs
tk.Label(bottom_frame, text="Start Time (s):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
start_time_entry = tk.Entry(bottom_frame, width=10)
start_time_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(bottom_frame, text="End Time (s):").grid(row=0, column=2, padx=5, pady=5, sticky="e")
end_time_entry = tk.Entry(bottom_frame, width=10)
end_time_entry.grid(row=0, column=3, padx=5, pady=5)

# Row 1: Calculation Inputs
tk.Label(bottom_frame, text="Fluid:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
fluid_var = tk.StringVar(root)
fluid_var.set("Select Fluid")
fluid_menu = tk.OptionMenu(bottom_frame, fluid_var, *FLUID_DENSITIES.keys())
fluid_menu.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

tk.Label(bottom_frame, text="Ambient Pressure (Pa):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
p_ambient_entry = tk.Entry(bottom_frame, width=10)
p_ambient_entry.insert(0, "101325") # Default to 1 atm
p_ambient_entry.grid(row=1, column=3, padx=5, pady=5)

# Row 2: Calculation Button
calc_button = tk.Button(bottom_frame, text="Calculate Average CdA", command=calculate_cda, state=tk.DISABLED, bg="#D1ECF1")
calc_button.grid(row=2, column=0, columnspan=2, pady=10, padx=5, sticky="ew")

clear_marker_button = tk.Button(bottom_frame, text="Clear Plot Markers", command=clear_markers, bg="#F8D7DA")
clear_marker_button.grid(row=2, column=2, columnspan=2, pady=10, padx=5, sticky="ew")

# Row 3: Result Display
result_title_label = tk.Label(bottom_frame, text="Average CdA (m^2):")
result_title_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="e")

result_label = tk.Label(bottom_frame, text="N/A", font=("TkDefaultFont", 12, "bold"), relief=tk.SUNKEN, width=20)
result_label.grid(row=3, column=2, columnspan=2, padx=5, pady=5, sticky="w")

# Configure grid expansion
bottom_frame.grid_columnconfigure(1, weight=1)
bottom_frame.grid_columnconfigure(3, weight=1)

# --- Start GUI ---
root.mainloop()