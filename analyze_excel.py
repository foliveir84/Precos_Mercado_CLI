import pandas as pd
import os

files = ['ValorVendido.xlsx', 'UnidadesVendidas.xlsx']

for file in files:
    print(f"--- Analyzing {file} ---")
    if not os.path.exists(file):
        print(f"File {file} not found.")
        continue
        
    try:
        df = pd.read_excel(file)
        print("Columns:", df.columns.tolist())
        print("\nData Types:")
        print(df.dtypes)
        print("\nFirst 5 rows:")
        print(df.head().to_string())
        print("\nSummary Statistics:")
        print(df.describe().to_string())
        print("\n" + "="*30 + "\n")
    except Exception as e:
        print(f"Error reading {file}: {e}")
