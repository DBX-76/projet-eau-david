# 📓 Notebooks du Pipeline

Ce dossier contient les **notebooks Python** du pipeline de données qualité eau.

## 📋 Structure

### `local_pipeline/`
Notebooks d'exploration et développement utilisés localement :

- `01_ingestion_bronze.py` : Ingestion des données brutes depuis data.gouv.fr
- `02_transformation_silver.py` : Nettoyage, validation et transformation (Great Expectations)
- `03_aggregation_gold.py` : Agrégations métier et KPIs

### `databricks_pipeline/`
Notebooks de production déployés sur Databricks (exportés depuis l'interface) :

- `01_ingestion_bronze.py` : Pipeline Bronze en environnement cloud
- `02_transformation_silver.py` : Pipeline Silver avec validation GX
- `03_aggregation_gold.py` : Pipeline Gold avec sauvegarde Delta

---

**Note** : Les notebooks `local_pipeline/` servent au développement, tandis que `databricks_pipeline/` contient le code de production optimisé pour Spark.