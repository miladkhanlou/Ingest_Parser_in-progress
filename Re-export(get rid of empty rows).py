import pandas as pd
df = pd.read_csv("lsu-metadata.csv")
print(df.head())
df.to_csv("new.csv", index = 0)