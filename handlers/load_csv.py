
# handlers/load_csv.py
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
from utils import infer_columns, compute_metrics

def run(app):
    ctx = app.ctx
    path = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if not path:
        return
    try:
        ctx.df = pd.read_csv(path, low_memory=False)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load: {e}")
        return

    infer_columns(app)

    tgt = simpledialog.askfloat("Target Thrust", "Enter expected target thrust (lbf):", parent=app)
    if tgt is None:
        return
    ctx.last_target_thrust = tgt  
    compute_metrics(app, tgt)
    # update GUI
    app.file_label.config(text=f"Loaded: {path.split('/')[-1]}", fg="black")
    app.display_metrics()
