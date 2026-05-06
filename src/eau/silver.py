"""
Module Silver - Nettoyage, validation et enrichissement

Responsabilités :
- Charger et reconstruire les données Bronze via jointures
- Nettoyer (dates, types, encodages)
- Dédupliquer sur clés métier
- Valider avec Great Expectations v0.18+
- Enrichir (record_id, quality_flag)
"""

# À importer depuis notebooks/02_transformation_silver.py
