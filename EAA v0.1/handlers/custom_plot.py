# handlers/custom_plot.py
"""
Interactive “mix-and-match” plot builder
– now with beefy error handling.
"""

import tkinter as tk
from tkinter import messagebox
import traceback
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from utils import apply_extra_data


# ---------- small helpers ----------
def _extract_unit(name: str):
    if "(" in name and ")" in name:
        return name[name.find("(") + 1 : name.find(")")]
    return None


def _pick_columns(app):
    """Modal checkbox picker → list[str]"""
    ctx = app.ctx
    chosen = []

    win = tk.Toplevel(app)
    win.title("Select Columns")
    win.geometry("600x800")

    tk.Label(win, text="Pick columns to plot:").pack(anchor="w", pady=6)

    vars_ = {c: tk.BooleanVar() for c in ctx.df.columns}
    # generated
    if ctx.thrust_cols:
        vars_["Thrust (lbf)"] = tk.BooleanVar()
    if ctx.chamber_col:
        vars_["Chamber Pressure (psi)"] = tk.BooleanVar()
    if ctx.of_ratio is not None:
        vars_["O/F Ratio"] = tk.BooleanVar()

    for c, var in vars_.items():
        tk.Checkbutton(win, text=c, variable=var).pack(anchor="w")

    def done():
        nonlocal chosen
        chosen = [c for c, v in vars_.items() if v.get()]
        win.destroy()

    tk.Button(win, text="Confirm", command=done).pack(pady=10)
    win.transient(app)
    win.grab_set()
    app.wait_window(win)
    return chosen


def _pick_display_opts(app, cols):
    """Modal option-menu picker → {col: ("Raw"|"Smoothed"|"Both")}"""
    opts = {c: tk.StringVar(value="Raw") for c in cols}

    win = tk.Toplevel(app)
    win.title("Display Options")
    win.geometry("400x600")

    tk.Label(win, text="Choose display type for each column").pack(anchor="w", pady=6)

    for c in cols:
        f = tk.Frame(win)
        f.pack(anchor="w", padx=6, pady=2)
        tk.Label(f, text=c, width=28, anchor="w").pack(side=tk.LEFT)
        tk.OptionMenu(f, opts[c], "Raw", "Smoothed", "Both").pack(side=tk.LEFT)

    tk.Button(win, text="Confirm", command=win.destroy).pack(pady=8)
    win.transient(app)
    win.grab_set()
    app.wait_window(win)
    return {c: v.get() for c, v in opts.items()}


def _prompt_constant_lines(app, unit_groups):
    """
    Prompts user to add optional constant lines for each unit group.
    Returns: {unit: [(title, value, color)]}
    """
    COLOR_CHOICES = [
        "gray", "red", "blue", "green", "orange", "purple", "black", "brown", "cyan", "magenta"
    ]
    result = {unit: [] for unit in unit_groups}

    win = tk.Toplevel(app)
    win.title("Add Constant Lines")
    win.geometry("540x700")

    frames = {}
    entries = {}

    def add_line(unit):
        f = frames[unit]
        row = tk.Frame(f)
        row.pack(anchor="w", pady=2)
        # Labels for each entry
        tk.Label(row, text="Name:").pack(side=tk.LEFT, padx=2)
        title_var = tk.StringVar()
        tk.Entry(row, textvariable=title_var, width=14).pack(side=tk.LEFT, padx=2)
        tk.Label(row, text="Value:").pack(side=tk.LEFT, padx=2)
        value_var = tk.StringVar()
        tk.Entry(row, textvariable=value_var, width=8).pack(side=tk.LEFT, padx=2)
        tk.Label(row, text="Color:").pack(side=tk.LEFT, padx=2)
        color_var = tk.StringVar(value=COLOR_CHOICES[0])
        tk.OptionMenu(row, color_var, *COLOR_CHOICES).pack(side=tk.LEFT, padx=2)
        entries[unit].append((title_var, value_var, color_var))

    for unit in unit_groups:
        lf = tk.LabelFrame(win, text=f"Unit: {unit or 'No Unit'}")
        lf.pack(fill="x", padx=8, pady=6)
        frames[unit] = tk.Frame(lf)
        frames[unit].pack(anchor="w")
        entries[unit] = []
        tk.Button(lf, text="Add Constant Line", command=lambda u=unit: add_line(u)).pack(anchor="w", pady=2)

    def confirm():
        for unit in unit_groups:
            for title_var, value_var, color_var in entries[unit]:
                title = title_var.get().strip()
                value = value_var.get().strip()
                color = color_var.get().strip()
                if title and value:
                    try:
                        val = float(value)
                        result[unit].append((title, val, color))
                    except ValueError:
                        continue  # skip invalid
        win.destroy()

    tk.Button(win, text="Confirm", command=confirm).pack(pady=10)
    win.transient(app)
    win.grab_set()
    app.wait_window(win)
    return result


def _prompt_plot_title(app, default_title="Custom Plot"):
    """
    Prompts the user to enter a plot title.
    Returns the title as a string.
    """
    result = {"title": default_title}

    win = tk.Toplevel(app)
    win.title("Set Plot Title")
    win.geometry("400x150")

    tk.Label(win, text="Enter plot title:").pack(pady=10)
    title_var = tk.StringVar(value=default_title)
    entry = tk.Entry(win, textvariable=title_var, width=40)
    entry.pack(pady=5)
    entry.focus_set()

    def confirm():
        result["title"] = title_var.get().strip() or default_title
        win.destroy()

    tk.Button(win, text="Confirm", command=confirm).pack(pady=10)
    win.transient(app)
    win.grab_set()
    app.wait_window(win)
    return result["title"]


