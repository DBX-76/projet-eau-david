#!/usr/bin/env python3
# ============================================================================
# SCRIPT DE DIAGNOSTIC : Analyser le contenu du ZIP
# ============================================================================
# Exécution : python analyze_zip.py
# Objectif : Voir quels fichiers sont dans le ZIP et comment les parser
# ============================================================================

import requests
import zipfile
import io
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

def analyze_zip_content():
    """Analyse le contenu du fichier ZIP."""
    logger.info("\n" + "=" * 80)
    logger.info("ANALYSE DU CONTENU DU ZIP")
    logger.info("=" * 80)
    
    try:
        logger.info("\nTéléchargement du ZIP...")
        response = requests.get(ZIP_URL, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        
        file_size_mb = len(response.content) / 1024 / 1024
        logger.info(f"Téléchargé : {file_size_mb:.2f} MB")
        
        # Analyser le ZIP
        zip_buffer = io.BytesIO(response.content)
        
        logger.info("\nFichiers dans le ZIP :")
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            file_list = zip_ref.namelist()
            
            # Trier par extension
            extensions = {}
            for fname in file_list:
                ext = fname.split('.')[-1].lower()
                if ext not in extensions:
                    extensions[ext] = []
                extensions[ext].append(fname)
            
            # Afficher les fichiers par extension
            for ext in sorted(extensions.keys()):
                logger.info(f"\n  Fichiers .{ext} ({len(extensions[ext])} fichier(s)) :")
                for fname in extensions[ext]:
                    try:
                        file_info = zip_ref.getinfo(fname)
                        size_mb = file_info.file_size / 1024 / 1024
                        logger.info(f"     - {fname} ({size_mb:.2f} MB)")
                    except:
                        logger.info(f"     - {fname}")
            
            # Analyser le premier fichier
            logger.info("\n🔬 Analyse du premier fichier :")
            first_file = file_list[0]
            logger.info(f"   Fichier : {first_file}")
            
            try:
                content = zip_ref.read(first_file)
                
                # Détecter l'encodage
                try:
                    text = content.decode('utf-8')
                    detected_encoding = 'UTF-8'
                except:
                    try:
                        text = content.decode('iso-8859-1')
                        detected_encoding = 'ISO-8859-1'
                    except:
                        text = content.decode('cp1252')
                        detected_encoding = 'CP1252'
                
                logger.info(f"   Encodage détecté : {detected_encoding}")
                
                # Analyser les lignes
                lines = text.split('\n')
                logger.info(f"   Lignes totales : {len(lines)}")
                
                if lines:
                    # Première ligne (en-têtes)
                    header = lines[0]
                    logger.info(f"   En-têtes (première ligne) :")
                    logger.info(f"   {header[:100]}...")
                    
                    # Déterminer le séparateur
                    if ',' in header and ';' not in header:
                        sep = ','
                    elif ';' in header and ',' not in header:
                        sep = ';'
                    elif '\t' in header:
                        sep = '\t'
                    else:
                        sep = '?'
                    
                    logger.info(f"   Séparateur détecté : '{sep}'")
                    
                    # Compter les colonnes
                    cols = header.split(sep)
                    logger.info(f"   Colonnes : {len(cols)}")
                    logger.info(f"   Premiers champs : {cols[:5]}")
                    
                    # Deuxième ligne (données)
                    if len(lines) > 1:
                        logger.info(f"\n   Data (deuxième ligne) :")
                        logger.info(f"   {lines[1][:100]}...")
            
            except Exception as e:
                logger.error(f"   Erreur analyse : {e}")
        
        logger.info("\n" + "=" * 80)
        logger.info("ANALYSE TERMINÉE")
        logger.info("=" * 80 + "\n")
        
    except Exception as e:
        logger.error(f"\nErreur : {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_zip_content()
