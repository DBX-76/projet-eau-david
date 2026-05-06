# 🛠️ Scripts de Développement

Ce dossier contient les **outils de diagnostic et vérification** utilisés lors du développement du pipeline eau.

Ces scripts ne sont **pas** destinés à la production, mais plutôt aux développeurs pour :
- Valider la qualité des données
- Vérifier les sorties intermédiaires
- Diagnostiquer les problèmes

## 📋 Scripts disponibles

### `check_gold_output.py`
Valide les fichiers Gold générés et affiche un aperçu des résultats.

```bash
python scripts/check_gold_output.py
```

### `check_silver.py`
Vérify les données de la couche Silver nettoyée.

```bash
python scripts/check_silver.py
```

### `quick_check.py`
Diagnostic rapide des données brutes Bronze.

```bash
python scripts/quick_check.py
```

### `quick_check_silver.py`
Diagnostic rapide de la couche Silver.

```bash
python scripts/quick_check_silver.py
```

### `analyze_zip.py`
Analyse la structure du ZIP d'ingestion.

```bash
python scripts/analyze_zip.py
```

---

**Note** : Ces scripts sont fournis à titre informatif. Pour une utilisation en production, intégrez la logique dans le module `src/eau/`.
