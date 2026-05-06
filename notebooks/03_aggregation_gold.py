# ============================================================================
# NOTEBOOK 3 : AGRÉGATION - COUCHE GOLD
# ============================================================================
# Objectif : Créer des KPIs métier et agrégations pour analyse/visualisation
#            À partir des données Silver nettoyées et validées
# 
# Auteur : [À compléter]
# Date : Mai 2026
# Version : 1.0.0-alpha
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import os

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

SILVER_PATH = "./data/clean/silver_clean.csv"
GOLD_PATH = "./data/gold"
os.makedirs(GOLD_PATH, exist_ok=True)

# Paramètres de nettoyage
ENCODING = 'iso-8859-1'
SEPARATOR = ';'

# Seuils de conformité par paramètre (source : OMS / Réglementation EU)
CONFORMITY_THRESHOLDS = {
    "pH": {"min": 6.5, "max": 8.5, "type": "range"},
    "Nitrates": {"threshold": 50, "unit": "mg/L", "type": "max"},
    "Phosphates": {"threshold": 2.2, "unit": "mg/L", "type": "max"},
    "Ammonium": {"threshold": 0.5, "unit": "mg/L", "type": "max"},
    "E.coli": {"threshold": 0, "unit": "UFC/100mL", "type": "presence"},
    "Coliformes": {"threshold": 0, "unit": "UFC/100mL", "type": "presence"},
    "Turbidite": {"threshold": 0.5, "unit": "NTU", "type": "max"},
    "Conductivite": {"threshold": 2500, "unit": "µS/cm", "type": "max"},
}

# ============================================================================
# FONCTION 1 : CHARGER LES DONNÉES SILVER
# ============================================================================

def load_silver_data(filepath: str) -> pd.DataFrame:
    """Charge les données Silver nettoyées."""
    try:
        logger.info(f"📂 Chargement données Silver : {filepath}")
        df = pd.read_csv(filepath, sep=SEPARATOR, encoding=ENCODING)
        logger.info(f"✅ {len(df)} lignes chargées")
        return df
    except FileNotFoundError:
        logger.error(f"❌ Fichier non trouvé : {filepath}")
        return None
    except Exception as e:
        logger.error(f"❌ Erreur chargement : {e}")
        return None


# ============================================================================
# FONCTION 2 : KPIs GLOBAUX
# ============================================================================

