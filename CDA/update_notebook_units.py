import json

notebook_path = 'CDA/CdACalc_Final.ipynb'

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# --- Update calculate_cda function ---
new_calculate_cda_source = [
    "def calculate_cda():\n",
    "    \"\"\"\n",
    "    Calculates the average CdA based on user inputs for time splice,\n",
    "    fluid density, and ambient pressure. Handles unit conversions and\n",
    "    mass flow rate calculation from weight if necessary.\n",
    "    \"\"\"\n",
    "    if df is None:\n",
    "        messagebox.showwarning(\"No Data\", \"Please load and plot data first.\")\n",
    "        return\n",
    "\n",
    "    # --- 1. Get Inputs ---\n",
    "    try:\n",
    "        start_time = float(start_time_entry.get())\n",
    "        end_time = float(end_time_entry.get())\n",
    "        p_ambient = float(p_ambient_entry.get())\n",
    "    except ValueError:\n",
    "        messagebox.showerror(\"Input Error\", \"Start Time, End Time, and Ambient Pressure must be numbers.\")\n",
    "        return\n",
    "\n",
    "    fluid_name = fluid_var.get()\n",
    "    density = FLUID_DENSITIES.get(fluid_name)\n",
    "    pressure_col = pressure_var.get()\n",
    "    mdot_col = mdot_var.get()\n",
    "    mdot_unit = mdot_unit_var.get()\n",
    "\n",
    "    # --- 2. Validate Inputs ---\n",
    "    if start_time >= end_time:\n",
    "        messagebox.showerror(\"Input Error\", \"Start Time must be less than End Time.\")\n",
    "        return\n",
    "        \n",
    "    if not density:\n",
    "        messagebox.showerror(\"Input Error\", \"Please select a valid fluid.\")\n",
    "        return\n",
    "\n",
    "    # --- 3. Splice Data ---\n",
    "    spliced_df = df[\n",
    "        (df[time_col_sec] >= start_time) & (df[time_col_sec] <= end_time)\n",
    "    ].copy() # Use .copy() to avoid SettingWithCopyWarning\n",
    "\n",
    "    if spliced_df.empty:\n",
    "        messagebox.showwarning(\"No Data\", \"No data found in the specified time range.\")\n",
    "        return\n",
    "\n",
    "    # --- 4. Calculate CdA ---\n",
    "    # Equation: mdot = CdA * sqrt(2 * rho * delta_p)\n",
    "    # Rearranged: CdA = mdot / sqrt(2 * rho * delta_p)\n",
    "    \n",
    "    try:\n",
    "        # --- 1. Calculate Average Pressure & Delta P ---\n",
    "        avg_pressure = spliced_df[pressure_col].mean()\n",
    "        \n",
    "        # Convert avg_pressure from PSI to Pa\n",
    "        avg_pressure_pa = avg_pressure * 6894.76\n",
    "        \n",
    "        # Check if input is Gauge or Absolute\n",
    "        if gauge_var.get():\n",
    "            # If Gauge, Delta P is just the pressure (assuming ambient is reference 0 for the gauge)\n",
    "            delta_p = avg_pressure_pa\n",
    "        else:\n",
    "            # If Absolute, Delta P = P_upstream_abs - P_ambient_abs\n",
    "            delta_p = avg_pressure_pa - p_ambient\n",
    "        \n",
    "        if delta_p <= 0:\n",
    "            messagebox.showwarning(\"Calculation Error\", \n",
    "                                   f\"Average pressure in range ({avg_pressure:.2f} PSI / {avg_pressure_pa:.2f} Pa) \"\n",
    "                                   f\"is not greater than ambient pressure ({p_ambient} Pa).\")\n",
    "            return\n",
    "\n",
    "        # --- 2. Calculate Mass Flow Rate (Mdot) ---\n",
    "        # Units: kg/s, lb/s, kg, lbs\n",
    "        \n",
    "        # Conversion factors\n",
    "        LB_TO_KG = 0.453592\n",
    "        \n",
    "        if mdot_unit in [\"kg\", \"lbs\"]:\n",
    "            # Cumulative Mass/Weight -> Calculate Slope (Derivative)\n",
    "            # We use linear regression (polyfit degree 1) to get the slope over the range\n",
    "            \n",
    "            # Get time and mass/weight arrays\n",
    "            t_data = spliced_df[time_col_sec].values\n",
    "            m_data = spliced_df[mdot_col].values\n",
    "            \n",
    "            if len(t_data) < 2:\n",
    "                 messagebox.showwarning(\"Calculation Error\", \"Not enough data points to calculate slope.\")\n",
    "                 return\n",
    "\n",
    "            # Calculate slope (units/sec)\n",
    "            slope, intercept = np.polyfit(t_data, m_data, 1)\n",
    "            \n",
    "            # Mass flow rate is the absolute value of the slope (assuming mass decreases)\n",
    "            raw_mdot = abs(slope)\n",
    "            \n",
    "            # Convert to kg/s if necessary\n",
    "            if mdot_unit == \"lbs\":\n",
    "                mdot_kg_s = raw_mdot * LB_TO_KG\n",
    "            else: # kg\n",
    "                mdot_kg_s = raw_mdot\n",
    "                \n",
    "        else: # \"kg/s\" or \"lb/s\"\n",
    "            # Rate -> Calculate Mean\n",
    "            raw_mdot = spliced_df[mdot_col].mean()\n",
    "            raw_mdot = abs(raw_mdot) # Ensure positive\n",
    "            \n",
    "            # Convert to kg/s if necessary\n",
    "            if mdot_unit == \"lb/s\":\n",
    "                mdot_kg_s = raw_mdot * LB_TO_KG\n",
    "            else: # kg/s\n",
    "                mdot_kg_s = raw_mdot\n",
    "        \n",
    "        if mdot_kg_s == 0:\n",
    "            messagebox.showwarning(\"Calculation Error\", \"Calculated Mass Flow Rate is 0.\")\n",
    "            return\n",
    "\n",
    "        # --- 3. Calculate Final CdA ---\n",
    "        # CdA = mdot / sqrt(2 * rho * delta_p)\n",
    "        denominator = np.sqrt(2 * density * delta_p)\n",
    "        \n",
    "        if denominator == 0:\n",
    "            messagebox.showwarning(\"Calculation Error\", \"Calculation denominator is zero (check density or delta_p).\")\n",
    "            return\n",
    "            \n",
    "        avg_cda = mdot_kg_s / denominator\n",
    "        \n",
    "        # Display the result\n",
    "        result_label.config(text=f\"{avg_cda:.5e} m^2\")\n",
    "        \n",
    "    except Exception as e:\n",
    "        messagebox.showerror(\"Calculation Error\", f\"An error occurred during calculation: {e}\")"
]

