#!/usr/bin/env python3
# ============================================================================
# SCRIPT : Analyser les colonnes réelles des données
# ============================================================================
# Exécution : python check_columns.py
# Objectif : Voir les vraies colonnes et proposer le mapping
# ============================================================================

import requests
import zipfile
import io
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# URL du ZIP
ZIP_URL = "https://www.data.gouv.fr/fr/datasets/r/7e38c236-dd3c-455e-a728-f0ecb84b1a7c"
TIMEOUT = 300
ENCODING = 'iso-8859-1'
SEPARATOR = ','

def analyze_columns():
    """Analyse les colonnes réelles des données."""
    logger.info("\n" + "=" * 80)
        logger.info("ANALYSE DES COLONNES RÉELLES")
    logger.info("=" * 80)
    
    try:
        logger.info("\nTéléchargement du ZIP...")
        response = requests.get(ZIP_URL, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        file_size_mb = len(response.content) / 1024 / 1024
        logger.info(f"Téléchargé : {file_size_mb:.2f} MB")
        
        # Analyser le ZIP
        zip_buffer = io.BytesIO(response.content)
        
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            txt_files = [f for f in file_list if f.lower().endswith('.txt')]
            
            if not txt_files:
                logger.error("Aucun fichier .txt trouvé")
                return
            
            # Analyser le premier fichier
            first_file = txt_files[0]
            logger.info(f"\nAnalyse du fichier : {first_file}")
            
            content = zip_ref.read(first_file)
            text = content.decode(ENCODING)
            lines = text.split('\n')
            
            if not lines:
                logger.error("Fichier vide")
                return
            
            # Première ligne = en-têtes
            header_line = lines[0].strip()
            columns = header_line.split(SEPARATOR)
            
            logger.info(f"\nCOLONNES DÉTECTÉES ({len(columns)} colonnes) :")
            logger.info("=" * 80)
            
            for i, col in enumerate(columns, 1):
                logger.info("2d")
            
            logger.info("\n" + "=" * 80)
            
            # Analyser quelques lignes de données
            logger.info("ÉCHANTILLON DE DONNÉES :")
            logger.info("=" * 80)
            
            for i in range(1, min(6, len(lines))):
                if lines[i].strip():
                    data_cols = lines[i].strip().split(SEPARATOR)
                    logger.info("2d")
            
            logger.info("\n" + "=" * 80)
            
            # Proposer un mapping
            logger.info("🔄 MAPPING PROPOSÉ (vers noms standardisés) :")
            logger.info("=" * 80)
            
            # Mapping basé sur les colonnes typiques des données eau
            mapping_suggestions = {
                # Géospatial
                'latitude': ['latitude', 'lat', 'y_wgs84', 'coord_y'],
                'longitude': ['longitude', 'lon', 'x_wgs84', 'coord_x'],
                'commune_code': ['code_commune', 'insee', 'code_insee', 'commune'],
                'commune_name': ['nom_commune', 'commune', 'libelle_commune'],
                
                # Temporel
                'date_prelevement': ['date_prelevement', 'date', 'date_prelev', 'date_obs'],
                
                # Paramètres
                'parametre': ['parametre', 'libelle_parametre', 'param', 'parameter'],
                'resultat': ['resultat', 'valeur', 'value', 'mesure'],
                'unite': ['unite', 'unit', 'symbole_unite'],
                
                # Métadonnées
                'laboratoire': ['laboratoire', 'labo', 'nom_laboratoire'],
                'station_id': ['code_station', 'station', 'id_station', 'numero_station'],
                'source': ['source', 'origine'],
            }
            
            for standard_name, possible_names in mapping_suggestions.items():
                found = None
                for col in columns:
                    col_lower = col.lower().strip()
                    if any(poss.lower() in col_lower or col_lower in poss.lower() for poss in possible_names):
                        found = col
                        break
                
                if found:
                    logger.info(f"{standard_name:<20} ← '{found}'")
                else:
                    logger.info(f"{standard_name:<20} ← ??? (pas trouvé)")
            
            logger.info("\n" + "=" * 80)
            logger.info("💡 PROCHAINES ÉTAPES :")
            logger.info("1. Copiez le mapping ci-dessus dans le code")
            logger.info("2. Ajoutez df.rename(columns=mapping) après le chargement")
            logger.info("3. Testez à nouveau l'ingestion")
            logger.info("=" * 80 + "\n")
            
    except Exception as e:
        logger.error(f"\nErreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_columns()
