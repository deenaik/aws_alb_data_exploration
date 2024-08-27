from pathlib import Path

import pandas as pd

app_data = Path(__file__).parent
df = pd.read_csv(app_data / 'sk_log_week_34.csv')
# df = pd.read_csv(app_data / 'sample_data.csv')
