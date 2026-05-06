"""
Module Bronze - Ingestion et extraction des données brutes

Responsabilités :
- Télécharger les fichiers ZIP depuis data.gouv.fr
- Extraire et parser les fichiers TXT
- Appliquer les mappages de colonnes spécifiques au type de fichier
- Fusionner les données en une table unique
"""

# À importer depuis notebooks/01_ingestion_bronze.py
# Cette structure permet l'import : from eau.bronze import load_bronze_data
