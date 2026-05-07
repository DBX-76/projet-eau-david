# Spécification des Règles de Qualité - Projet Eau

## Vue d'ensemble
Ce document détaille toutes les règles de validation et de qualité des données qui seront implémentées via **Great Expectations** dans la couche Silver (données nettoyées) du pipeline Data Engineering.

---

## 1. Règles Géospatiales

### 1.1 Latitude dans les limites de la France
- **Règle :** La colonne `latitude` doit être comprise entre 41.0 et 51.5
- **Justification :** Coordonnées minimales/maximales du territoire français (Continental + Corse)
- **Type d'erreur :** Valeur aberrante / GPS défaillant
- **Action en cas d'anomalie :** Rejeter la ligne ou marquer comme "données suspectes"
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="latitude",
      min_value=41.0,
      max_value=51.5,
      result_format="SUMMARY"
  )
  ```

### 1.2 Longitude dans les limites de la France
- **Règle :** La colonne `longitude` doit être comprise entre -5.5 et 8.5
- **Justification :** Coordonnées Ouest/Est du territoire français
- **Type d'erreur :** Valeur aberrante / GPS défaillant
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="longitude",
      min_value=-5.5,
      max_value=8.5,
      result_format="SUMMARY"
  )
  ```

### 1.3 Combinaison Latitude/Longitude valide
- **Règle :** Aucune des coordonnées ne doit être (0, 0)
- **Justification :** (0, 0) indique généralement des données manquantes ou mal formatées
- **Type d'erreur :** Donnée par défaut / Point d'ancrage fictif
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_combinations_to_be_unique(
      column_combinations=[["latitude", "longitude"]],
      ignore_row_if="any_value_is_missing"
  )
  ```

---

## 2. Règles Temporelles

### 2.1 Date de prélèvement valide
- **Règle :** La colonne `date_prelevement` doit être dans le format ISO 8601 (YYYY-MM-DD)
- **Justification :** Standardisation internationale
- **Type d'erreur :** Format incohérent / Donnée corrompue
- **Action en cas d'anomalie :** Rejeter la ligne ou appliquer un parsing robuste
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_match_regex(
      column="date_prelevement",
      regex=r"^\d{4}-\d{2}-\d{2}$"
  )
  ```

### 2.2 Date de prélèvement antérieure à aujourd'hui
- **Règle :** `date_prelevement` ≤ date du traitement (pas de dates futures)
- **Justification :** Éviter les erreurs d'horodatage
- **Type d'erreur :** Erreur d'entrée utilisateur / Bug système
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  from datetime import datetime
  batch.expect_column_values_to_be_dateutil_parseable(
      column="date_prelevement"
  )
  # Puis vérifier en PySpark : df.filter(col("date_prelevement") > current_date())
  ```

### 2.3 Cohérence temporelle des séries
- **Règle :** Pour une même station, pas de gap anormal (> 90 jours) sans annotation
- **Justification :** Identifier les interruptions de mesure
- **Type d'erreur :** Station inaccessible / Arrêt de surveillance
- **Action en cas d'anomalie :** Signaler dans un log (ne pas rejeter)
- **Code Great Expectations :**
  ```python
  # À implémenter en PySpark custom validator
  # df.groupBy("station_id").agg(max("date_prelevement") - min("date_prelevement"))
  ```

---

## 3. Règles d'Identifiants et Références

### 3.1 ID de station non nul
- **Règle :** La colonne `station_id` ne doit jamais être NULL
- **Justification :** Clé de traçabilité indispensable
- **Type d'erreur :** Donnée manquante
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_not_be_null(column="station_id")
  ```

### 3.2 ID de station unique par commune
- **Règle :** Chaque `station_id` correspondra à une seule `commune_code` (pas de déplacement)
- **Justification :** Garantir la traçabilité géographique
- **Type d'erreur :** Erreur d'intégration de données
- **Action en cas d'anomalie :** Marquer comme anomalie et enquêter
- **Code Great Expectations :**
  ```python
  batch.expect_compound_columns_to_be_unique(
      column_sets=[["station_id", "commune_code"]]
  )
  ```

