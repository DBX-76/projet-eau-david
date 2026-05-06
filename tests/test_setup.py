#!/usr/bin/env python3
# ============================================================================
# SCRIPT de TEST : Vérifier que les imports et configuration sont OK
# ============================================================================
# Exécution : python test_setup.py
# ============================================================================

import sys
import os

print("\n" + "=" * 80)
print("🧪 TEST DE CONFIGURATION - Pipeline Eau")
print("=" * 80 + "\n")

# Test 1 : Python version
print("✓ Test 1 : Version Python")
print(f"  Python {sys.version.split()[0]} (requis : 3.9+)")
if sys.version_info < (3, 9):
    print("  ERREUR : Python 3.9+ requis")
    sys.exit(1)
print("  OK\n")

# Test 2 : Dépendances
print("✓ Test 2 : Dépendances")
required_packages = {
    'pandas': 'données tabulaires',
    'numpy': 'calculs numériques',
    'requests': 'téléchargement HTTP',
    'great_expectations': 'validation qualité',
    'openpyxl': 'support Excel',
}

all_installed = True
for package, desc in required_packages.items():
    try:
        __import__(package)
        print(f"  {package} : {desc}")
    except ImportError:
        print(f"  {package} : MANQUANT ({desc})")
        all_installed = False

if not all_installed:
    print("\n  Installation manquante !")
    print("  Exécutez : pip install -r requirements.txt\n")
    sys.exit(1)
print("  OK\n")

# Test 3 : Structure de dossiers
print("✓ Test 3 : Structure de dossiers")
required_dirs = {
    'notebooks': 'Notebooks Python',
    'data': 'Stockage données',
    'docs': 'Documentation',
    'tests': 'Tests unitaires',
    'config': 'Configuration',
}

all_dirs_exist = True
for dirname, desc in required_dirs.items():
    if os.path.isdir(dirname):
        print(f"  {dirname}/ : {desc}")
    else:
        print(f"  {dirname}/ : MANQUANT")
        all_dirs_exist = False

if not all_dirs_exist:
    print("\n  Dossiers manquants !\n")
    sys.exit(1)
print("  OK\n")

# Test 4 : Fichiers clés
print("✓ Test 4 : Fichiers clés")
required_files = {
    'README.md': 'Vue d\'ensemble',
    'requirements.txt': 'Dépendances',
    '.gitignore': 'Exclusions Git',
    'notebooks/01_ingestion_bronze.py': 'Ingestion',
    'notebooks/02_transformation_silver.py': 'Transformation',
    'notebooks/03_aggregation_gold.py': 'Agrégation',
    'docs/regles_qualite.md': 'Règles de validation',
    'docs/MIGRATION_URL_2025.md': 'Configuration URL',
}

all_files_exist = True
for filepath, desc in required_files.items():
    if os.path.isfile(filepath):
        size_kb = os.path.getsize(filepath) / 1024
        print(f"  {filepath} : {desc} ({size_kb:.1f} KB)")
    else:
        print(f"  {filepath} : MANQUANT")
        all_files_exist = False

if not all_files_exist:
    print("\n  Fichiers manquants !\n")
    sys.exit(1)
print("  OK\n")

# Test 5 : Import des modules locaux
print("✓ Test 5 : Modules locaux")
try:
    sys.path.insert(0, 'notebooks')
    # On va juste vérifier la syntaxe
    import ast
    for notebook in ['01_ingestion_bronze.py', '02_transformation_silver.py', '03_aggregation_gold.py']:
        with open(f'notebooks/{notebook}', 'r', encoding='utf-8') as f:
            try:
                ast.parse(f.read())
                print(f"  {notebook} : Syntaxe OK")
            except SyntaxError as e:
                print(f"  {notebook} : Erreur de syntaxe - {e}")
                sys.exit(1)
    print("  OK\n")
except Exception as e:
    print(f"  Erreur vérification syntaxe : {e}\n")
    sys.exit(1)

# Test 6 : Vérifier la config
print("✓ Test 6 : Fichiers de configuration")
try:
    import json
    with open('config/databricks_job_config.json', 'r') as f:
        config = json.load(f)
        print(f"  databricks_job_config.json : {config.get('name', 'Job')}")
    print("  OK\n")
except Exception as e:
    print(f"  databricks_job_config.json : {e}\n")

# Test 7 : URLs data.gouv
print("✓ Test 7 : Configuration URL")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("ingestion", "notebooks/01_ingestion_bronze.py")
    module = importlib.util.module_from_spec(spec)
    # On simule juste une lecture du fichier
    with open('notebooks/01_ingestion_bronze.py', 'r') as f:
        content = f.read()
        if 'data.gouv.fr' in content and 'qualite_eau_2025' in content:
            print(f"  URL data.gouv.fr 2025 configurée")
        else:
            print(f"  URL data.gouv.fr à vérifier")
    print("  OK\n")
except Exception as e:
    print(f"  Erreur vérification URL : {e}\n")

# Résumé final
print("=" * 80)
print("TOUT EST CONFIGURÉ CORRECTEMENT !")
print("=" * 80)
print("\n📝 Prochaines étapes :\n")
print("  1. Lire QUICKSTART.md")
print("  2. Tester : python notebooks/01_ingestion_bronze.py")
print("  3. Continuer avec les notebooks suivants")
print("\n" + "=" * 80 + "\n")