def calculate_global_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Calcule les indicateurs clés globaux."""
    logger.info("\n📊 CALCUL DES KPIs GLOBAUX")
    
    kpis = {}
    
    # Bases
    kpis['total_records'] = len(df)
    if 'id_prelevement' in df.columns:
        kpis['total_samplings'] = df['id_prelevement'].nunique()
    
    # Couverture temporelle
    if 'date_prelevement' in df.columns:
        try:
            df['date_prelevement'] = pd.to_datetime(df['date_prelevement'], errors='coerce')
            kpis['min_date'] = df['date_prelevement'].min()
            kpis['max_date'] = df['date_prelevement'].max()
            kpis['days_covered'] = (kpis['max_date'] - kpis['min_date']).days
        except:
            kpis['days_covered'] = 0
    
    # Géographie
    if 'code_departement' in df.columns:
        kpis['departments_covered'] = df['code_departement'].nunique()
    if 'nom_commune' in df.columns:
        kpis['communes_covered'] = df['nom_commune'].nunique()
    
    # Paramètres
    if 'nom_parametre' in df.columns:
        kpis['parameters_analyzed'] = df['nom_parametre'].nunique()
    
    # Taux conformité global
    conformity_count = 0
    total_count = 0
    if 'nom_parametre' in df.columns and 'resultat' in df.columns:
        for param in df['nom_parametre'].unique():
            if pd.isnull(param):
                continue
            param_data = df[df['nom_parametre'] == param]['resultat'].dropna()
            if len(param_data) == 0:
                continue
            total_count += len(param_data)
            param_str = str(param).lower()
            if 'nitrate' in param_str:
                conformity_count += (param_data <= 50).sum()
            elif 'ph' in param_str:
                conformity_count += ((param_data >= 6.5) & (param_data <= 8.5)).sum()
            elif 'e.coli' in param_str or 'coliform' in param_str:
                conformity_count += (param_data == 0).sum()
            else:
                conformity_count += len(param_data)
    
    if total_count > 0:
        kpis['global_conformity_rate'] = round((conformity_count / total_count) * 100, 2)
    else:
        kpis['global_conformity_rate'] = 0.0
    
    # Qualité
    if 'quality_flag' in df.columns:
        quality_dist = df['quality_flag'].value_counts()
        kpis['quality_ok'] = quality_dist.get('OK', 0)
        kpis['quality_warning'] = quality_dist.get('WARNING', 0)
        kpis['quality_alert'] = quality_dist.get('ALERT', 0)
        kpis['quality_unknown'] = quality_dist.get('UNKNOWN', 0)
    
    logger.info(f"  ✅ {len(kpis)} KPIs générés")
    return pd.DataFrame([kpis])


# ============================================================================
# FONCTION 3 : AGRÉGATION PAR DÉPARTEMENT
# ============================================================================

def aggregate_by_department(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège par département avec score pollution."""
    logger.info("\n🗺️ AGRÉGATION PAR DÉPARTEMENT")
    
    if 'code_departement' not in df.columns:
        logger.warning("  ⚠️ Colonne 'code_departement' absente")
        return pd.DataFrame()
    
    dept_agg = df.groupby('code_departement', as_index=False).agg({
        'id_prelevement': 'nunique',
        'resultat': ['mean', 'std', 'min', 'max'],
        'nom_commune': 'nunique',
    }).round(3)
    
    dept_agg.columns = ['code_departement', 'samplings', 'avg_result', 'std_result', 'min_result', 'max_result', 'communes']
    
    # Ajouter alertes si présentes
    if 'quality_flag' in df.columns:
        alerts = df[df['quality_flag'] == 'ALERT'].groupby('code_departement').size().reset_index(name='alerts')
        dept_agg = dept_agg.merge(alerts, on='code_departement', how='left').fillna(0)
    else:
        dept_agg['alerts'] = 0
    
    # Score pollution
    max_result = df['resultat'].max()
    dept_agg['pollution_score'] = (
        (dept_agg['avg_result'] / max_result if max_result > 0 else 0) * 0.5 +
        (dept_agg['alerts'] / len(df) if len(df) > 0 else 0) * 0.5
    ).round(3)
    
    dept_agg = dept_agg.sort_values('pollution_score', ascending=False)
    logger.info(f"  ✅ {len(dept_agg)} départements analysés")
    return dept_agg


# ============================================================================
# FONCTION 4 : TOP 10 ET BOTTOM 10 COMMUNES
# ============================================================================

def get_best_worst_communes(df: pd.DataFrame, n: int = 10) -> tuple:
    """Identifie Top N et Bottom N communes."""
    logger.info(f"\n🏆 TOP {n} / BOTTOM {n} COMMUNES")
    
    if 'nom_commune' not in df.columns or 'resultat' not in df.columns:
        logger.warning("  ⚠️ Colonnes requises absentes")
        return pd.DataFrame(), pd.DataFrame()
    
    commune_quality = df.groupby('nom_commune', as_index=False).agg({
        'id_prelevement': 'nunique',
        'resultat': ['mean', 'std'],
    }).round(3)
    
    commune_quality.columns = ['nom_commune', 'samplings', 'avg_pollution', 'std_pollution']
    commune_quality = commune_quality[commune_quality['samplings'] >= 5]
    
    best = commune_quality.nsmallest(n, 'avg_pollution')[['nom_commune', 'samplings', 'avg_pollution']]
    worst = commune_quality.nlargest(n, 'avg_pollution')[['nom_commune', 'samplings', 'avg_pollution']]
    
    logger.info(f"  ✅ {len(best)} meilleures et {len(worst)} pires communes identifiées")
    return best, worst


# ============================================================================
# FONCTION 5 : SÉRIES TEMPORELLES
# ============================================================================