### 3.3 Format du code commune INSEE
- **Règle :** La colonne `commune_code` doit être un code INSEE valide (5 chiffres)
- **Justification :** Format standardisé INSEE
- **Type d'erreur :** Donnée corrompue
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_match_regex(
      column="commune_code",
      regex=r"^\d{5}$"
  )
  ```

---

## 4. Règles de Paramètres Physico-Chimiques

### 4.1 Paramètre non nul
- **Règle :** La colonne `parametre` (nitrates, phosphates, pH, etc.) ne doit jamais être NULL
- **Justification :** Donnée centrale du dataset
- **Type d'erreur :** Donnée manquante
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_not_be_null(column="parametre")
  ```

### 4.2 Paramètre dans liste autorisée
- **Règle :** `parametre` ∈ {pH, Nitrates, Phosphates, Ammonium, E.coli, Coliformes, Turbidité, Conductivité, ...}
- **Justification :** Valider contre le dictionnaire technique
- **Type d'erreur :** Nouveau paramètre != identifié / Typo
- **Action en cas d'anomalie :** Rejeter la ligne + Créer ticket d'investigation
- **Code Great Expectations :**
  ```python
  authorized_parameters = ["pH", "Nitrates", "Phosphates", "Ammonium", 
                          "E.coli", "Coliformes", "Turbidite", "Conductivite"]
  batch.expect_column_values_to_be_in_set(
      column="parametre",
      value_set=authorized_parameters
  )
  ```

### 4.3 Résultat de mesure non nul
- **Règle :** La colonne `resultat` (valeur mesurée) ne doit jamais être NULL
- **Justification :** Donnée centrale du dataset
- **Type d'erreur :** Donnée manquante
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_not_be_null(column="resultat")
  ```

---

## 5. Règles par Paramètre Spécifique

### 5.1 pH (potentiel hydrogène)
- **Plage acceptée :** pH ∈ [6.0 - 9.0]
- **Justification :** Normes eau potable (Directive 2020/2184/UE)
- **Type d'erreur :** Valeur aberrante / Eau extrêmement basique ou acide
- **Action en cas d'anomalie :** Rejeter ou marquer comme alerte
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=6.0,
      max_value=9.0,
      condition=batch["parametre"] == "pH"
  )
  ```

### 5.2 Nitrates (NO₃)
- **Plage acceptée :** Nitrates ∈ [0 - 500 mg/L]
- **Justification :** Norme PL (Norme 50 mg/L eau potable), mais captage les variations naturelles
- **Type d'erreur :** Valeur aberrante
- **Action en cas d'anomalie :** Rejeter ou marquer comme alerte (dépassement normatif)
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=0,
      max_value=500,
      condition=batch["parametre"] == "Nitrates"
  )
  ```

### 5.3 Phosphates (PO₄)
- **Plage acceptée :** Phosphates ∈ [0 - 20 mg/L]
- **Justification :** Limite de lixiviation naturelle
- **Type d'erreur :** Valeur aberrante
- **Action en cas d'anomalie :** Rejeter
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=0,
      max_value=20,
      condition=batch["parametre"] == "Phosphates"
  )
  ```

### 5.4 Ammonium (NH₄⁺)
- **Plage acceptée :** Ammonium ∈ [0 - 10 mg/L]
- **Justification :** Indicateur de pollution
- **Type d'erreur :** Valeur aberrante (pollution extrême)
- **Action en cas d'anomalie :** Marquer comme alerte environnementale
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=0,
      max_value=10,
      condition=batch["parametre"] == "Ammonium"
  )
  ```

### 5.5 Escherichia coli (E.coli)
- **Plage acceptée :** E.coli ∈ [0 - 10000 CFU/100mL]
- **Justification :** Indicateur bactérien de contamination fécale
- **Type d'erreur :** Valeur aberrante
- **Action en cas d'anomalie :** Rejeter (qualité critique)
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=0,
      max_value=10000,
      condition=batch["parametre"] == "E.coli"
  )
  ```

### 5.6 Coliformes totaux
- **Plage acceptée :** Coliformes ∈ [0 - 100000 CFU/100mL]
- **Justification :** Indicateur bactérien
- **Type d'erreur :** Valeur aberrante
- **Action en cas d'anomalie :** Marquer comme alerte
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=0,
      max_value=100000,
      condition=batch["parametre"] == "Coliformes"
  )
  ```

### 5.7 Turbidité
- **Plage acceptée :** Turbidité ∈ [0 - 1000 NTU]
- **Justification :** Mesure de la clarté de l'eau (0.5-1 NTU pour eau potable)
- **Type d'erreur :** Valeur aberrante
- **Action en cas d'anomalie :** Rejeter
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=0,
      max_value=1000,
      condition=batch["parametre"] == "Turbidite"
  )
  ```

