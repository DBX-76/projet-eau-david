# Projet Qualité d'Eau

---

## Vue d'ensemble

Projet implémentant une **architecture Médaillon** (Bronze → Silver → Gold) pour transformer les données brutes de qualité d'eau en indicateurs métier exploitables.

### Objectifs

- Ingérer automatiquement les données depuis [data.gouv.fr](https://www.data.gouv.fr/)
- Nettoyer, valider et standardiser (couche Silver)
- Générer des KPIs et agrégations (couche Gold)
- Intégrer **Great Expectations v0.18+** pour la qualité

---

## Architecture Médaillon

```
 data.gouv.fr
    ↓
 BRONZE (Raw Data)
    • 13M lignes, 40 colonnes
    • 3 fichiers fusionnés (RESULT, PLV, COM)
    ↓
 SILVER (Cleaned & Validated)
    • 12.5M lignes, 55 colonnes
    • Jointures, déduplication, enrichissement
    • GX Validation : 9/9 attentes OK
    ↓
 GOLD (Business Metrics)
    • 5 fichiers d'agrégation
    • KPIs globaux, départements, communes
    • Analyse paramètres critiques
```

---

## Résultats Clés

| Métrique | Valeur |
|----------|--------|
| **Enregistrements traités** | 12.5M |
| **Taux de conformité** | 92.96% |
| **Prélèvements uniques** | 295K |
| **Couverture géographique** | 103 départements, 30K communes |
| **Paramètres analysés** | 1,366 uniques |
| **Validation Great Expectations** | 9/9 attentes OK |

### Résultats Métier

- **Meilleure commune** : JONCREUIL (pollution moyenne: 0.004)
- **Pire commune** : CROUZILLES (pollution moyenne: 210.618)
- **pH moyen** : 7.555 (plage acceptable: 6.5-8.5)

---

##  Structure du Projet

```
eau-project/
├── README.md                    
├── requirements.txt            
├── .gitignore                  
│
├── 📂 src/eau/                
│   ├── __init__.py
│   ├── bronze.py               # Logique Bronze
│   ├── silver.py               # Logique Silver
│   └── gold.py                 # Logique Gold
│
├── 📂 notebooks/               
│   ├── 01_ingestion_bronze.py      # Pipeline d'ingestion
│   ├── 02_transformation_silver.py # Pipeline de nettoyage/validation
│   └── 03_aggregation_gold.py      # Pipeline d'agrégation
│   └── notebook_databricks_eau     # Notebook commité de la plateforme Databricks
│
├── 📂 scripts/                 
│   ├── README.md               # Documentation des scripts
│   ├── check_gold_output.py    # Diagnostic fichiers Gold
│   ├── check_silver.py         # Diagnostic couche Silver
│   ├── quick_check.py          # Diagnostic rapide
│   ├── quick_check_silver.py   # Diagnostic rapide Silver
│   └── analyze_zip.py          # Analyse structure ZIP
│
├── 📂 tests/                 
│   ├── __init__.py
│   ├── test_setup.py
│   └── test_columns.py
│
├── 📂 data/                  
│   ├── bronze/
│   │   └── bronze_combined.csv   
│   ├── clean/
│   │   └── silver_clean.csv      
│   └── gold/
│       ├── gold_global_kpis.csv
│       ├── gold_departments_pollution.csv
│       ├── gold_communes_top10_best.csv
│       ├── gold_communes_top10_worst.csv
│       └── gold_critical_parameters.csv
│
└── 📂 gx/                      # GREAT EXPECTATIONS
    └── (contexte éphémère)
```

---

## Quick Start

### Prérequis

- **Python** ≥ 3.9
- **pandas**, **numpy**, **requests**
- **Great Expectations** ≥ 0.18.0

### Installation

```bash
# 1. Cloner le repo
git clone https://github.com/user/eau-project.git
cd eau-project

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. (Optionnel) Installer en mode développement
pip install -e ".[dev]"
```

### Exécution

```bash
# Bronze - Ingestion des données
python notebooks/01_ingestion_bronze.py

# Silver - Nettoyage & validation
python notebooks/02_transformation_silver.py

# Gold - Agrégations métier
python notebooks/03_aggregation_gold.py
```

### Diagnostic

```bash
# Valider les sorties Gold
python scripts/check_gold_output.py

# Vérifier la qualité Silver
python scripts/check_silver.py
```

---

##  Détails Techniques

### Pipeline Bronze (`01_ingestion_bronze.py`)

- Télécharge le ZIP depuis data.gouv.fr (276 MB)
- Extrait 3 fichiers TXT (RESULT, PLV, COM)
- Applique mappages de colonnes spécifiques
- Fusionne via jointures externes
- Exporte en CSV UTF-8

**Sortie :** 13M lignes × 40 colonnes

### Pipeline Silver (`02_transformation_silver.py`)

**Étapes :**
1. **Reconstruction** : Jointures PLV (96.9% enrichissement communes)
2. **Nettoyage** : Conversion dates, types, encodages
3. **Déduplication** : Clé (id_prelevement, code_parametre)
4. **Validation** : Great Expectations v0.18+ (9 attentes)
5. **Enrichissement** : record_id, quality_flag

**Validation GX :** 9/9 attentes OK

**Validation personnalisée :**
- resultat NULL : 0.86% (normal - params qualitatifs)
- pH hors [4.0, 11.0] : 847K (à investiguer)
- Nitrates hors [0, 500] : 2.8K
- Autres paramètres : <0.03%

**Sortie :** 12.5M lignes × 55 colonnes (6.8 GB)

### Pipeline Gold (`03_aggregation_gold.py`)

**Fichiers générés :**

1. **`gold_global_kpis.csv`** — Indicateurs clés globaux
   - Taux conformité, couverture temporelle, géographie

2. **`gold_departments_pollution.csv`** — Agrégation par département (103 depts)
   - Score pollution, alertes, anomalies

3. **`gold_communes_top10_best.csv`** — Top 10 des meilleures communes
4. **`gold_communes_top10_worst.csv`** — Top 10 des pires communes

5. **`gold_critical_parameters.csv`** — Analyse des paramètres critiques
   - pH, Nitrates, Coliformes, etc.

---

## Qualité & Validation

### Great Expectations v0.18+

La pipeline utilise **Great Expectations** avec :
- **Contexte éphémère** (aucun fichier YAML)
- **Fluent API** pour définition des attentes
- **ValidationDefinition** pour exécution

**Attentes :**
- Table non-vide
- Colonnes requises présentes
- Types de données corrects
- Valeurs non-NULL
- Valeurs dans plages acceptables

## Databricks

### Ce qui a été fait

Les fichiers CSV de la couche Gold (générés localement) ont été importés dans Databricks pour :

1. **Convertir les CSV en tables Delta** - Utilisation de PySpark pour créer des tables managées
2. **Explorer les données avec PySpark** - Requêtes sur les DataFrames et affichage des résultats
3. **Tester les requêtes SQL** - Interrogation directe des tables Delta

### Ce qui n'a PAS été fait

- Le pipeline d'ingestion (Bronze/Silver) n'a pas été réexécuté dans Databricks
- Seuls les fichiers Gold finaux ont été utilisés
- Aucune transformation supplémentaire n'a été appliquée

### voir le répertoire notebook/notebook_databricks_eau

