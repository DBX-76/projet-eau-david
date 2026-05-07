# Documentation Technique — Projet Qualité d'Eau

---

## 1. Vue d'ensemble et contexte

### Objectif du projet

Implémenter une architecture de données de type médaillon (Bronze → Silver → Gold) pour transformer les données brutes de qualité d'eau issues de data.gouv.fr en indicateurs métier exploitables, avec validation qualité automatisée et exposition via API.

### Contraintes et adaptations

Le projet était initialement conçu pour être déployé sur Azure Databricks avec accès à Azure Data Lake Storage et SQL Endpoint. En l'absence d'accès Azure en temps utile, le projet a été migré vers Databricks Community Edition (gratuite), avec les ajustements techniques suivants :

- Remplacement d'ADLS Gen2 par DBFS / Unity Catalog Volumes
- Traitement ETL lourd réalisé en local (machine performante) pour la couche Silver (6,8 Go)
- Exposition API via FastAPI + fichier JSON (alternative au SQL Endpoint indisponible)

Cette contrainte a renforcé la compréhension des principes d'architecture découplée et de la portabilité des pipelines.

---

## 2. Architecture technique détaillée

### 2.1 Schéma global

```
[data.gouv.fr]
       ↓
[Machine locale — Python/Pandas]
       ├── Bronze : Ingestion, fusion, export CSV (13 M lignes)
       ├── Silver : Nettoyage, validation GX, enrichissement (12,5 M lignes)
       └── Gold   : Agrégations métier, export CSV (5 fichiers)
       ↓
[Databricks Community Edition]
       ├── 01_gold_delta_tables     : CSV → Tables Delta managées
       ├── 02_quality_validation    : Great Expectations sur tables Delta
       ├── 03_visualisation_export  : Dashboards HTML + JSON API
       └── Databricks Job           : Orchestration séquentielle des 3 notebooks
       ↓
[Exposition]
       ├── FastAPI (localhost)  : Endpoints REST /api/kpis, /api/departments…
       ├── Swagger UI           : Documentation interactive à /docs
       └── exports/             : Fichiers HTML/JSON téléchargeables
```

### 2.2 Paramétrage par composant

#### Pipeline local (Bronze / Silver / Gold)

| Composant | Fichier | Paramètres clés | Sortie |
|-----------|---------|-----------------|--------|
| Bronze | `notebooks/01_ingestion_bronze.py` | `DATA_GOUV_URL`, `SEPARATOR=';'`, `ENCODING='iso-8859-1'` | `bronze_combined.csv` (13 M lignes) |
| Silver | `notebooks/02_transformation_silver.py` | `GX_CONTEXT_TYPE='ephemeral'`, `QUALITY_RULES=9`, `DEDUP_KEYS=['id_prelevement','code_parametre']` | `silver_clean.csv` (12,5 M lignes, 55 colonnes) |
| Gold | `notebooks/03_aggregation_gold.py` | `AGGREGATIONS=['global_kpis','departements','communes_top10','critical_params']` | 5 fichiers CSV dans `data/gold/` |

#### Pipeline Databricks (Gold uniquement)

| Notebook | Chemin Databricks | Paramètres critiques | Action |
|----------|-------------------|----------------------|--------|
| 01_gold_delta_tables | `/Workspace/projet-eau/01_gold_delta_tables` | `BASE_PATH='/Volumes/workspace/default/eau/gold/'`, `overwriteSchema=true` | Chargement CSV → Tables Delta managées |
| 02_quality_validation | `/Workspace/projet-eau/02_quality_validation` | `GE_VERSION='1.17+'`, `VALIDATION_RULES` par table, `EXPORT_PATH` | Exécution Great Expectations + rapport JSON |
| 03_visualisation_export | `/Workspace/projet-eau/03_visualisation_export` | `EXPORT_PATH='/Volumes/.../exports/'`, `include_plotlyjs='cdn'` | Dashboards HTML + `api_exposition.json` |

#### Orchestration Databricks Job

