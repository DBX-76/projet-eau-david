# 🎯 QUICKSTART - Projet Eau (5 min)

## 🚀 Démarrage Immédiat

### 1. Activez l'environnement Python
```bash
# Windows
venv\Scripts\activate

# macOS/Linux  
source venv/bin/activate
```

### 2. Installez les dépendances
```bash
pip install -r requirements.txt
```

### 3. Lancez le pipeline complet
```bash
# Étape 1: Ingestion (Bronze)
python notebooks/01_ingestion_bronze.py

# Étape 2: Transformation (Silver)  
python notebooks/02_transformation_silver.py

# Étape 3: Agrégation (Gold)
python notebooks/03_aggregation_gold.py
```

---

## 📂 Fichiers Clés

| Fichier | Description |
|---------|-------------|
| `README.md` | Vue d'ensemble complète du projet |
| `docs/regles_qualite.md` | 📋 **Spécifications de validation** (super important !) |
| `docs/guide_installation.md` | Troubleshooting & installation détaillée |
| `requirements.txt` | Toutes les dépendances Python |
| `.gitignore` | Fichiers à ne pas committer |

---

## 📊 Structure Pipeline

```
data.gouv.fr 
    ↓
📦 Bronze (01_ingestion_bronze.py)
    ↓
🔧 Silver (02_transformation_silver.py) + Great Expectations
    ↓
⭐ Gold (03_aggregation_gold.py) → KPIs, Top 10, Tendances
```

---

## 🔄 Prochaines Étapes

1. **Lire les spécifications :** [docs/regles_qualite.md](docs/regles_qualite.md)
2. **Adapter les URLs :** Remplacer les URLs fictives par celles réelles de data.gouv.fr
3. **Configurer Azure :** Remplir `.env` avec vos paramètres Databricks
4. **Tester localement :** Valider le code avant le déploiement cloud
5. **Déployer :** Uploader sur Databricks quand les droits arrivent

---

## 📞 Support Rapide

- ❓ Question sur l'installation ? → `docs/guide_installation.md`
- ❓ Question sur les règles ? → `docs/regles_qualite.md`
- ❓ Question sur l'architecture ? → `README.md`

**Bon coding ! 🎉**