def analyze_timeseries(df: pd.DataFrame, parameter: str = "Nitrates") -> pd.DataFrame:
    """Analyse la série temporelle d'un paramètre."""
    logger.info(f"\n📈 SÉRIE TEMPORELLE - {parameter}")
    
    if 'nom_parametre' not in df.columns or 'date_prelevement' not in df.columns:
        logger.warning("  ⚠️ Colonnes requises absentes")
        return pd.DataFrame()
    
    try:
        df_param = df[df['nom_parametre'].str.lower() == parameter.lower()].copy()
        
        if len(df_param) == 0:
            logger.warning(f"  ⚠️ Aucun enregistrement pour {parameter}")
            return pd.DataFrame()
        
        df_param['date_prelevement'] = pd.to_datetime(df_param['date_prelevement'], errors='coerce')
        df_param['year_month'] = df_param['date_prelevement'].dt.to_period('M')
        
        ts_agg = df_param.groupby('year_month', as_index=False).agg({
            'resultat': ['mean', 'std', 'min', 'max', 'count']
        }).round(3)
        
        ts_agg.columns = ['year_month', 'avg_value', 'std_value', 'min_value', 'max_value', 'sample_count']
        ts_agg['year_month'] = ts_agg['year_month'].astype(str)
        
        logger.info(f"  ✅ {len(ts_agg)} mois analysés")
        return ts_agg
    except Exception as e:
        logger.error(f"  ❌ Erreur : {e}")
        return pd.DataFrame()


# ============================================================================
# FONCTION 6 : ANALYSE PARAMÈTRES CRITIQUES
# ============================================================================

def analyze_critical_parameters(df: pd.DataFrame) -> pd.DataFrame:
    """Analyse les paramètres critiques."""
    logger.info("\n⚠️ ANALYSE PARAMÈTRES CRITIQUES")
    
    critical_params = ['Nitrates', 'E.coli', 'pH', 'Coliformes', 'Pesticides']
    analysis = []
    
    for param in critical_params:
        if 'nom_parametre' not in df.columns:
            continue
        
        param_data = df[df['nom_parametre'].str.lower() == param.lower()]['resultat'].dropna()
        
        if len(param_data) == 0:
            continue
        
        threshold = CONFORMITY_THRESHOLDS.get(param, {}).get('threshold', None)
        
        analysis.append({
            'parameter': param,
            'count': len(param_data),
            'mean': round(param_data.mean(), 3),
            'median': round(param_data.median(), 3),
            'std': round(param_data.std(), 3),
            'min': round(param_data.min(), 3),
            'max': round(param_data.max(), 3),
            'threshold': threshold,
            'exceedances': (param_data > threshold).sum() if threshold else 0,
            'percent_exceeding': round((param_data > threshold).sum() / len(param_data) * 100, 2) if threshold else 0
        })
    
    analysis_df = pd.DataFrame(analysis)
    logger.info(f"  ✅ Analyse de {len(analysis_df)} paramètres critiques")
    return analysis_df


# ============================================================================
# FONCTION 7 : SAUVEGARDER LES FICHIERS GOLD
# ============================================================================

def save_gold_files(kpis: pd.DataFrame, dept_agg: pd.DataFrame, 
                   best_communes: pd.DataFrame, worst_communes: pd.DataFrame,
                   ts_nitrates: pd.DataFrame, critical_params: pd.DataFrame) -> bool:
    """Sauvegarde tous les fichiers Gold."""
    try:
        files_saved = []
        
        if not kpis.empty:
            filepath = os.path.join(GOLD_PATH, "gold_global_kpis.csv")
            kpis.to_csv(filepath, sep=SEPARATOR, encoding=ENCODING, index=False)
            files_saved.append("gold_global_kpis.csv")
        
        if not dept_agg.empty:
            filepath = os.path.join(GOLD_PATH, "gold_departments_pollution.csv")
            dept_agg.to_csv(filepath, sep=SEPARATOR, encoding=ENCODING, index=False)
            files_saved.append("gold_departments_pollution.csv")
        
        if not best_communes.empty:
            filepath = os.path.join(GOLD_PATH, "gold_communes_top10_best.csv")
            best_communes.to_csv(filepath, sep=SEPARATOR, encoding=ENCODING, index=False)
            files_saved.append("gold_communes_top10_best.csv")
        
        if not worst_communes.empty:
            filepath = os.path.join(GOLD_PATH, "gold_communes_top10_worst.csv")
            worst_communes.to_csv(filepath, sep=SEPARATOR, encoding=ENCODING, index=False)
            files_saved.append("gold_communes_top10_worst.csv")
        
        if not ts_nitrates.empty:
            filepath = os.path.join(GOLD_PATH, "gold_timeseries_nitrates.csv")
            ts_nitrates.to_csv(filepath, sep=SEPARATOR, encoding=ENCODING, index=False)
            files_saved.append("gold_timeseries_nitrates.csv")
        
        if not critical_params.empty:
            filepath = os.path.join(GOLD_PATH, "gold_critical_parameters.csv")
            critical_params.to_csv(filepath, sep=SEPARATOR, encoding=ENCODING, index=False)
            files_saved.append("gold_critical_parameters.csv")
        
        logger.info(f"💾 {len(files_saved)} fichiers Gold sauvegardés")
        return True
    except Exception as e:
        logger.error(f"❌ Erreur sauvegarde Gold : {e}")
        return False


