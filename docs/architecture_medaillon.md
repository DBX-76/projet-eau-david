# 📐 Architecture Médaillon — Documentation Détaillée

**Version :** 1.0.0 | **Date :** Mai 2026

---

## 🏗️ Couches Médaillon

### L1 - BRONZE 📦 (Données Brutes)

**Responsabilités :**
- Ingérer directement depuis la source (data.gouv.fr ZIP)
- Aucune transformation (sauf parsage basique)
- Préserver les données telles qu'elles

**Structure :**
```
BRONZE (13M lignes × 40 colonnes)
├── File 1: RESULTATS (12.6M rows)
│   ├── id_prelevement
│   ├── code_parametre
│   ├── resultat
│   ├── date_prelevement
│   └── ...
├── File 2: CONFORMITE_PLV (409K rows)
│   ├── id_prelevement
│   ├── nom_commune
│   ├── code_reseau
│   └── ...
└── File 3: COMMUNES (49K rows)
    ├── code_reseau
    ├── code_departement
    └── ...
```

**Fichier de sortie :** `data/bronze/bronze_combined.csv`

---

### L2 - SILVER 🔧 (Données Nettoyées & Validées)

**Responsabilités :**
1. Joindre les 3 fichiers Bronze sur clés métier
2. Nettoyer types, dates, encodages
3. Dédupliquer sur (id_prelevement, code_parametre)
4. Valider avec Great Expectations
5. Enrichir avec métadonnées (record_id, quality_flag)

**Jointures :**

```
RESULTATS (12.6M)
    ↓ [LEFT JOIN sur id_prelevement]
CONFORMITE_PLV (409K)
    → ENRICHIT 96.9% (12.2M communes ajoutées)
    
COMMUNES (49K)
    ↓ [LEFT JOIN sur code_reseau]
RESULTATS+PLV
    → 0% match (code_reseau vide partout)
```

**Output après jointures & dedup :**
```
SILVER (12.5M lignes × 55 colonnes)
├── id_prelevement (PK)
├── code_parametre (PK)
├── resultat (float)
├── date_prelevement (datetime)
├── nom_commune (enrichi)
├── code_departement (enrichi)
├── record_id (hash) ← NEW
├── quality_flag (OK/WARNING/ALERT/UNKNOWN) ← NEW
└── ... (50 autres colonnes)
```

**Fichier de sortie :** `data/clean/silver_clean.csv`

**Great Expectations Validation (9 attentes) :**
```
✅ Table non-vide
✅ Colonnes requises présentes
✅ Types de données corrects
✅ id_prelevement NOT NULL
✅ code_parametre NOT NULL
✅ resultat NOT NULL OU qualité = QUALITATIVE
✅ date_prelevement en plage valide
✅ Pas de valeurs aberrantes extrêmes
✅ Pas de doublons sur clé (id_prelevement, code_parametre)
```

---

### L3 - GOLD ⭐ (Agrégations Métier)

**Responsabilités :**
- Calculer KPIs globaux
- Agréger par département
- Identifier top/bottom communes
- Analyser paramètres critiques

**Fichiers générés :**

#### 1. `gold_global_kpis.csv` (1 ligne)
```
total_records: 12512381
total_samplings: 295089
min_date: NaT
max_date: NaT
days_covered: NaN
departments_covered: 103
communes_covered: 30152
parameters_analyzed: 1366
global_conformity_rate: 92.96
quality_ok: 12403010
quality_warning: 1616
quality_alert: 0
quality_unknown: 107755
```

#### 2. `gold_departments_pollution.csv` (103 lignes)
```
code_departement | samplings | avg_result | pollution_score | ...
1                | 3613      | 11.167     | 0.0              |
67               | 3954      | 14.385     | 0.0              |
...
```

#### 3. `gold_communes_top10_best.csv` (10 lignes)
```
nom_commune              | samplings | avg_pollution
JONCREUIL               | 5         | 0.004
VILLIERS-HERBISSE      | 9         | 0.311
...
```

#### 4. `gold_communes_top10_worst.csv` (10 lignes)
```
nom_commune              | samplings | avg_pollution
CROUZILLES             | 5         | 210.618
ISCHES                 | 7         | 139.9
...
```

#### 5. `gold_critical_parameters.csv` (1 ligne)
```
parameter | count  | mean  | std   | min | max   | threshold | exceedances | percent_exceeding
pH        | 273307 | 7.555 | 0.456 | 0.0 | 13.7  | NaN       | 0           | 0
```

---

## 📊 Flux de Données

