# Guide d'Installation - Pipeline Eau

## Démarrage Ultra-Rapide (5 minutes)

### 1. Cloner le Dépôt
```bash
git clone https://github.com/<votre-nom>/eau-project.git
cd eau-project
```

### 2. Créer l'Environnement Virtuel
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Installer les Dépendances
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Tester Localement
```bash
# Télécharger un petit échantillon de données
python notebooks/local_pipeline/01_ingestion_bronze.py

# Si succès, continuez :
python notebooks/local_pipeline/02_transformation_silver.py
python notebooks/local_pipeline/03_aggregation_gold.py
```

---

## Installation Détaillée

### Prérequis
- **Python :** 3.9+ (vérifiez avec `python --version`)
- **Pip :** Installé avec Python
- **Git :** Pour cloner le dépôt
- **RAM :** Au minimum 4 GB (8 GB recommandé)

### Étape 1 : Cloner le Dépôt

```bash
# HTTPS (sans SSH)
git clone https://github.com/<votre-nom>/eau-project.git

# ou SSH (si configuré)
git clone git@github.com:<votre-nom>/eau-project.git

cd eau-project
```

### Étape 2 : Créer et Activer l'Environnement Virtuel

**IMPORTANT :** L'environnement virtuel isole votre projet des autres packages Python.

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```
Vous devriez voir `(venv)` au début de la ligne de commande.

#### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### Étape 3 : Installer les Dépendances

# Mettre à jour pip (important !)
pip install --upgrade pip setuptools wheel

# Installer les packages
pip install -r requirements.txt
```

Cela installe :
- `pandas` : Manipulation de données
- `numpy` : Calcul numérique
- `pyspark` : Traitement distribué
- `great-expectations` : Validation qualité
- `requests` : Téléchargement HTTP
- `pytest` : Tests unitaires

### Étape 4 : Vérifier l'Installation

```bash
python -c "import pandas, pyspark, great_expectations; print('Tous les packages sont installes')"
```

Cela installe :
- `pandas` : Manipulation de données
- `numpy` : Calcul numérique
- `pyspark` : Traitement distribué
- `great-expectations` : Validation qualité
- `requests` : Téléchargement HTTP
- `pytest` : Tests unitaires

### Étape 4️⃣ : Vérifier l'Installation

```bash
python -c "import pandas, pyspark, great_expectations; print('✅ Tous les packages sont installés')"
```

---

## Configuration Locale

### Créer le Fichier .env

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer .env avec vos paramètres (pour l'instant, laissez les valeurs par défaut)
```

### Vérifier la Structure

```bash
# Vérifier que les dossiers existent
ls -la notebooks/
ls -la data/
ls -la docs/
```

---

## Lancer le Pipeline Local

### Test Complet (toutes les étapes)

```bash
# 1. Ingestion (Bronze)
python notebooks/local_pipeline/01_ingestion_bronze.py

# Vérifiez : un fichier bronze_combined.csv devrait apparaître dans ./data/bronze/

# 2. Transformation (Silver)
python notebooks/local_pipeline/02_transformation_silver.py

# Vérifiez : un fichier silver_clean.csv devrait apparaître dans ./data/clean/

# 3. Agrégation (Gold)
python notebooks/local_pipeline/03_aggregation_gold.py

# Vérifiez : les fichiers Gold devraient apparaître dans ./data/gold/
```

### Lancer les Tests

```bash
# Exécuter tous les tests
pytest tests/ -v

# Avec couverture de code
pytest tests/ --cov=. --cov-report=html
```

---

## Troubleshooting

| Problème | Cause | Solution |
|----------|-------|----------|
| `ModuleNotFoundError: No module named 'pandas'` | Packages non installés | `pip install -r requirements.txt` |
| `(venv)` n'apparaît pas | Environnement non activé | Relancer `source venv/bin/activate` (macOS/Linux) ou `venv\Scripts\activate` (Windows) |
| `FileNotFoundError: bronze_combined.csv` | Étape 1 n'a pas fonctionné | Vérifier les logs. Peut être un problème de connexion à data.gouv.fr |
| `MemoryError` lors de PySpark | Pas assez de RAM | Réduire le volume de données ou augmenter la RAM système |
| Erreur d'encodage (ISO-8859-1) | Format CSV différent | Modifier `ENCODING` dans le notebook (ex: `utf-8`) |

---

## Dépendances Principales

### Core
- **pandas** : Manipulation de données tabulaires
- **numpy** : Calculs numériques
- **pyspark** : Traitement distribué (local ou Databricks)

### Validation
- **great-expectations** : Framework de validation de qualité

### Ingestion
- **requests** : Téléchargement HTTP

### Testing
- **pytest** : Framework de tests
- **pytest-cov** : Couverture de code

---

## Déploiement sur Azure Databricks

### Prérequis
- Accès Azure (Resource Group, Databricks Workspace)
- Token Databricks généré
- Stockage Azure (Data Lake Storage)

### Configuration

```bash
# 1. Installer la CLI Databricks
pip install databricks-cli

# 2. Configurer le token
databricks configure --token

# Entrez l'hôte et le token quand demandé

# 3. Uploader les notebooks
databricks workspace import-dir ./notebooks /Users/your-email@example.com/eau-project --language PYTHON --overwrite

# 4. Créer un job
databricks jobs create --json-file config/databricks_job_config.json
```

---

## Checklist de Démarrage

- [ ] Python 3.9+ installé
- [ ] Dépôt Git cloné
- [ ] Environnement virtuel créé et activé
- [ ] `pip install -r requirements.txt` exécuté sans erreurs
- [ ] `python notebooks/local_pipeline/01_ingestion_bronze.py` fonctionne
- [ ] Fichiers CSV générés dans `/data/`
- [ ] Les tests passent : `pytest tests/ -v`
- [ ] Fichier `.env` rempli avec les paramètres Azure

---

Consultez [docs/regles_qualite.md](../docs/regles_qualite.md) pour les règles de validation.
