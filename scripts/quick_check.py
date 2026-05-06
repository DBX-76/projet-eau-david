#!/usr/bin/env python3
# ============================================================================
# SCRIPT RAPIDE : Analyser les colonnes (version simplifiée)
# ============================================================================
# Exécution : python quick_check.py
# Objectif : Voir rapidement les colonnes sans tout télécharger
# ============================================================================

import requests
import zipfile
import io
import pandas as pd

# URL du ZIP
ZIP_URL = "https://www.data.gouv.fr/fr/datasets/r/7e38c236-dd3c-455e-a728-f0ecb84b1a7c"
ENCODING = 'iso-8859-1'
SEPARATOR = ','

print("\n" + "=" * 80)
print("ANALYSE RAPIDE DES COLONNES")
print("=" * 80)

try:
    print("\nTéléchargement du ZIP...")
    response = requests.get(ZIP_URL, timeout=60, allow_redirects=True)
    response.raise_for_status()

    file_size_mb = len(response.content) / 1024 / 1024
    print(f"Téléchargé : {file_size_mb:.2f} MB")

    # Analyser le ZIP
    zip_buffer = io.BytesIO(response.content)

    with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
        file_list = zip_ref.namelist()
        txt_files = [f for f in file_list if f.lower().endswith('.txt')]

        if not txt_files:
            print("Aucun fichier .txt trouvé")
            exit(1)

        print(f"\nFichiers .txt trouvés : {txt_files}")

        # Analyser le premier fichier seulement
        first_file = txt_files[0]
        print(f"\nAnalyse de : {first_file}")

        # Lire seulement les 10 premières lignes
        content = zip_ref.read(first_file)
        text = content.decode(ENCODING)
        lines = text.split('\n')[:10]  # 10 premières lignes

        if not lines:
            print("Fichier vide")
            exit(1)

        # Première ligne = en-têtes
        header_line = lines[0].strip()
        columns = header_line.split(SEPARATOR)

        print(f"\nCOLONNES ({len(columns)} colonnes) :")
        print("=" * 80)

        for i, col in enumerate(columns, 1):
            print(f"   {i:02d}. {col}")

        print("\n" + "=" * 80)
        print("ÉCHANTILLON DE DONNÉES :")
        print("=" * 80)

        for i in range(1, min(6, len(lines))):
            if lines[i].strip():
                data_cols = lines[i].strip().split(SEPARATOR)
                sample = " | ".join(data_cols[:10])
                print(f"   L{i}: {sample}")

        print("\n" + "=" * 80)
        print("ANALYSE TERMINÉE")
        print("=" * 80 + "\n")

except Exception as e:
    print(f"\nErreur : {e}")
    import traceback
    traceback.print_exc()
