import pandas as pd

MM_CITRIC = 192.12  # g/mol

df = pd.read_csv("citric_pH_synthetic_600.csv")

df["citric_g_per_L"] = df["citric_conc_M"] * MM_CITRIC
df["citric_percent_wv"] = df["citric_g_per_L"] / 10.0  # g per 100 mL

df.to_csv("citric_pH_synthetic_600_with_percent.csv", index=False)
print(df.head())