### 5.8 Conductivité électrique
- **Plage acceptée :** Conductivité ∈ [0 - 2500 µS/cm]
- **Justification :** Indicateur de minéralisation
- **Type d'erreur :** Valeur aberrante (eau sursalinisée)
- **Action en cas d'anomalie :** Rejeter
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_be_between(
      column="resultat",
      min_value=0,
      max_value=2500,
      condition=batch["parametre"] == "Conductivite"
  )
  ```

---

## 6. Règles de Doublons

### 6.1 Pas de doublons exacts
- **Règle :** Aucun doublon sur la combinaison `(station_id, date_prelevement, parametre)`
- **Justification :** Une seule mesure par lieu/date/paramètre
- **Type d'erreur :** Import dupliqué / Erreur ETL
- **Action en cas d'anomalie :** Dédupliquer (garder le premier)
- **Code Great Expectations :**
  ```python
  batch.expect_compound_columns_to_be_unique(
      column_sets=[["station_id", "date_prelevement", "parametre"]],
      ignore_row_if="any_value_is_missing"
  )
  ```

---

## 7. Règles d'Unité de Mesure

### 7.1 Unité non nulle
- **Règle :** La colonne `unite` ne doit jamais être NULL
- **Justification :** Impossible d'interpréter le résultat sans unité
- **Type d'erreur :** Donnée manquante
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_not_be_null(column="unite")
  ```

### 7.2 Unité cohérente par paramètre
- **Règle :** Chaque paramètre a une unité associée fixe (pH → sans unité, Nitrates → mg/L, etc.)
- **Justification :** Garantir la comparabilité des mesures
- **Type d'erreur :** Unité incohérente / Bug d'import
- **Action en cas d'anomalie :** Rejeter ou corriger automatiquement
- **Dictionnaire :**
  - pH : `sans unite`
  - Nitrates : `mg/L`
  - Phosphates : `mg/L`
  - Ammonium : `mg/L`
  - E.coli : `CFU/100mL`
  - Coliformes : `CFU/100mL`
  - Turbidité : `NTU`
  - Conductivité : `µS/cm`
- **Code Great Expectations :**
  ```python
  expected_units = {
      "pH": "sans unite",
      "Nitrates": "mg/L",
      "Phosphates": "mg/L",
      # ... etc
  }
  for parametre, unit in expected_units.items():
      batch.expect_column_values_to_equal(
          column="unite",
          value=unit,
          condition=batch["parametre"] == parametre
      )
  ```

---

## 8. Règles de Métadonnées

### 8.1 Laboratoire présent
- **Règle :** La colonne `laboratoire` ne doit jamais être NULL
- **Justification :** Traçabilité de la source des données
- **Type d'erreur :** Donnée manquante
- **Action en cas d'anomalie :** Rejeter la ligne
- **Code Great Expectations :**
  ```python
  batch.expect_column_values_to_not_be_null(column="laboratoire")
  ```

### 8.2 Source de données identifiée
- **Règle :** La colonne `source` doit être dans la liste des sources référencées (ex: "data.gouv.fr", "Agence de l'Eau", etc.)
- **Justification :** Traçabilité et audit
- **Type d'erreur :** Source inconnue
- **Action en cas d'anomalie :** Marquer comme "source à valider"
- **Code Great Expectations :**
  ```python
  authorized_sources = ["data.gouv.fr", "Agence de l'Eau", "SISE Eaux", ...]
  batch.expect_column_values_to_be_in_set(
      column="source",
      value_set=authorized_sources
  )
  ```

---

## 9. Résumé des Actions par Sévérité

| Sévérité | Type de Règle | Action | Exemple |
|----------|---------------|--------|---------|
| **CRITIQUE** | Donnée manquante, format invalide | **REJETER** la ligne | station_id NULL, date format invalide |
| **HAUTE** | Valeur aberrante dangereuse | **REJETER** ou **ALERTE** | E.coli > 100000 |
| **MOYENNE** | Incohérence ou doublon | **MARK** + Investigation | Doublon sur (station, date, param) |
| **BASSE** | Métadonnée manquante | **LOG** + Continuation | Source inconnue |

---
