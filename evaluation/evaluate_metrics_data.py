import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

con = sqlite3.connect('data/rota_operations.db')
df = pd.read_sql_query("SELECT metric_name, metric_value, run_id FROM evaluation_metrics", con)

pivot = df.pivot_table(index='metric_name', columns='run_id', values='metric_value')
pivot.loc[['qualification_match_accuracy','on_time_completion_rate','avg_travel_minutes']].plot(kind='bar')
plt.ylabel('Value')
plt.title('Baseline vs AI/Core Comparisons')
plt.tight_layout()
plt.show()