L'exécution séquentielle des trois notebooks est pilotée via l'interface **Workflows > Jobs** de Databricks, nativement disponible sur la version Community Edition. Le pipeline est configuré avec des dépendances strictes entre les tâches :

| Tâche | Notebook | Dépendance |
|-------|----------|------------|
| `1` | `01_gold_delta_tables` | Aucune (exécution initiale) |
| `2` | `02_quality_validation` | Succès de la tâche 1 |
| `3` | `03_visualisation_export` | Succès de la tâche 2 |

Cette configuration garantit un flux linéaire et interrompt automatiquement l'exécution en cas d'échec, évitant ainsi la propagation de données non validées. Le déclenchement s'effectue manuellement depuis l'interface Databricks ou de manière programmatique via l'API REST (`scripts/trigger_pipeline.py`). 

#### API FastAPI

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/health` | GET | Vérification de l'état du service |
| `/api/kpis` | GET | Indicateurs clés globaux |
| `/api/departments` | GET | Top départements par score de pollution |
| `/api/parameters` | GET | Statistiques des paramètres critiques |
| `/docs` | GET | Documentation interactive Swagger UI |

Fichier de configuration `.env` (exclu de Git) :

```bash
DATABRICKS_HOST=https://dbc-xxxx.cloud.databricks.com
DATABRICKS_TOKEN=dapi_xxxxxxxxxxxx
DATABRICKS_JOB_ID=123456789
```

### 2.3 Choix techniques et alternatives envisagées

#### Ingestion des données : `requests` vs Data Load Tool (DLT)

L'énoncé du projet proposait l'utilisation du **Data Load Tool (DLT)** pour automatiser l'ingestion des données depuis les sources externes. La bibliothèque standard `requests` combinée à `pandas` a été retenue à la place, pour les raisons suivantes :

| Critère | Analyse | Décision |
|---------|---------|----------|
| Contexte Azure | Le Data Load Tool prend tout son sens dans un écosystème Azure complet | Sans accès Azure immédiat, l'outil perdait une partie de sa pertinence opérationnelle. |
| Phase d'exploration | Besoin de prototypage rapide et de compréhension des données brutes en début de projet. | `requests` + `pandas` permet une itération immédiate, un débogage facile et un contrôle total du flux. |
| Capacité locale | La machine de développement disposait de ressources suffisantes pour traiter la volumétrie (~2 Go compressés). | Pas de nécessité de déporter l'ingestion vers un outil cloud. |
| Maîtrise préalable | Connaissance solide de `requests` et des patterns d'ingestion HTTP/CSV. | Réduction du risque technique et accélération du développement. |

Ce choix ne remet pas en cause la pertinence du Data Load Tool. Dans un contexte Azure complet, cet outil serait naturellement privilégié. 

#### Traitement des données : Pandas (local) vs PySpark (Databricks)

| Environnement | Moteur | Usage | Justification |
|---------------|--------|-------|---------------|
| Local (Python) | `pandas` | Ingestion Bronze, nettoyage Silver, agrégations Gold | Simplicité d'usage, débogage interactif, performance suffisante pour 12 M de lignes en local. |
| Databricks | `PySpark` | Conversion CSV → Delta Tables, validation distribuée, exposition | Passage à l'échelle natif, intégration avec Unity Catalog, exécution sur cluster distribué. |

---

## 3. Récit de développement et logique d'adaptation

### 3.1 Point de départ : les attentes initiales

Le projet était conçu autour d'Azure Databricks, avec une architecture cloud complète : ingestion depuis Azure Data Lake, traitement distribué, orchestration native et exposition via SQL Endpoint. Cette vision supposait un accès immédiat à l'environnement Azure.

### 3.2 Le pivot : adapter sans renoncer

L'accès Azure n'étant pas disponible en temps utile, une décision a été prise : ne pas attendre, mais adapter. Plutôt que de bloquer le projet, la migration vers Databricks Community Edition a permis de préserver les principes architecturaux fondamentaux :

- Séparation des couches (Bronze / Silver / Gold)
- Validation qualité automatisée (Great Expectations)
- Orchestration séquentielle (Databricks Job / notebook maître)
- Exposition structurée des résultats (API FastAPI)

### 3.3 La méthode : commencer par le résultat

Sans l'infrastructure cloud complète, l'approche a été inversée :

1. **D'abord le résultat** : générer localement les fichiers Gold avec Pandas
2. **Puis l'intégration** : importer ces résultats dans Databricks pour valider l'orchestration et la qualité
3. **Enfin l'exposition** : construire l'API et la documentation autour des livrables existants

Cette approche ascendante a permis de maintenir la progression malgré les contraintes, et a renforcé la compréhension des dépendances entre les couches.

### 3.4 Le déclic : quand tout prend sens

Les deux premiers jours ont été marqués par l'exploration technique et l'incertitude. C'est à partir du troisième jour, avec la mise en place de Great Expectations sur Databricks et l'orchestration du Job, que l'architecture globale a pris sa cohérence. Chaque composant a alors trouvé sa place dans un flux logique et reproductible.

---

## 4. Retours d'expérience et perspectives

### 4.1 Ce qui a fonctionné

- **Flexibilité technique** : la capacité à adapter l'implémentation sans compromettre les objectifs pédagogiques
- **Approche itérative** : valider chaque brique avant de passer à la suivante a limité les blocages
- **Documentation continue** : mettre à jour le README au fil de l'eau a facilité la synthèse finale

### 4.2 Difficultés rencontrées

- **Gestion des volumétries** : traiter 6,8 Go de données Silver en local a nécessité une machine performante et une optimisation des scripts Pandas
- **Compatibilité Great Expectations** : les changements d'API entre les versions 0.18 et 1.17+ ont requis une veille technique et des ajustements en cours de route (passage de `context.sources` à `context.data_sources`, nommage PascalCase des expectations)
- **Limites de la version gratuite** : l'absence de SQL Endpoint et de DBFS public a imposé des contournements (Volumes, export JSON)

### 4.3 Perspectives d'amélioration

- **Migration vers Azure Databricks** : traiter l'ensemble du pipeline (Bronze → Gold) dans un environnement cloud natif, avec Unity Catalog, Delta Live Tables et SQL Endpoint
- **Déploiement de l'API** : héberger FastAPI sur une plateforme serverless (Render, Railway) pour une exposition publique
- **Tests de non-régression** : intégrer dans GitHub Actions la validation des agrégats Gold pour détecter les régressions métier

### 4.4 Expérience Azure antérieure

Lors d'un projet précédent en machine learning, l'utilisation d'Azure AI Foundry a été une expérience formatrice. Bien que la courbe d'apprentissage initiale soit raide, la puissance et l'intégration des services Azure se révèlent particulièrement efficaces une fois les concepts maîtrisés. Cette expérience renforce la motivation à déployer les projets futurs sur Azure dans pour en exploiter tout le potentiel cloud.

---

## 5. Annexes techniques

### 5.1 Commandes clés pour reproduction

```bash
# Cloner et installer
git clone https://github.com/DBX-76/projet-eau-david.git
cd projet-eau-david
pip install -r requirements.txt

# Exécuter le pipeline local
python notebooks/01_ingestion_bronze.py
python notebooks/02_transformation_silver.py
python notebooks/03_aggregation_gold.py

# Lancer l'API
python api_server.py
# Accéder à http://localhost:8000/docs

# Déclencher le pipeline Databricks à distance
# (après configuration du fichier .env)
python scripts/trigger_pipeline.py
```

### 5.2 Structure des exports pour évaluation

```
exports/
├── conformite_gauge.html          # Dashboard jauge (ouvert dans navigateur)
├── pollution_departements.html    # Histogramme départements
├── parametres_critiques.html      # Tableau statistiques paramètres
└── api_exposition.json            # Données structurées pour API
```

### 5.3 Références

- [Great Expectations Documentation](https://docs.greatexpectations.io)
- [Databricks Community Edition](https://community.cloud.databricks.com)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [data.gouv.fr — Qualité de l'eau](https://www.data.gouv.fr/fr/datasets/resultats-du-controle-sanitaire-des-eaux-distribuees/)
