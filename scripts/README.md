# 🛠️ Scripts Utiles

Ce dossier contient les **scripts essentiels** pour l'exploitation du pipeline eau.

## 📋 Scripts disponibles

### `trigger_pipeline.py`
Déclenche le pipeline Databricks à distance via l'API REST.

```bash
python scripts/trigger_pipeline.py
```

**Prérequis** : Configuration du fichier `.env` avec les variables Databricks.

### `check_gold_output.py`
Valide les fichiers Gold générés et affiche un aperçu des résultats métier.

```bash
python scripts/check_gold_output.py
```

**Utilité** : Vérification finale de la qualité des données agrégées.

---

**Note** : Ces scripts sont optimisés pour l'exploitation et la validation du pipeline de production.
