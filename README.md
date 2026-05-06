# 🌊 Eau-Project : Pipeline Data Engineering — Qualité d'Eau

**Statut :** ✅ Production-Ready | **Version :** 1.0.0 | **Dernière mise à jour :** Mai 2026

---

## 📋 Vue d'ensemble

Projet complet de **Data Engineering** implémentant une **architecture Médaillon** (Bronze → Silver → Gold) pour transformer les données brutes de qualité d'eau en indicateurs métier exploitables.

### 🎯 Objectifs

- ✅ Ingérer automatiquement les données depuis [data.gouv.fr](https://www.data.gouv.fr/)
- ✅ Nettoyer, valider et standardiser (couche Silver)
- ✅ Générer des KPIs et agrégations (couche Gold)
- ✅ Intégrer **Great Expectations v0.18+** pour la qualité
- ✅ Prêt pour Azure Databricks et cloud deployment

---

## 🏗️ Architecture Médaillon

```
🌐 data.gouv.fr
    ↓
📦 BRONZE (Raw Data)
    • 13M lignes, 40 colonnes
    • 3 fichiers fusionnés (RESULT, PLV, COM)
    ↓
🔧 SILVER (Cleaned & Validated)
    • 12.5M lignes, 55 colonnes
    • Jointures, déduplication, enrichissement
    • ✅ GX Validation : 9/9 attentes OK
    ↓
⭐ GOLD (Business Metrics)
    • 5 fichiers d'agrégation
    • KPIs globaux, départements, communes
    • Analyse paramètres critiques
    ↓
📊 Visualisation / BI (Power BI, Looker, etc.)
```

---

## 📊 Résultats Clés

| Métrique | Valeur |
|----------|--------|
| **Enregistrements traités** | 12.5M |
| **Taux de conformité** | 92.96% |
| **Prélèvements uniques** | 295K |
| **Couverture géographique** | 103 départements, 30K communes |
| **Paramètres analysés** | 1,366 uniques |
| **Validation Great Expectations** | ✅ 9/9 attentes OK |

### 🥇 Résultats Métier

- **Meilleure commune** : JONCREUIL (pollution moyenne: 0.004)
- **Pire commune** : CROUZILLES (pollution moyenne: 210.618)
- **pH moyen** : 7.555 (plage acceptable: 6.5-8.5)

---

## 📁 Structure du Projet

```
eau-project/
├── README.md                    # Ce fichier
├── pyproject.toml              # Configuration Python (packaging)
├── requirements.txt            # Dépendances
├── .gitignore                  # Fichiers à ignorer Git
├── .env.example                # Template variables d'environnement
│
├── 📂 src/eau/                 # 🎯 CODE MÉTIER (réutilisable)
│   ├── __init__.py
│   ├── bronze.py               # Logique Bronze
│   ├── silver.py               # Logique Silver
│   └── gold.py                 # Logique Gold
│
├── 📂 notebooks/               # 🔬 ANALYSES & EXPLORATIONS
│   ├── 01_ingestion_bronze.py      # Pipeline d'ingestion
│   ├── 02_transformation_silver.py # Pipeline de nettoyage/validation
│   └── 03_aggregation_gold.py      # Pipeline d'agrégation
│
├── 📂 scripts/                 # 🛠️ OUTILS DE DÉVELOPPEMENT
│   ├── README.md               # Documentation des scripts
│   ├── check_gold_output.py    # Diagnostic fichiers Gold
│   ├── check_silver.py         # Diagnostic couche Silver
│   ├── quick_check.py          # Diagnostic rapide
│   ├── quick_check_silver.py   # Diagnostic rapide Silver
│   └── analyze_zip.py          # Analyse structure ZIP
│
├── 📂 tests/                   # ✅ TESTS UNITAIRES
│   ├── __init__.py
│   ├── test_setup.py
│   └── test_columns.py
│
├── 📂 data/                    # 📊 DONNÉES
│   ├── bronze/
│   │   └── bronze_combined.csv          (2.1 GB)
│   ├── clean/
│   │   └── silver_clean.csv             (6.8 GB)
│   └── gold/
│       ├── gold_global_kpis.csv
│       ├── gold_departments_pollution.csv
│       ├── gold_communes_top10_best.csv
│       ├── gold_communes_top10_worst.csv
│       └── gold_critical_parameters.csv
│
├── 📂 docs/                    # 📚 DOCUMENTATION
│   └── ...
│
├── 📂 config/                  # ⚙️ CONFIGURATION
│   └── ...
│
└── 📂 gx/                      # 🔍 GREAT EXPECTATIONS
    └── (contexte éphémère)
```

---

## 🚀 Quick Start

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

## 🔍 Détails Techniques

### Pipeline Bronze (`01_ingestion_bronze.py`)

- 📥 Télécharge le ZIP depuis data.gouv.fr (276 MB)
- 📂 Extrait 3 fichiers TXT (RESULT, PLV, COM)
- 🔄 Applique mappages de colonnes spécifiques
- 📊 Fusionne via jointures externes
- 💾 Exporte en CSV UTF-8

**Sortie :** 13M lignes × 40 colonnes

### Pipeline Silver (`02_transformation_silver.py`)

**Étapes :**
1. **Reconstruction** : Jointures PLV (96.9% enrichissement communes)
2. **Nettoyage** : Conversion dates, types, encodages
3. **Déduplication** : Clé (id_prelevement, code_parametre)
4. **Validation** : Great Expectations v0.18+ (9 attentes)
5. **Enrichissement** : record_id, quality_flag

**Validation GX :** 9/9 attentes OK ✅

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

## ✅ Qualité & Validation

### Great Expectations v0.18+

La pipeline utilise **Great Expectations** avec :
- **Contexte éphémère** (aucun fichier YAML)
- **Fluent API** pour définition des attentes
- **ValidationDefinition** pour exécution

**Attentes (9 au total) :**
- Table non-vide
- Colonnes requises présentes
- Types de données corrects
- Valeurs non-NULL (où attendu)
- Valeurs dans plages acceptables

### Problèmes Connus & À Investiguer

| Problème | Sévérité | Statut | Note |
|----------|----------|--------|------|
| pH hors plage [4.0, 11.0] | ⚠️ Moyen | À investiguer | 847K anomalies — possible unité de mesure |
| Dates : NaT en résumé | 🔵 Info | À résoudre | Suffixes de fusion non nettoyés |
| Nitrates > 500 mg/L | 🟡 Faible | Accepté | 2.8K cas — <0.03% du total |

---

## 🌐 Déploiement Azure Databricks

```python
# spark-submit à partir de Azure Databricks
spark-submit --packages org.apache.hadoop:hadoop-azure:3.2.0 \
    dbfs:/notebooks/02_transformation_silver.py
```

**Configuration requise :**
- Storage Account pour fichiers (Bronze, Silver, Gold)
- Cluster Databricks (7.3 LTS ou plus récent)
- Great Expectations SDK installé

---

## 📝 Logs & Monitoring

Tous les pipelines produisent des logs structurés :

```
2026-05-06 09:21:44 - INFO - 🔄 PIPELINE SILVER — TRANSFORMATION + VALIDATION GX
2026-05-06 09:21:44 - INFO - 📂 Chargement des données : ./data/clean/silver_clean.csv
...
2026-05-06 09:25:40 - INFO - ✅ Résultat global : SUCCÈS
```

---

## 🔗 Ressources

- **Data Source :** [data.gouv.fr — Qualité de l'eau](https://www.data.gouv.fr/)
- **Great Expectations :** [Documentation](https://docs.greatexpectations.io/)
- **Medallion Architecture :** [Databricks Blog](https://www.databricks.com/blog/)
- **Azure Data Engineering :** [Microsoft Docs](https://learn.microsoft.com/fr-fr/azure/architecture/reference-architectures/data-engineering/)

---

## 👨‍💼 Contribution & Support

- **Issues :** Signaler un bug ou proposer une amélioration
- **Discussions :** Questions techniques (Discussions GitHub)
- **Pull Requests :** Contributions bienvenues !

---

## 📄 Licence

MIT License — Libre d'utilisation

---

## 📧 Contact

**Auteur :** eau-project  
**Email :** contact@eau-project.local  
**Dernière mise à jour :** Mai 2026

---

**Statut :** ✅ **PRODUCTION-READY**
