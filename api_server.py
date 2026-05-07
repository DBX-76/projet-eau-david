# api_server.py
from fastapi import FastAPI, HTTPException
import json
import os

app = FastAPI(title="Pipeline Qualite Eau - API Exposition", version="1.0")

# Chemin relatif vers le fichier JSON genere par le notebook Databricks
JSON_PATH = os.path.join(os.path.dirname(__file__), "exports", "api_exposition.json")

def load_data():
    if not os.path.exists(JSON_PATH):
        raise HTTPException(status_code=503, detail="Fichier de donnees introuvable. Verifiez le dossier exports/.")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

@app.get("/api/health")
def health_check():
    return {"status": "operational", "message": "API Qualite Eau fonctionnelle"}

@app.get("/api/kpis")
def get_kpis():
    data = load_data()
    return {"kpis": data.get("kpis", [])}

@app.get("/api/departments")
def get_departments():
    data = load_data()
    return {"top_departments": data.get("top_departments_polluted", [])}

@app.get("/api/parameters")
def get_parameters():
    data = load_data()
    return {"critical_parameters": data.get("critical_parameters_summary", [])}

# Execution locale : python api_server.py
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)