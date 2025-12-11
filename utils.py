# utils.py
import tkinter as tk  # Import tkinter for GUI components
from tkinter import messagebox  # Import messagebox for displaying alerts
import numpy as np  # Import numpy for numerical operations
import pandas as pd  # Import pandas for data manipulation
import matplotlib.pyplot as plt  # Import matplotlib for plotting
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # Import for embedding matplotlib in tkinter

def infer_columns(app):
    """Infer basic columns in the loaded CSV, prompt if missing."""
    ctx = app.ctx  # Get the application context
    df = ctx.df  # Get the dataframe from the context
    columns = list(df.columns)  # Get the list of column names
    lower_cols = [c.lower().strip() for c in columns]  # Convert column names to lowercase and strip whitespace
    col_map = dict(zip(lower_cols, columns))  # Map lowercase column names to original names

    # Initialize context variables for column names
    ctx.time_col = None
    ctx.thrust_cols = []
    ctx.chamber_col = None
    ctx.fuel_col = None
    ctx.oxidizer_col = None

    # Infer the time column
    for key in ["time", "t"]:
        if key in col_map:
            ctx.time_col = col_map[key]
            break

    # Infer thrust columns
    for col in columns:
        if "thrust" in col.lower():
            ctx.thrust_cols.append(col)

    # Infer chamber pressure column
    for col in columns:
        if "chamber" in col.lower() and "press" in col.lower():
            ctx.chamber_col = col
            break

    # Infer optional tank weight columns
    for col in columns:
        if "fuel" in col.lower() and "weight" in col.lower():
            ctx.fuel_col = col
        if ("ox" in col.lower() or "oxidizer" in col.lower()) and "weight" in col.lower():
            ctx.oxidizer_col = col

    # If required columns are missing, prompt the user for manual selection
    if ctx.time_col is None or not ctx.thrust_cols:
        manual_column_selection(app, columns)

def manual_column_selection(app, columns):
    """Prompt the user to manually select columns with a scrollable interface."""
    ctx = app.ctx  # Get the application context
    small_font = ("Arial", 12)

    def set_columns():
        """Set the selected columns in the context."""
        ctx.time_col = time_var.get()  # Set the time column
        ctx.thrust_cols = [col for col, var in thrust_vars.items() if var.get()]  # Set the thrust columns
        ctx.chamber_col = chamber_var.get()  # Set the chamber pressure column
        ctx.fuel_col = fuel_var.get()  # Set the fuel weight column
        ctx.oxidizer_col = oxidizer_var.get()  # Set the oxidizer weight column
        win.destroy()  # Close the selection window

    # Create a new window for column selection
    win = tk.Toplevel(app)
    win.title("Select Columns")  # Set the window title
    win.geometry("600x700")  # Set the window size
    
    # Create main container frame
    main_frame = tk.Frame(win)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Create canvas with scrollbar for scrollable content
    canvas = tk.Canvas(main_frame)
    scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Enable mousewheel scrolling
    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    # Pack canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Dropdown for time column
    tk.Label(scrollable_frame, text="Time column:", font=small_font).pack(anchor="w", pady=(10, 2))
    time_var = tk.StringVar(value=ctx.time_col or columns[0])  # Default to the first column
    time_menu = tk.OptionMenu(scrollable_frame, time_var, *columns)
    time_menu.config(font=small_font)
    time_menu.pack(fill=tk.X, pady=(0, 10))

    # Checkboxes for thrust columns (in a labeled frame)
    thrust_frame = tk.LabelFrame(scrollable_frame, text="Thrust columns (select all that apply):", font=small_font)
    thrust_frame.pack(fill=tk.X, pady=10)
    
    thrust_vars = {c: tk.BooleanVar(value=c in ctx.thrust_cols) for c in columns}  # Create a checkbox for each column
    for c, var in thrust_vars.items():
        cb = tk.Checkbutton(thrust_frame, text=c, variable=var, font=("Arial", 10))
        cb.pack(anchor="w")

    # Dropdown for chamber pressure column
    tk.Label(scrollable_frame, text="Chamber pressure column:", font=small_font).pack(anchor="w", pady=(10, 2))
    chamber_var = tk.StringVar(value=ctx.chamber_col or columns[0])  # Default to the first column
    chamber_menu = tk.OptionMenu(scrollable_frame, chamber_var, *columns)
    chamber_menu.config(font=small_font)
    chamber_menu.pack(fill=tk.X, pady=(0, 10))

    # Dropdown for fuel weight column
    tk.Label(scrollable_frame, text="Fuel weight column:", font=small_font).pack(anchor="w", pady=(10, 2))
    fuel_var = tk.StringVar(value=ctx.fuel_col or "")  # Default to empty
    fuel_menu = tk.OptionMenu(scrollable_frame, fuel_var, "", *columns)
    fuel_menu.config(font=small_font)
    fuel_menu.pack(fill=tk.X, pady=(0, 10))

    # Dropdown for oxidizer weight column
    tk.Label(scrollable_frame, text="Oxidizer weight column:", font=small_font).pack(anchor="w", pady=(10, 2))
    oxidizer_var = tk.StringVar(value=ctx.oxidizer_col or "")  # Default to empty
    oxidizer_menu = tk.OptionMenu(scrollable_frame, oxidizer_var, "", *columns)
    oxidizer_menu.config(font=small_font)
    oxidizer_menu.pack(fill=tk.X, pady=(0, 10))
    
    # Unbind mousewheel when window closes to avoid errors
    def on_close():
        canvas.unbind_all("<MouseWheel>")
        win.destroy()

    # Confirm button - OUTSIDE the scrollable area so it's always visible
    button_frame = tk.Frame(win)
    button_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
    tk.Button(button_frame, text="Confirm", command=set_columns, font=("Arial", 14, "bold"), 
              bg="#4CAF50", fg="white", height=2).pack(fill=tk.X, padx=20)
    
    win.protocol("WM_DELETE_WINDOW", on_close)
    win.transient(app)  # Make the window modal
    win.grab_set()  # Prevent interaction with the main window
    app.wait_window(win)  # Wait for the window to close