# ============================================================================
# PIPELINE PRINCIPALE
# ============================================================================

def main():
    """Fonction principale : orchestre le pipeline Gold."""
    logger.info("\n" + "=" * 80)
    logger.info("🌟 DÉMARRAGE DU PIPELINE D'AGRÉGATION (GOLD)")
    logger.info(f"Timestamp : {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    # 1. Charger les données Silver
    df = load_silver_data(SILVER_PATH)
    if df is None:
        logger.error("❌ Impossible de charger Silver. Pipeline arrêté.")
        return
    
    logger.info(f"\n📊 Données Silver chargées : {len(df)} lignes × {len(df.columns)} colonnes")
    
    # 2. Calculer KPIs globaux
    kpis = calculate_global_kpis(df)
    
    # 3. Agrégations par département
    dept_agg = aggregate_by_department(df)
    
    # 4. Top 10 / Bottom 10 communes
    best_communes, worst_communes = get_best_worst_communes(df, n=10)
    
    # 5. Série temporelle Nitrates
    ts_nitrates = analyze_timeseries(df, parameter="Nitrates")
    
    # 6. Analyse paramètres critiques
    critical_params = analyze_critical_parameters(df)
    
    # 7. Sauvegarder tous les fichiers Gold
    success = save_gold_files(kpis, dept_agg, best_communes, worst_communes, ts_nitrates, critical_params)
    
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("📊 RÉSUMÉ DE L'AGRÉGATION GOLD")
        logger.info("=" * 80)
        
        if not kpis.empty:
            logger.info(f"Taux de conformité global : {kpis.iloc[0].get('global_conformity_rate', 'N/A')}%")
            logger.info(f"Prélèvements uniques : {kpis.iloc[0].get('total_samplings', 'N/A')}")
            logger.info(f"Départements couverts : {kpis.iloc[0].get('departments_covered', 'N/A')}")
            logger.info(f"Communes couvertes : {kpis.iloc[0].get('communes_covered', 'N/A')}")
        
        if not dept_agg.empty:
            logger.info(f"\n📍 Département le plus pollué : {dept_agg.iloc[0]['code_departement']} (score: {dept_agg.iloc[0]['pollution_score']})")
        
        if not best_communes.empty:
            logger.info(f"\n🥇 Meilleure commune : {best_communes.iloc[0]['nom_commune']} (pollution moyenne: {best_communes.iloc[0]['avg_pollution']})")
        
        if not worst_communes.empty:
            logger.info(f"🥉 Pire commune : {worst_communes.iloc[0]['nom_commune']} (pollution moyenne: {worst_communes.iloc[0]['avg_pollution']})")
        
        if not critical_params.empty:
            logger.info(f"\n⚠️ Paramètres critiques analysés : {len(critical_params)}")
            for _, row in critical_params.iterrows():
                logger.info(f"  - {row['parameter']}: {row['count']} mesures, {row['percent_exceeding']}% hors seuil")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ AGRÉGATION GOLD COMPLÈTE\n")
    else:
        logger.error("❌ Erreur lors de la sauvegarde Gold. Pipeline arrêté.")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️ Pipeline arrêté par l'utilisateur")
    except Exception as e:
        logger.critical(f"❌ Erreur critique : {e}")
        import traceback
        traceback.print_exc()
