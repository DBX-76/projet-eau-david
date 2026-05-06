# ============================================================================
# NOTEBOOK 3 : AGRÉGATION DES DONNÉES - COUCHE GOLD
# ============================================================================
# Description : Ce notebook réalise l'agrégation des données nettoyées de la couche Silver
#               pour créer des indicateurs clés (KPIs) et des analyses métier destinées
#               à l'analyse et à la visualisation.
#
# Objectif : À partir des données Silver validées, générer des agrégations globales,
#            des analyses par département, des classements de communes, des séries
#            temporelles et des analyses de paramètres critiques pour faciliter
#            la prise de décision.
#
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

# Chemins des données
SILVER_PATH = "./data/clean/silver_clean.csv"  # Fichier source nettoyé depuis la couche Silver
GOLD_PATH = "./data/gold"                      # Dossier de destination pour les agrégations Gold
os.makedirs(GOLD_PATH, exist_ok=True)

# Paramètres de formatage
ENCODING = 'iso-8859-1'  # Encodage des fichiers texte (support des caractères français)
SEPARATOR = ';'          # Séparateur de colonnes pour l'export CSV

# Seuils de conformité par paramètre pour l'évaluation qualité eau
# Sources : OMS (Organisation Mondiale de la Santé) et Réglementation Européenne
# Ces seuils définissent les limites acceptables pour la potabilité de l'eau
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
        logger.info(f"Chargement données Silver : {filepath}")
        df = pd.read_csv(filepath, sep=SEPARATOR, encoding=ENCODING)
        logger.info(f"{len(df)} lignes chargées")
        return df
    except FileNotFoundError:
        logger.error(f"Fichier non trouvé : {filepath}")
        return None
    except Exception as e:
        logger.error(f"Erreur chargement : {e}")
        return None


# ============================================================================
# FONCTION 2 : KPIs GLOBAUX
# ============================================================================