# Find the cell with calculate_cda and replace it
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "def calculate_cda():" in source:
            cell['source'] = new_calculate_cda_source
            break

# --- Update GUI Setup to add Mdot Unit Dropdown ---
# We need to find the GUI setup cell and inject the new dropdown code
# We'll look for where mdot_menu is defined and add the unit menu after it.

gui_setup_cell = None
for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = "".join(cell['source'])
        if "# --- GUI Setup ---" in source:
            gui_setup_cell = cell
            break

if gui_setup_cell:
    source_lines = gui_setup_cell['source']
    new_source_lines = []
    
    for line in source_lines:
        new_source_lines.append(line)
        # Insert unit dropdown after mdot_menu grid
        if "mdot_menu.grid(row=2, column=2, padx=5, sticky=\"ew\")" in line:
             new_source_lines.append("\n")
             new_source_lines.append("# Row 2.5: Mdot/Weight Unit Selection\n")
             new_source_lines.append("tk.Label(top_frame, text=\"Mdot/Weight Unit:\").grid(row=1, column=3, padx=5, sticky=\"e\")\n")
             new_source_lines.append("mdot_unit_var = tk.StringVar(gui)\n")
             new_source_lines.append("mdot_unit_var.set(\"kg/s\") # Default\n")
             new_source_lines.append("mdot_unit_menu = tk.OptionMenu(top_frame, mdot_unit_var, \"kg/s\", \"lb/s\", \"kg\", \"lbs\")\n")
             new_source_lines.append("mdot_unit_menu.grid(row=2, column=3, padx=5, sticky=\"ew\")\n")
             new_source_lines.append("\n")
             new_source_lines.append("# Update column configure to handle 4th column\n")
             new_source_lines.append("top_frame.grid_columnconfigure(3, weight=1)\n")

    # Remove the old column configure lines to avoid duplicates/conflicts if we just appended
    # Actually, simpler to just replace the whole block if we can identify it, but insertion is safer.
    # Let's filter out the old column configures if they exist in the new list to be clean?
    # The old ones were:
    # top_frame.grid_columnconfigure(0, weight=1)
    # top_frame.grid_columnconfigure(1, weight=1)
    # top_frame.grid_columnconfigure(2, weight=1)
    
    # We added column 3 config. The old ones are fine.
    
    # However, we need to make sure the plot button spans all columns now.
    # Old: plot_button.grid(row=3, column=0, columnspan=3, ...)
    # New: plot_button.grid(row=3, column=0, columnspan=4, ...)
    
    final_source_lines = []
    for line in new_source_lines:
        if "plot_button.grid(row=3, column=0, columnspan=3" in line:
            final_source_lines.append(line.replace("columnspan=3", "columnspan=4"))
        else:
            final_source_lines.append(line)
            
    gui_setup_cell['source'] = final_source_lines

with open(notebook_path, 'w') as f:
    json.dump(nb, f, indent=1)

print("Notebook updated successfully.")
