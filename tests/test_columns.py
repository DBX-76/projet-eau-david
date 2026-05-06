import pandas as pd
df = pd.read_csv("./data/clean/silver_clean_sample.csv", sep=';', encoding='iso-8859-1')
print("Colonnes :", df.columns.tolist())
print("\nColonnes avec 'commune' :", [c for c in df.columns if 'commune' in c.lower()])
print("\nColonnes avec 'param' :", [c for c in df.columns if 'param' in c.lower()])
print("\nPremiers parametres uniques :", df['nom_parametre'].unique()[:20] if 'nom_parametre' in df.columns else "N/A")