def calculate_global_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les indicateurs clés de performance (KPIs) globaux à partir des données Silver.

    Cette fonction génère des métriques globales incluant :
    - Statistiques de couverture (temporelle, géographique, paramètres)
    - Taux de conformité globale aux normes de qualité
    - Distribution des indicateurs de qualité (OK, WARNING, ALERT, UNKNOWN)

    Args:
        df (pd.DataFrame) : DataFrame Silver nettoyé

    Returns:
        pd.DataFrame : DataFrame contenant une ligne avec tous les KPIs calculés
    """
    logger.info("\nCALCUL DES KPIs GLOBAUX")
    
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
    
    logger.info(f"  {len(kpis)} KPIs générés")
    return pd.DataFrame([kpis])


# ============================================================================
# FONCTION 3 : AGRÉGATION PAR DÉPARTEMENT
# ============================================================================

def aggregate_by_department(df: pd.DataFrame) -> pd.DataFrame:
    """
    Réalise l'agrégation des données par département avec calcul d'un score de pollution.

    Pour chaque département, calcule :
    - Nombre de prélèvements et communes couvertes
    - Statistiques des résultats (moyenne, écart-type, min, max)
    - Nombre d'alertes qualité
    - Score de pollution composite basé sur la moyenne et les alertes

    Args:
        df (pd.DataFrame) : DataFrame Silver nettoyé

    Returns:
        pd.DataFrame : DataFrame agrégé par département, trié par score de pollution décroissant
    """
    logger.info("\nAGRÉGATION PAR DÉPARTEMENT")
    
    if 'code_departement' not in df.columns:
        logger.warning("  Colonne 'code_departement' absente")
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
    logger.info(f"  {len(dept_agg)} départements analysés")
    return dept_agg


# ============================================================================
# FONCTION 4 : TOP 10 ET BOTTOM 10 COMMUNES
# ============================================================================

def get_best_worst_communes(df: pd.DataFrame, n: int = 10) -> tuple:
    """
    Identifie les N meilleures et N pires communes en termes de qualité de l'eau.

    La classification est basée sur la moyenne des résultats de pollution,
    en ne considérant que les communes avec au moins 5 prélèvements
    pour assurer la représentativité des données.

    Args:
        df (pd.DataFrame) : DataFrame Silver nettoyé
        n (int) : Nombre de communes à retourner pour chaque catégorie (défaut: 10)

    Returns:
        tuple : (pd.DataFrame meilleures communes, pd.DataFrame pires communes)
                Chaque DataFrame contient nom_commune, samplings, avg_pollution
    """
    logger.info(f"\nTOP {n} / BOTTOM {n} COMMUNES")
    
    if 'nom_commune' not in df.columns or 'resultat' not in df.columns:
        logger.warning("  Colonnes requises absentes")
        return pd.DataFrame(), pd.DataFrame()
    
    commune_quality = df.groupby('nom_commune', as_index=False).agg({
        'id_prelevement': 'nunique',
        'resultat': ['mean', 'std'],
    }).round(3)
    
    commune_quality.columns = ['nom_commune', 'samplings', 'avg_pollution', 'std_pollution']
    commune_quality = commune_quality[commune_quality['samplings'] >= 5]
    
    best = commune_quality.nsmallest(n, 'avg_pollution')[['nom_commune', 'samplings', 'avg_pollution']]
    worst = commune_quality.nlargest(n, 'avg_pollution')[['nom_commune', 'samplings', 'avg_pollution']]
    
    logger.info(f"  {len(best)} meilleures et {len(worst)} pires communes identifiées")
    return best, worst


# ============================================================================
# FONCTION 5 : SÉRIES TEMPORELLES
# ============================================================================

def analyze_timeseries(df: pd.DataFrame, parameter: str = "Nitrates") -> pd.DataFrame:
    """
    Analyse l'évolution temporelle d'un paramètre spécifique par mois.

    Agrège les données par mois pour fournir des statistiques
    (moyenne, écart-type, min, max, nombre d'échantillons)
    permettant d'observer les tendances saisonnières et l'évolution.

    Args:
        df (pd.DataFrame) : DataFrame Silver nettoyé
        parameter (str) : Nom du paramètre à analyser (défaut: "Nitrates")

    Returns:
        pd.DataFrame : DataFrame avec colonnes year_month, avg_value, std_value,
                      min_value, max_value, sample_count
    """
    logger.info(f"\nSÉRIE TEMPORELLE - {parameter}")
    
    if 'nom_parametre' not in df.columns or 'date_prelevement' not in df.columns:
        logger.warning("  Colonnes requises absentes")
        return pd.DataFrame()
    
    try:
        df_param = df[df['nom_parametre'].str.lower() == parameter.lower()].copy()
        
        if len(df_param) == 0:
            logger.warning(f"  Aucun enregistrement pour {parameter}")
            return pd.DataFrame()
        
        df_param['date_prelevement'] = pd.to_datetime(df_param['date_prelevement'], errors='coerce')
        df_param['year_month'] = df_param['date_prelevement'].dt.to_period('M')
        
        ts_agg = df_param.groupby('year_month', as_index=False).agg({
            'resultat': ['mean', 'std', 'min', 'max', 'count']
        }).round(3)
        
        ts_agg.columns = ['year_month', 'avg_value', 'std_value', 'min_value', 'max_value', 'sample_count']
        ts_agg['year_month'] = ts_agg['year_month'].astype(str)
        
        logger.info(f"  {len(ts_agg)} mois analysés")
        return ts_agg
    except Exception as e:
        logger.error(f"  Erreur : {e}")
        return pd.DataFrame()


# ============================================================================
# FONCTION 6 : ANALYSE PARAMÈTRES CRITIQUES
# ============================================================================

def analyze_critical_parameters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyse approfondie des paramètres critiques pour la qualité de l'eau.

    Pour chaque paramètre critique (Nitrates, E.coli, pH, etc.),
    calcule les statistiques descriptives et évalue le taux de dépassement
    des seuils réglementaires.

    Args:
        df (pd.DataFrame) : DataFrame Silver nettoyé

    Returns:
        pd.DataFrame : DataFrame avec statistiques par paramètre critique,
                      incluant seuils et taux de dépassement
    """
    logger.info("\nANALYSE PARAMÈTRES CRITIQUES")
    
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
    logger.info(f"  Analyse de {len(analysis_df)} paramètres critiques")
    return analysis_df


# ============================================================================
# FONCTION 7 : SAUVEGARDER LES FICHIERS GOLD
# ============================================================================

def save_gold_files(kpis: pd.DataFrame, dept_agg: pd.DataFrame,
                   best_communes: pd.DataFrame, worst_communes: pd.DataFrame,
                   ts_nitrates: pd.DataFrame, critical_params: pd.DataFrame) -> bool:
    """
    Sauvegarde tous les fichiers agrégés de la couche Gold au format CSV.

    Les fichiers sauvegardés incluent :
    - KPIs globaux
    - Agrégations par département
    - Classements des communes (top/bottom)
    - Série temporelle des nitrates
    - Analyse des paramètres critiques

    Args:
        kpis (pd.DataFrame) : KPIs globaux
        dept_agg (pd.DataFrame) : Agrégations par département
        best_communes (pd.DataFrame) : Meilleures communes
        worst_communes (pd.DataFrame) : Pires communes
        ts_nitrates (pd.DataFrame) : Série temporelle nitrates
        critical_params (pd.DataFrame) : Analyse paramètres critiques

    Returns:
        bool : True si toutes les sauvegardes ont réussi, False sinon
    """
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
        
        logger.info(f" {len(files_saved)} fichiers Gold sauvegardés")
        return True
    except Exception as e:
        logger.error(f"Erreur sauvegarde Gold : {e}")
        return False


# ============================================================================
# PIPELINE PRINCIPALE
# ============================================================================

def main():
    """
    Fonction principale qui orchestre l'agrégation des données vers la couche Gold.

    Cette fonction exécute séquentiellement les étapes suivantes :
    - Chargement des données Silver nettoyées
    - Calcul des indicateurs clés globaux (KPIs)
    - Agrégation des données par département
    - Identification des meilleures et pires communes
    - Analyse des séries temporelles pour les nitrates
    - Analyse des paramètres critiques
    - Sauvegarde de tous les fichiers agrégés dans la couche Gold
    """
    logger.info("\n" + "=" * 80)
    logger.info("DÉMARRAGE DU PIPELINE D'AGRÉGATION (GOLD)")
    logger.info(f"Timestamp : {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    # Étape 1 : Chargement des données nettoyées depuis la couche Silver
    df = load_silver_data(SILVER_PATH)
    if df is None:
        logger.error("Chargement des données Silver impossible — arrêt du pipeline")
        return

    logger.info(f"\nDonnées Silver chargées : {len(df)} lignes × {len(df.columns)} colonnes")

    # Étape 2 : Calcul des indicateurs clés globaux (KPIs)
    kpis = calculate_global_kpis(df)

    # Étape 3 : Agrégation des données par département avec scores de pollution
    dept_agg = aggregate_by_department(df)

    # Étape 4 : Identification des 10 meilleures et 10 pires communes
    best_communes, worst_communes = get_best_worst_communes(df, n=10)

    # Étape 5 : Analyse des séries temporelles pour les nitrates
    ts_nitrates = analyze_timeseries(df, parameter="Nitrates")

    # Étape 6 : Analyse approfondie des paramètres critiques
    critical_params = analyze_critical_parameters(df)

    # Étape 7 : Sauvegarde de tous les fichiers agrégés dans la couche Gold
    success = save_gold_files(kpis, dept_agg, best_communes, worst_communes, ts_nitrates, critical_params)
    
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("RÉSUMÉ DE L'AGRÉGATION GOLD")
        logger.info("=" * 80)
        
        if not kpis.empty:
            logger.info(f"Taux de conformité global : {kpis.iloc[0].get('global_conformity_rate', 'N/A')}%")
            logger.info(f"Prélèvements uniques : {kpis.iloc[0].get('total_samplings', 'N/A')}")
            logger.info(f"Départements couverts : {kpis.iloc[0].get('departments_covered', 'N/A')}")
            logger.info(f"Communes couvertes : {kpis.iloc[0].get('communes_covered', 'N/A')}")
        
        if not dept_agg.empty:
            logger.info(f"\nDépartement le plus pollué : {dept_agg.iloc[0]['code_departement']} (score: {dept_agg.iloc[0]['pollution_score']})")
        
        if not best_communes.empty:
            logger.info(f"\nMeilleure commune : {best_communes.iloc[0]['nom_commune']} (pollution moyenne: {best_communes.iloc[0]['avg_pollution']})")
        
        if not worst_communes.empty:
            logger.info(f"Pire commune : {worst_communes.iloc[0]['nom_commune']} (pollution moyenne: {worst_communes.iloc[0]['avg_pollution']})")
        
        if not critical_params.empty:
            logger.info(f"\nParamètres critiques analysés : {len(critical_params)}")
            for _, row in critical_params.iterrows():
                logger.info(f"  - {row['parameter']}: {row['count']} mesures, {row['percent_exceeding']}% hors seuil")
        
        logger.info("\n" + "=" * 80)
        logger.info("AGRÉGATION GOLD COMPLÈTE\n")
    else:
        logger.error("Erreur lors de la sauvegarde Gold. Pipeline arrêté.")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nPipeline arrêté par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur critique : {e}")
        import traceback
        traceback.print_exc()
