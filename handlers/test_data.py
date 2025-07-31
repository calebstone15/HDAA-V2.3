
# handlers/test_data.py
from utils import create_plot_window
def run(app):
    ctx = app.ctx
    if ctx.df is None or ctx.time_col is None or not ctx.thrust_cols:
        return
    time = ctx.df[ctx.time_col].values
    thrust = ctx.df[ctx.thrust_cols].sum(axis=1).values
    create_plot_window(app, "Test Data: Total Thrust", time, thrust,
                       "Time (s)", "Thrust (lbf)", "Total Thrust", "blue")
