import pandas as pd
import os

print("\n" + "=" * 80)
print("DIAGNOSTIC DU FICHIER SILVER")
print("=" * 80)

silver_path = "./data/clean/silver_clean.csv"

if not os.path.exists(silver_path):
    print(f"Fichier non trouvé : {silver_path}")
    exit(1)

print(f"\n📂 Chargement : {silver_path}")
df = pd.read_csv(silver_path, sep=';', encoding='iso-8859-1', nrows=1000)

print(f"Chargé : {len(df)} lignes × {len(df.columns)} colonnes")

# ============================================================================
# 1. COLONNES DISPONIBLES
# ============================================================================
print("\n" + "=" * 80)
print("1️⃣ TOUTES LES COLONNES DISPONIBLES :")
print("=" * 80)
for i, col in enumerate(df.columns, 1):
    non_null = df[col].notna().sum()
    null_pct = (1 - non_null / len(df)) * 100
    print(f"{i:2d}. {col:30s} | Non-nulls: {non_null:6d} ({100-null_pct:5.1f}%) | Uniques: {df[col].nunique():6d}")

# ============================================================================
# 2. COLONNES CONTENANT "COMMUNE"
# ============================================================================
print("\n" + "=" * 80)
print("2️⃣ COLONNES CONTENANT 'COMMUNE' :")
print("=" * 80)
cols_commune = [c for c in df.columns if 'commune' in c.lower()]
if cols_commune:
    for col in cols_commune:
        print(f"\n📍 Colonne : {col}")
        print(f"   Non-nulls: {df[col].notna().sum()} / {len(df)}")
        print(f"   Uniques: {df[col].nunique()}")
        print(f"   Exemples :")
        for val in df[col].dropna().unique()[:5]:
            print(f"      - '{val}'")
else:
    print("Aucune colonne avec 'commune'")

# ============================================================================
# 3. COLONNES CONTENANT "PARAMETRE" OU "NOM" (POUR LES PARAMÈTRES)
# ============================================================================
print("\n" + "=" * 80)
print("3️⃣ COLONNES PARAMÈTRES (contenant 'parametre', 'param', 'code_param') :")
print("=" * 80)
cols_param = [c for c in df.columns if any(x in c.lower() for x in ['parametre', 'param', 'code_param'])]
if cols_param:
    for col in cols_param:
        print(f"\n🧪 Colonne : {col}")
        print(f"   Non-nulls: {df[col].notna().sum()} / {len(df)}")
        print(f"   Uniques: {df[col].nunique()}")
        print(f"   Premiers 20 uniques :")
        for val in sorted(df[col].dropna().unique())[:20]:
            print(f"      - '{val}'")
        
        # Chercher "Nitrate" / "NITRATE" / "NO3"
        print(f"\n   🔎 Recherche 'NITRATE' / 'Nitrate' / 'NO3' :")
        nitrate_variants = df[df[col].str.contains('NITRATE|Nitrate|NO3|nitrate', case=False, na=False)][col].unique()
        if len(nitrate_variants) > 0:
            for val in nitrate_variants[:10]:
                print(f"      '{val}'")
        else:
            print(f"      Aucun enregistrement trouvé")
else:
    print("Aucune colonne paramètre trouvée")

# ============================================================================
# 4. COLONNES CONTENANT "RESULTAT" (POUR LES VALEURS MESURÉES)
# ============================================================================
print("\n" + "=" * 80)
print("4️⃣ COLONNES RÉSULTATS/VALEURS :")
print("=" * 80)
cols_resultat = [c for c in df.columns if 'resultat' in c.lower() or 'valeur' in c.lower()]
if cols_resultat:
    for col in cols_resultat:
        print(f"\nColonne : {col}")
        print(f"   Type: {df[col].dtype}")
        print(f"   Non-nulls: {df[col].notna().sum()} / {len(df)}")
        print(f"   Stats : min={df[col].min()}, max={df[col].max()}, mean={df[col].mean():.2f}")
else:
    print("Aucune colonne résultat trouvée")

# ============================================================================
# 5. COLONNES CONTENANT "DATE"
# ============================================================================
print("\n" + "=" * 80)
print("5️⃣ COLONNES DATES :")
print("=" * 80)
cols_date = [c for c in df.columns if 'date' in c.lower()]
if cols_date:
    for col in cols_date:
        print(f"\n📅 Colonne : {col}")
        print(f"   Type: {df[col].dtype}")
        print(f"   Non-nulls: {df[col].notna().sum()} / {len(df)}")
        print(f"   Exemples : {df[col].dropna().unique()[:3].tolist()}")
else:
    print("Aucune colonne date trouvée")

# ============================================================================
# 6. COLONNES CONTENANT "DEPT" OU "CODE" GÉOGRAPHIQUE
# ============================================================================
print("\n" + "=" * 80)
print("6️⃣ COLONNES GÉOGRAPHIQUES (dept/région/code) :")
print("=" * 80)
cols_geo = [c for c in df.columns if any(x in c.lower() for x in ['dept', 'departement', 'code_', 'reseau', 'region'])]
if cols_geo:
    for col in cols_geo:
        print(f"\n🗺️ Colonne : {col}")
        print(f"   Non-nulls: {df[col].notna().sum()} / {len(df)}")
        print(f"   Uniques: {df[col].nunique()}")
        print(f"   Exemples :")
        for val in df[col].dropna().unique()[:5]:
            print(f"      - '{val}'")
else:
    print("Aucune colonne géographique trouvée")

# ============================================================================
# 7. APERÇU GLOBAL
# ============================================================================
print("\n" + "=" * 80)
print("7️⃣ APERÇU GLOBAL (premières lignes) :")
print("=" * 80)
print(df.head(3).to_string())

print("\n" + "=" * 80)
print("DIAGNOSTIC TERMINÉ")
print("=" * 80 + "\n")
