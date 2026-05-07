import os
import requests
from dotenv import load_dotenv

# Charge les variables depuis le fichier .env s'il existe
load_dotenv()

def trigger_pipeline():
    host = os.getenv("DATABRICKS_HOST")
    token = os.getenv("DATABRICKS_TOKEN")
    job_id = os.getenv("DATABRICKS_JOB_ID")

    if not all([host, token, job_id]):
        raise ValueError("Les variables DATABRICKS_HOST, DATABRICKS_TOKEN et DATABRICKS_JOB_ID doivent être définies.")

    url = f"{host}/api/2.1/jobs/run-now"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"job_id": int(job_id)}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    result = trigger_pipeline()
    print(f"Pipeline déclenché. Run ID : {result.get('run_id')}")