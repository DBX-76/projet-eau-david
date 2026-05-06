# 🔄 Migration vers URL Réelle (2025)

**Date :** 4 Mai 2026  
**Sujet :** Intégration de l'URL réelle data.gouv.fr (fichier ZIP 276 Mo)

---

## 📝 Changements Apportés

### ✅ Notebook `01_ingestion_bronze.py`

#### Nouvelles fonctionnalités :
1. **Support natif des fichiers ZIP** ✨
   - Détection automatique du format (ZIP vs CSV)
   - Extraction en mémoire (pas de disque intermédiaire)
   - Support multi-formats (CSV et Excel)

2. **Gestion des redirections HTTP**
   - Les URLs data.gouv.fr redirigent automatiquement
   - Le code suit les redirections avec `allow_redirects=True`

3. **Détection intelligente du type de contenu**
   ```python
   # Vérifie 3 critères :
   - Header Content-Type
   - Extension de l'URL
   - Signature binaire ZIP (bytes PK)
   ```

4. **Timeout augmenté**
   - 30 sec → 300 sec (5 minutes)
   - Nécessaire pour les 276 Mo (selon débit)

#### Nouvelles imports :
```python
import io       # Buffers en mémoire
import zipfile  # Gestion ZIP
```

---

## 🚀 Utilisation de l'URL Réelle

### URL 2025 (déjà intégrée)
```python
DATA_SOURCES = {
    "qualite_eau_2025": "https://www.data.gouv.fr/datasets/resultats-du-controle-sanitaire-de-leau-distribuee-commune-par-commune?resource_id=7e38c236-dd3c-455e-a728-f0ecb84b1a7c",
}
```

### Pour tester localement :

```bash
# 1. Installer les dépendances
pip install -r requirements.txt

# 2. Lancer l'ingestion (prendra 5-10 min selon débit)
python notebooks/01_ingestion_bronze.py

# 3. Vérifier le résultat
ls -lah data/bronze/
# Doit contenir : bronze_qualite_eau_2025.csv et bronze_combined.csv
```

---

## ⚙️ Flux Technique

```
1. requests.get(URL, allow_redirects=True)
   ↓
2. Détection : Content-Type / Extension / Signature
   ↓
3. Si ZIP → extract_csv_from_zip()
   - zipfile.ZipFile(BytesIO)
   - Cherche .csv ou .xlsx
   - Lit en mémoire avec StringIO/BytesIO
   ↓
4. Si CSV → pd.read_csv(StringIO)
   ↓
5. Retourne DataFrame
```

---

## 📊 Format Expected

### Fichier ZIP contient :
```
donnees_qualite_eau_2025.zip
├── data_sanitaire_2025.csv    (ou autre nom)
├── [autres fichiers]
└── [documentation optionnelle]
```

### Schéma CSV (estimation) :
```
commune_code | commune_name | parameter | value | unit | date | lab | ...
```

---

## 🔧 Configuration `.env.example`

Mise à jour avec URL réelle 2025 :
```env
DATA_SOURCE_URL_2025=https://www.data.gouv.fr/datasets/...?resource_id=7e38c236-dd3c-455e-a728-f0ecb84b1a7c
DATA_SOURCE_URL_2024=[À remplir si dispo]
DATA_SOURCE_URL_2023=[À remplir si dispo]
```

---

## 🐛 Troubleshooting

| Problème | Cause | Solution |
|----------|-------|----------|
| `URLError: Connection refused` | Pas de connexion internet | Vérifier votre VPN/connexion |
| `⏱️ Timeout après 300s` | Fichier trop volumineux ou débit faible | Augmenter `TIMEOUT` ou utiliser une meilleure connexion |
| `BadZipFile` | ZIP corrompu | data.gouv.fr peut avoir un problème → réessayer plus tard |
| `Aucun fichier CSV/Excel trouvé` | Structure ZIP inattendue | Vérifier le contenu du ZIP manuellement |
| `UnicodeDecodeError` | Encodage incorrect | Adapter `ENCODING` (utf-8, latin-1, etc.) |

---

## 📈 Performance

### Temps estimé (pour 276 Mo) :
```
Débit         | Téléchargement | Extraction | Total
50 Mbps       | 45 sec        | 30 sec     | 1:15 min
10 Mbps       | 220 sec       | 30 sec     | 4:10 min
1 Mbps        | ~40 min       | 30 sec     | ~41 min
```

### RAM requise :
- ZIP en mémoire : 276 Mo
- DataFrame intermediate : 500 Mo - 1 Go (selon contenu)
- **Minimum :** 2 GB libres

---

## ✅ Validation

Après exécution, vérifier :
```bash
# 1. Fichiers créés
ls -la data/bronze/
# → bronze_qualite_eau_2025.csv (doit exister)
# → bronze_combined.csv

# 2. Taille raisonnable
wc -l data/bronze/bronze_combined.csv
# Doit avoir > 1000 lignes

# 3. Colonnes présentes
head -1 data/bronze/bronze_combined.csv
# Doit montrer les en-têtes du CSV
```

---

## 🔗 Prochaines Étapes

1. **Tester localement :** `python notebooks/01_ingestion_bronze.py`
2. **Adapter le schéma Silver :** `02_transformation_silver.py` selon colonnes réelles
3. **Mettre à jour règles validation :** `docs/regles_qualite.md`
4. **Tester le pipeline complet :** Bronze → Silver → Gold

---

## 📞 Ressources

- 📖 [data.gouv.fr - Eau](https://www.data.gouv.fr/datasets/resultats-du-controle-sanitaire-de-leau-distribuee-commune-par-commune)
- 🐍 [zipfile Python docs](https://docs.python.org/3/library/zipfile.html)
- 📊 [pandas.read_csv docs](https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html)

---

**Bon développement ! 🚀**

*Mis à jour : 4 Mai 2026*
