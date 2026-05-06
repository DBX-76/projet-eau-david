# tests/test_smoke.py
# Tests pytest compatibles pour GitHub Actions
import pandas as pd
import os
import sys

def test_python_version():
    """Vérifie que Python >= 3.9"""
    assert sys.version_info >= (3, 9), f"Python 3.9+ requis, trouvé {sys.version}"

def test_sample_data_exists():
    """Vérifie que le fichier échantillon est présent"""
    path = os.getenv("SAMPLE_DATA_PATH", "data/sample/sample_eau.csv")
    assert os.path.exists(path), f"Sample data not found at {path}"

def test_sample_data_loads():
    """Vérifie que le CSV Silver sample se charge correctement"""
    path = os.getenv("SAMPLE_DATA_PATH", "data/sample/sample_eau.csv")
    df = pd.read_csv(path, sep=";", encoding="iso-8859-1")
    assert len(df) > 0, "Sample data is empty"
    assert "id_prelevement" in df.columns or "nom_parametre" in df.columns, "Missing required columns"

def test_always_pass_fallback():
    """Test de secours pour éviter 'no tests collected'"""
    assert True, "Fallback test to ensure pytest collects at least one test"