def compute_metrics(app, target_thrust):
    """Compute metrics like burn time, total impulse, and average thrust."""
    ctx = app.ctx  # Get the application context
    if ctx.df is None or ctx.time_col is None or not ctx.thrust_cols:
        ctx.metrics = {"Error": "Missing data"}  # Set error if data is missing
        return
    time = ctx.df[ctx.time_col].values  # Get time values
    thrust_total = ctx.df[ctx.thrust_cols].sum(axis=1).values  # Sum thrust columns

    # --- Custom data splicing logic ---
    use_custom_splice = hasattr(app, "custom_splice_var") and app.custom_splice_var.get()
    if use_custom_splice and hasattr(app, "custom_splice_start") and hasattr(app, "custom_splice_end"):
        try:
            t_start = float(app.custom_splice_start.get())
            t_end = float(app.custom_splice_end.get())
            mask = (time >= t_start) & (time <= t_end)
        except Exception:
            ctx.metrics = {"Error": "Invalid custom splice time range."}
            ctx.data_mask = np.ones(len(ctx.df), dtype=bool)
            return
    else:
        # Define the thrust range for filtering
        lower, upper = 0.5 * target_thrust, 1.5 * target_thrust
        mask = (thrust_total >= lower) & (thrust_total <= upper)  # Create a mask for valid thrust values

    if not np.any(mask):  # Check if no data is in the valid range
        ctx.metrics = {"Error": "No data in selected window."}
        ctx.data_mask = np.ones(len(ctx.df), dtype=bool)  # Default to all data
        return

    ctx.initial_mask = mask.copy()  # Save the initial mask
    ctx.data_mask = mask  # Save the mask for later use
    start_idx = np.argmax(mask)  # Find the start index of the valid range
    end_idx = len(mask) - np.argmax(mask[::-1]) - 1  # Find the end index of the valid range

    # Extract the valid time and thrust slices
    t_slice = time[mask]
    thrust_slice = thrust_total[mask]
    burn_dur = t_slice[-1] - t_slice[0]  # Calculate burn duration
    total_impulse = float(np.trapz(thrust_slice, t_slice))  # Calculate total impulse
    avg_thrust = total_impulse / burn_dur if burn_dur > 0 else 0  # Calculate average thrust

    peak_press = None
    if ctx.chamber_col:  # Check if chamber pressure column exists
        peak_press = float(ctx.df[ctx.chamber_col].max())  # Get the peak chamber pressure

    # Calculate O/F ratio if fuel and oxidizer columns exist
    if ctx.fuel_col and ctx.oxidizer_col:
        fuel_w = ctx.df[ctx.fuel_col][mask].values  # Get fuel weight values
        ox_w = ctx.df[ctx.oxidizer_col][mask].values  # Get oxidizer weight values
        ctx.of_ratio = ox_w / (fuel_w + 1e-6)  # Calculate O/F ratio

    # Save computed metrics in the context
    ctx.metrics = {
        "Burn Time (s)": f"{burn_dur:.3f}",
        "Total Impulse (lbf·s)": f"{total_impulse:.2f}",
    }

def apply_extra_data(app):
    """Expand the data mask to include extra data points."""
    ctx = app.ctx  # Get the application context
    if ctx.initial_mask is None:  # Check if the initial mask is missing
        return slice(None)  # Return all data
    mask = ctx.initial_mask.copy()  # Copy the initial mask
    start_idx = np.argmax(mask)  # Find the start index of the valid range
    end_idx = len(mask) - np.argmax(mask[::-1]) - 1  # Find the end index of the valid range
    extra_frac = app.extra_data_slider.get() / 100  # Get the extra data fraction
    extra_pts = max(1, int(len(mask) * extra_frac))  # Calculate the number of extra points
    start_idx = max(0, start_idx - extra_pts)  # Expand the start index
    end_idx = min(len(mask) - 1, end_idx + extra_pts)  # Expand the end index
    mask[start_idx:end_idx+1] = True  # Update the mask to include extra points
    return mask

def create_plot_window(app, title, x, y, xlab, ylab, legend, color, fit=None):
    """Create a generic plot window with optional fit line."""
    import tkinter as tk  # Import tkinter for GUI components
    plot_win = tk.Toplevel(app)  # Create a new window
    plot_win.title(title)  # Set the window title
    plot_win.geometry("1200x900")  # Set the window size
    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)  # Create a matplotlib figure and axes
    ax.plot(x, y, label=legend, color=color)  # Plot the data
    if fit:  # Check if a fit line is provided
        m, b, lbl = fit  # Unpack the fit parameters
        ax.plot(x, m * x + b, linestyle="--", label=lbl, color="red")  # Plot the fit line
    ax.set_xlabel(xlab)  # Set the x-axis label
    ax.set_ylabel(ylab)  # Set the y-axis label
    ax.set_title(title)  # Set the plot title
    ax.legend()  # Add a legend
    canvas = FigureCanvasTkAgg(fig, master=plot_win)  # Embed the matplotlib figure in the tkinter window
    canvas.draw()  # Draw the canvas
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # Pack the canvas widget
    NavigationToolbar2Tk(canvas, plot_win).update()  # Add a navigation toolbar
