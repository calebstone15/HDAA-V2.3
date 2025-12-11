
# handlers/generate_all.py
from tkinter import messagebox
from handlers import (plot_c_star, plot_isp, plot_thrust, plot_chamber_pressure, plot_of_ratio,
                      plot_fuel_weight, plot_oxidizer_weight, plot_ve_from_isp)

def run(app):
    ctx = app.ctx
    if ctx.df is None:
        messagebox.showerror("Error", "Load data first.")
        return
    # call each plot handler
    for fn in [plot_thrust, plot_chamber_pressure, plot_of_ratio,
               plot_fuel_weight, plot_oxidizer_weight, plot_c_star, plot_isp, plot_ve_from_isp]:
        try:
            fn.run(app)
        except Exception as e:
            print("Skipped plot:", e)
