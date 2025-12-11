
# context.py
class AnalyzerContext:
    """Holds shared data so every handler sees the same state."""
    def __init__(self):
        # Raw data
        self.df = None
        # Column names
        self.time_col = None
        self.thrust_cols = []
        self.chamber_col = None
        self.fuel_col = None
        self.oxidizer_col = None
        # Derived data
        self.of_ratio = None
        self.initial_mask = None
        self.data_mask = None
        # Metrics & misc
        self.metrics = {}
