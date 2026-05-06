# 🤝 Guide de Contribution

Merci de vouloir contribuer à **eau-project** ! Ce guide explique comment participer efficacement.

---

## 📋 Code de conduite

- ✅ Respectez les autres contributeurs
- ✅ Testez votre code avant de proposer
- ✅ Documentez vos changements
- ✅ Suivez les conventions du projet

---

## 🚀 Workflow de contribution

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/eau-project.git
cd eau-project
git checkout -b feature/votre-feature
```

### 2. Développer & Tester

```bash
# Installer les dépendances
pip install -r requirements.txt
pip install -e ".[dev]"

# Exécuter les tests
pytest tests/ -v

# Vérifier le formatage
black notebooks/ src/
isort notebooks/ src/
```

### 3. Commit & Push

```bash
git add .
git commit -m "feat: description claire de votre feature"
git push origin feature/votre-feature
```

### 4. Pull Request

- Ouvrir une PR sur GitHub
- Décrire les changements apportés
- Lier les issues liées (`Fixes #123`)
- Attendre la review

---

## 📝 Convention de commits

Format : `type(scope): description`

**Types :**
- `feat` — Nouvelle fonctionnalité
- `fix` — Correction de bug
- `docs` — Documentation
- `style` — Formatage (pas de changement logique)
- `refactor` — Restructuration (pas de changement fonctionnel)
- `test` — Ajout/modification de tests
- `chore` — Maintenance, deps

**Exemples :**
```
feat(silver): ajouter validation pH
fix(bronze): corriger parsing du ZIP
docs(readme): clarifier architecture
test(gold): ajouter tests KPI global
```

---

## 🔍 Standards de Code

### Python

- **Linter :** flake8
- **Formatter :** black (100 car/ligne)
- **Import sorter :** isort
- **Type hints :** Recommandés (graduel)

```bash
black --line-length=100 notebooks/
isort --profile=black notebooks/
flake8 notebooks/ --max-line-length=100
```

### Docstrings

```python
def calculate_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les KPIs globaux de qualité d'eau.
    
    Args:
        df: DataFrame Silver nettoyé (12.5M+ lignes)
    
    Returns:
        DataFrame avec 1 ligne × 13 colonnes de KPIs
    
    Raises:
        ValueError: Si df ne contient pas les colonnes requises
    """
    pass
```

---

## 🧪 Tests

- **Framework :** pytest
- **Couverture minimale :** 80%
- **Localisation :** `tests/test_*.py`

```bash
# Exécuter tous les tests
pytest tests/ -v

# Avec couverture
pytest tests/ --cov=src/eau --cov-report=html

# Test spécifique
pytest tests/test_silver.py::test_deduplication -v
```

---

## 📚 Structure pour contribuer

```
Pour ajouter une feature :

1. FEATURE BRANCH
   git checkout -b feature/ma-feature

2. DÉVELOPPEMENT
   - Modifiez src/eau/*.py OU notebooks/*.py
   - Écrivez des tests dans tests/test_*.py
   - Mettez à jour la documentation

3. TESTS LOCAUX
   pytest tests/ -v

4. COMMIT
   git commit -m "feat(module): description"

5. PULL REQUEST
   - Clique sur "Compare & pull request"
   - Description détaillée
   - Attendre la review ✅
```

---

## 📌 Points d'amélioration courants

| Domaine | Aide Bienvenue |
|---------|---|
| **Bronze** | Optimisation ZIP parsing, gestion encodages alternés |
| **Silver** | Améliorer jointures, réduire temps dedup |
| **Gold** | Ajouter plus d'agrégations métier, KPIs régionaux |
| **Tests** | Tests unitaires, fixtures, mocks |
| **Docs** | Clarifier la documentation, ajouter diagrammes |
| **CI/CD** | GitHub Actions, déploiement auto |

---

## ❓ Questions ?

- **Issues :** Poser une question via GitHub Issues
- **Discussions :** Utiliser les GitHub Discussions
- **Email :** contact@eau-project.local

---

Merci pour votre contribution ! 🙏
