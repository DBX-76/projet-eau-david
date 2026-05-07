#  Migration vers URL Réelle (2025)

**Sujet :** Intégration de l'URL réelle data.gouv.fr (fichier ZIP 276 Mo)

---

##  Changements Apportés

### Notebook `01_ingestion_bronze.py`

1. **Support natif des fichiers ZIP** 
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

4. **Timeout**
   - 300 sec (5 minutes)
   - Nécessaire pour les 276 Mo (selon débit)

---

##  Utilisation de l'URL Réelle

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

## Flux Technique

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