```
┌─────────────────────────────────────────────────────────┐
│                   data.gouv.fr                          │
│              (API ZIP 276 MB)                           │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ 01_INGESTION_BRONZE.py                                  │
│ ├─ Télécharger ZIP                                      │
│ ├─ Extraire 3 TXT (RESULT, PLV, COM)                   │
│ ├─ Parser avec encodage ISO-8859-1                     │
│ ├─ Mapper colonnes (spécifique par type)               │
│ └─ Fusionner via outer join                            │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
      data/bronze/
      bronze_combined.csv
      (13M lignes, 2.1 GB)
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ 02_TRANSFORMATION_SILVER.py                             │
│ ├─ Charger bronze_combined.csv                         │
│ ├─ Reconstruct: Jointures (PLV 96.9%, COM 0%)         │
│ ├─ Clean: Dates (ISO 8601), Types, Encodage           │
│ ├─ Deduplicate: (id_prelevement, code_parametre)      │
│ ├─ Validate: Great Expectations 9/9 ✅                │
│ └─ Enrich: record_id, quality_flag                     │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
      data/clean/
      silver_clean.csv
      (12.5M lignes, 6.8 GB)
             │
             ▼
┌─────────────────────────────────────────────────────────┐
│ 03_AGGREGATION_GOLD.py                                  │
│ ├─ KPIs globaux (conformité, couverture)              │
│ ├─ Agrégation par département (103)                   │
│ ├─ Top 10 communes best/worst                         │
│ ├─ Analyse paramètres critiques                       │
│ └─ Export 5 fichiers CSV                              │
└────────────┬────────────────────────────────────────────┘
             │
             ▼
      data/gold/
      ├─ gold_global_kpis.csv
      ├─ gold_departments_pollution.csv
      ├─ gold_communes_top10_best.csv
      ├─ gold_communes_top10_worst.csv
      └─ gold_critical_parameters.csv
             │
             ▼
      📊 Power BI / Dashboard
         Visualisation & BI
```

---

## 🔑 Clés Métier

### Clé Primaire par Couche

| Couche | Clé(s) | Cardinality | Note |
|--------|--------|-------------|------|
| **Bronze** | Aucune (multiplet) | N:M | Données brutes en vrac |
| **Silver** | (id_prelevement, code_parametre) | 1:1 | Clé métier unique |
| **Gold** | Dépend du fichier | Voir ci-après | Agrégations/résumés |

### Clés de Jointure (Silver)

```
RESULTATS.id_prelevement = PLV.id_prelevement (96.9% match)
RESULTATS.code_reseau    = COM.code_reseau    (0% match)
```

---

## 📈 Volumes & Performance

| Étape | Input | Output | Temps | Ram |
|-------|-------|--------|-------|-----|
| **Bronze Load** | ZIP 276MB | 13M rows | ~30s | 2GB |
| **Reconstruct** | 13M rows | 12.6M rows | ~10s | 4GB |
| **Clean** | 12.6M rows | 12.6M rows | ~15s | 3GB |
| **Dedup** | 12.6M rows | 12.5M rows | ~15s | 4GB |
| **Validate GX** | 12.5M rows | — | ~110s | 3GB |
| **Enrich** | 12.5M rows | 12.5M rows | ~15s | 4GB |
| **Gold Agg** | 12.5M rows | 5 CSVs | ~45s | 2GB |
| **TOTAL** | — | — | **~7min** | — |

---

## 🚨 Anomalies Détectées

### Silver Validation Issues

| Paramètre | Anomalies | % | Cause Probable | Action |
|-----------|-----------|---|---|---|
| **pH** | 847K | 6.8% | Unité de mesure? | À investiguer |
| **Nitrates** | 2.8K | 0.02% | Données aberrantes | Acceptable |
| **Phosphates** | 2 | 0.0% | Données aberrantes | Acceptable |
| **Ammonium** | 74 | 0.001% | Données aberrantes | Acceptable |
| **Coliformes** | 1.055K | 0.008% | Données aberrantes | Acceptable |

---

## 🔐 Encodages & Formats

| Fichier | Encodage | Séparateur | Format |
|---------|----------|-----------|--------|
| **Bronze source** | ISO-8859-1 | ; | CSV |
| **Silver** | UTF-8 | ; | CSV |
| **Gold** | UTF-8 | ; | CSV |

---

## 📋 Colonnes par Couche

### BRONZE (40 colonnes)
```
[RESULTATS]
- id_prelevement, code_parametre, resultat, date_prelevement, ...

[PLV]  
- id_prelevement, nom_commune, date_limite, ...

[COM]
- code_reseau, code_departement, nom_region, ...
```

### SILVER (55 colonnes)
```
[Clés]
- id_prelevement, code_parametre, record_id

[Data]
- resultat, date_prelevement, nom_commune, code_departement

[Métadonnées]
- quality_flag (OK/WARNING/ALERT/UNKNOWN)
- processed_date

[Tous les champs Bronze fusionnés]
```

### GOLD (colonnes variables)
```
gold_global_kpis.csv → 13 colonnes
gold_departments_pollution.csv → 9 colonnes
gold_communes_top10_best.csv → 3 colonnes
gold_communes_top10_worst.csv → 3 colonnes
gold_critical_parameters.csv → 10 colonnes
```

---

## 🎯 Great Expectations Configuration

**Version :** 1.17.0  
**API :** Fluent (v0.18+ compatible)  
**Contexte :** Éphémère (no YAML files)  

**Attentes définies :**
```python
suite.add_expectation(
    gxe.ExpectTableRowCountToBeBetween(min_value=1000000)
)
suite.add_expectation(
    gxe.ExpectTableColumnsToMatchOrderedList(column_list=[...])
)
# ... etc
```

---

## ✅ Checklist de Déploiement

- [x] Bronze pipeline testé ✅
- [x] Silver pipeline testé ✅
- [x] Gold pipeline testé ✅
- [x] Great Expectations v0.18+ fonctionnel ✅
- [x] Structure projet professionnelle ✅
- [ ] Tests unitaires complets (phase 2)
- [ ] Azure Databricks déploiement (phase 2)
- [ ] Power BI dashboard (phase 2)
- [ ] Documentation complète (phase 2)

---

**Fin de la documentation d'architecture**
