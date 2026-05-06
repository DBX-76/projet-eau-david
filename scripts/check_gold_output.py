#!/usr/bin/env python3
"""
Script de validation des fichiers Gold générés
"""
import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

GOLD_PATH = "./data/gold"

files = [
    "gold_global_kpis.csv",
    "gold_departments_pollution.csv", 
    "gold_communes_top10_best.csv",
    "gold_communes_top10_worst.csv",
    "gold_critical_parameters.csv"
]

logger.info("=" * 80)
logger.info("📊 VALIDATION DES FICHIERS GOLD")
logger.info("=" * 80)

for filename in files:
    filepath = os.path.join(GOLD_PATH, filename)
    
    if not os.path.exists(filepath):
        logger.warning(f"❌ {filename} — MANQUANT")
        continue
    
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    logger.info(f"\n📄 {filename} ({size_mb:.2f} MB)")
    
    try:
        df = pd.read_csv(filepath, sep=";")
        logger.info(f"   Dimensions : {df.shape[0]} lignes × {df.shape[1]} colonnes")
        logger.info(f"   Colonnes   : {', '.join(df.columns[:5].tolist())}")
        
        # Aperçu des données
        if df.shape[0] > 0:
            logger.info(f"\n   📋 Aperçu :")
            for idx, row in df.head(3).iterrows():
                logger.info(f"      {row.to_dict()}")
        
    except Exception as e:
        logger.error(f"   ❌ Erreur lecture : {e}")

logger.info("\n" + "=" * 80)
logger.info("✅ VALIDATION TERMINÉE")
logger.info("=" * 80)