# ---------- main entry ----------
def run(app):
    try:
        _run_inner(app)
    except Exception as e:
        # show traceback so you see what went wrong
        tb = traceback.format_exc()
        print(tb)
        messagebox.showerror("Custom Plot Error", tb)


def _run_inner(app):
    ctx = app.ctx
    if ctx.df is None:
        messagebox.showerror("Error", "Load a CSV first.")
        return

    cols = _pick_columns(app)
    if not cols:
        messagebox.showinfo("Info", "No columns selected.")
        return

    # Prompt for plot title after columns are selected
    plot_title = _prompt_plot_title(app, default_title="Custom Plot")

    disp_opts = _pick_display_opts(app, cols)

    # ------------ prep data ------------
    mask = apply_extra_data(app)
    ds = max(app.downsampling_slider.get(), 1)
    time = ctx.df[ctx.time_col][mask].iloc[::ds]

    # Prepare generated data if selected
    generated = {
        "Thrust (lbf)": ctx.df[ctx.thrust_cols].sum(axis=1)
        if ctx.thrust_cols
        else None,
        "Chamber Pressure (psi)": ctx.df[ctx.chamber_col]
        if ctx.chamber_col
        else None,
        "O/F Ratio": (
            pd.Series(ctx.of_ratio, index=ctx.df.index[:len(ctx.of_ratio)])
            .reindex(ctx.df.index)  # Ensure alignment with the full DataFrame index
            .loc[mask]  # Apply the mask
            .iloc[::ds]  # Downsample
            if ctx.of_ratio is not None and len(ctx.of_ratio) > 0
            else None
        ),
    }

    # Debugging: Check generated data
    for key, series in generated.items():
        if series is not None:
            print(f"Generated series '{key}': {series.describe()}")
        else:
            print(f"Generated series '{key}' is None.")

    # Debugging: Check mask alignment
    print(f"Mask length: {len(mask)}, DataFrame length: {len(ctx.df)}")
    print(f"Mask true count: {mask.sum()}")

    # group by units
    unit_groups = {}
    for col in cols:
        unit_groups.setdefault(_extract_unit(col), []).append(col)

    # Prompt for constant lines
    constant_lines = _prompt_constant_lines(app, unit_groups)

    # ------------ build plot window ------------
    plot_win = tk.Toplevel(app)
    plot_win.title(plot_title)
    plot_win.geometry("1200x900")

    fig, ax0 = plt.subplots(figsize=(12, 6), dpi=100)
    canvas = FigureCanvasTkAgg(fig, master=plot_win)
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    NavigationToolbar2Tk(canvas, plot_win).update()

    palette = list(plt.cm.tab10.colors)
    color_for = {c: palette[i % len(palette)] for i, c in enumerate(cols)}

    plotted_any = False
    for idx, (unit, unit_cols) in enumerate(unit_groups.items()):
        ax = ax0 if idx == 0 else ax0.twinx()
        if idx > 0:
            ax.spines["right"].set_position(("axes", 1 + 0.1 * (idx - 1)))
        ax.set_ylabel(unit or "Value")

        # Draw constant lines for this unit (dashed, user-selected color)
        for title, value, color in constant_lines.get(unit, []):
            ax.axhline(value, linestyle="--", color=color, linewidth=1, alpha=0.8)
            ax.text(
                time.iloc[0] if len(time) else 0,
                value,
                f"{title} ({value})",
                va="bottom",
                ha="left",
                fontsize=9,
                color=color,
                backgroundcolor="white",
                alpha=0.7,
            )

        for col in unit_cols:
            raw_series = (
                ctx.df[col] if col in ctx.df.columns else generated.get(col)
            )
            if raw_series is None:
                continue  # skip missing

            # Align mask with raw_series length
            aligned_mask = mask[:len(raw_series)]

            # Debugging: Check raw_series and aligned_mask
            print(f"Column '{col}' raw_series length: {len(raw_series)}")
            print(f"Aligned mask length: {len(aligned_mask)}")
            print(f"Aligned mask true count: {aligned_mask.sum()}")

            raw_series = raw_series[aligned_mask].iloc[::ds]

            if raw_series.empty:
                print(f"Column '{col}' resulted in an empty series after masking and downsampling.")
                continue

            opt = disp_opts[col]
            c = color_for[col]

            if opt in ("Raw", "Both"):
                ax.plot(time, raw_series, label=f"{col} (Raw)", color=c,
                        alpha=0.35 if opt == "Both" else 1)
            if opt in ("Smoothed", "Both"):
                sm = raw_series.rolling(window=10, center=True).mean()
                ax.plot(time, sm, label=f"{col} (Smoothed)", color=c, linewidth=2)

            plotted_any = True

        ax.legend(loc="upper right" if idx else "upper left")

    if not plotted_any:
        plot_win.destroy()
        messagebox.showwarning("Nothing to plot", "All selected series were empty.")
        return

    ax0.set_xlabel("Time (s)")
    ax0.set_title(plot_title)
    fig.tight_layout()
    canvas.draw()
