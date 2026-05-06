# ============================================================================
# NOTEBOOK 2 : TRANSFORMATION - COUCHE SILVER
# ============================================================================
# Objectif : Nettoyer, valider et standardiser les données brutes (Bronze)
#            Utilise Great Expectations v0.18+ (nouvelle API Fluent)
#
# Date : Mai 2026
# Version : 2.0.0
# ============================================================================

import pandas as pd
import numpy as np
from datetime import datetime
import logging
import os
import gc

# Great Expectations — import au niveau module pour que les helpers y aient accès
try:
    import great_expectations as gx
    import great_expectations.expectations as gxe
    GX_AVAILABLE = True
except (ImportError, AttributeError, ModuleNotFoundError) as _gx_err:
    GX_AVAILABLE = False
    gx  = None
    gxe = None
    logging.getLogger(__name__).warning(
        f"Great Expectations non disponible : {_gx_err}"
    )

# ============================================================================
# CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BRONZE_PATH = "./data/bronze/bronze_combined.csv"
SILVER_PATH = "./data/clean"
GX_DOCS_PATH = "./gx"          # Dossier racine Great Expectations
os.makedirs(SILVER_PATH, exist_ok=True)
os.makedirs(GX_DOCS_PATH, exist_ok=True)

ENCODING  = 'iso-8859-1'
SEPARATOR = ';'

# Plages de valeurs acceptables par paramètre (métier)
# Sources : directive 98/83/CE + arrêté du 11 janvier 2007 (eau potable France)
# Le pH est mesuré aussi sur eaux brutes/intermédiaires → plage élargie à [4, 11]
# Les dépassements signalés en WARNING sont des non-conformités réelles, pas des erreurs
PARAMETER_RANGES = {
    "pH":           (4.0,  11.0),   # eau potable [6.5-9.0], eau brute jusqu'à 4/11
    "Nitrates":     (0,    500),     # limite qualité 50 mg/L, référence 0 ; 500 = seuil extrême
    "Phosphates":   (0,    50),      # élargi : eaux brutes eutrophisées peuvent dépasser 20
    "Ammonium":     (0,    50),      # limite qualité 0.5 mg/L, eaux brutes peuvent être élevées
    "E.coli":       (0,    100000),  # UFC/100mL — eaux brutes non traitées
    "Coliformes":   (0,    500000),  # élargi pour eaux brutes
    "Turbidite":    (0,    10000),   # NTU — crues peuvent dépasser 1000
    "Conductivite": (0,    5000),    # µS/cm — eaux saumâtres/minérales > 2500
}

# Limites géographiques France métropolitaine
GEO_BOUNDS = {
    "latitude":  (41.0, 51.5),
    "longitude": (-5.5,  8.5),
}


# ============================================================================
# GREAT EXPECTATIONS — HELPERS
# ============================================================================

def _get_gx_context():
    """
    Crée (ou réutilise) un DataContext éphémère en mémoire.

    On utilise get_context() sans argument pour obtenir un EphemeralDataContext :
    - Aucun fichier YAML à maintenir
    - Compatible avec une exécution script ou notebook
    - 100 % API v0.18+ (Fluent API)

    Returns:
        gx.DataContext | None
    """
    try:
        import great_expectations as gx
        context = gx.get_context()          # EphemeralDataContext
        logger.info(f"  Great Expectations {gx.__version__} — contexte éphémère initialisé")
        return context
    except Exception as e:
        logger.warning(f"  Impossible d'initialiser GX : {e}")
        return None


def _build_expectation_suite(context, suite_name: str):
    """
    Crée (ou écrase) une ExpectationSuite dans le contexte.

    Args:
        context  : DataContext GX
        suite_name (str) : Nom de la suite

    Returns:
        ExpectationSuite
    """
    # Supprimer si elle existe déjà (évite les conflits entre runs)
    try:
        context.suites.delete(suite_name)
    except Exception:
        pass

    suite = context.suites.add(
        gx.ExpectationSuite(name=suite_name)
    )
    return suite


def _add_expectations(suite, df_columns: list) -> None:
    """
    Ajoute toutes les attentes métier à la suite.

    L'API Fluent v0.18+ : on instancie des objets Expectation
    et on les ajoute via suite.add_expectation().

    Args:
        suite       : ExpectationSuite GX
        df_columns  : Liste des colonnes disponibles dans le DataFrame
    """
    import great_expectations.expectations as gxe

    # ── Colonnes critiques : pas de NULL ────────────────────────────────────
    # id_prelevement et nom_parametre : jamais NULL (clés métier)
    for col in ['id_prelevement', 'nom_parametre']:
        if col in df_columns:
            suite.add_expectation(
                gxe.ExpectColumnValuesToNotBeNull(column=col)
            )
    # resultat : peut être NULL pour les paramètres qualitatifs (ASPECT, etc.)
    # On tolère jusqu'à 2 % de NULL — ajustez si votre jeu de données le justifie
    if 'resultat' in df_columns:
        suite.add_expectation(
            gxe.ExpectColumnValuesToNotBeNull(column='resultat', mostly=0.98)
        )

    # ── Types attendus ───────────────────────────────────────────────────────
    if 'resultat' in df_columns:
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeOfType(column='resultat', type_='float64')
        )

    if 'date_prelevement' in df_columns:
        # Format ISO 8601 (YYYY-MM-DD)
        suite.add_expectation(
            gxe.ExpectColumnValuesToMatchRegex(
                column='date_prelevement',
                regex=r'^\d{4}-\d{2}-\d{2}$',
                mostly=0.95   # Tolérance 5 % pour les NaT/None résiduels
            )
        )

    # ── Unicité de la clé composite ──────────────────────────────────────────
    key_cols = [c for c in ['id_prelevement', 'code_parametre'] if c in df_columns]
    if len(key_cols) == 2:
        suite.add_expectation(
            gxe.ExpectCompoundColumnsToBeUnique(column_list=key_cols)
        )

    # ── Plages numériques ────────────────────────────────────────────────────
    if 'resultat' in df_columns:
        # La colonne resultat doit être ≥ 0 dans l'ensemble (règle générale)
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeBetween(
                column='resultat',
                min_value=0,
                mostly=0.98   # 2 % de tolérance (valeurs négatives codées)
            )
        )

    # ── Colonnes obligatoires dans le schéma ─────────────────────────────────
    required = [c for c in ['id_prelevement', 'nom_parametre', 'resultat'] if c in df_columns]
    if required:
        suite.add_expectation(
            gxe.ExpectTableColumnsToMatchSet(
                column_set=required,
                exact_match=False     # D'autres colonnes peuvent exister
            )
        )

    # ── quality_flag : valeurs connues ───────────────────────────────────────
    if 'quality_flag' in df_columns:
        suite.add_expectation(
            gxe.ExpectColumnValuesToBeInSet(
                column='quality_flag',
                value_set=['OK', 'WARNING', 'ALERT', 'UNKNOWN']
            )
        )

    logger.info(f"  {len(suite.expectations)} attentes définies dans la suite")


def validate_with_great_expectations(df: pd.DataFrame) -> dict:
    """
    Valide le DataFrame avec Great Expectations v0.18+ (API Fluent).

    Workflow GX v0.18 :
      1. get_context()                     → EphemeralDataContext
      2. context.suites.add(suite)         → ExpectationSuite
      3. context.data_sources.add_pandas() → PandasDatasource
      4. datasource.add_dataframe_asset()  → DataFrameAsset
      5. asset.add_batch_definition_whole_dataframe()  → BatchDefinition
      6. batch_def.get_batch(batch_parameters)         → Batch
      7. context.run_validation_definition(...)  OU
         context.run_checkpoint(...)             → ValidationResult

    Args:
        df (pd.DataFrame) : DataFrame Silver à valider

    Returns:
        dict : {'success': bool, 'statistics': dict, 'results': list, 'skipped': bool}
    """
        logger.info("\nVALIDATION GREAT EXPECTATIONS (v0.18+)")

    if not GX_AVAILABLE:
        logger.warning("  Great Expectations non installé — validation ignorée")
        return {'success': True, 'skipped': True}

    # ── Initialiser le contexte ──────────────────────────────────────────────
    context = _get_gx_context()
    if context is None:
        logger.warning("  Contexte GX non disponible — validation ignorée")
        return {'success': True, 'skipped': True}

    try:
        SUITE_NAME  = "water_quality_suite"
        SOURCE_NAME = "silver_pandas_source"
        ASSET_NAME  = "silver_dataframe"

        # ── 1. Suite d'attentes ──────────────────────────────────────────────
        suite = _build_expectation_suite(context, SUITE_NAME)
        _add_expectations(suite, list(df.columns))

        # ── 2. Datasource Pandas ─────────────────────────────────────────────
        # On supprime la source si elle existe déjà (re-run idempotent)
        try:
            context.data_sources.delete(SOURCE_NAME)
        except Exception:
            pass

        datasource = context.data_sources.add_pandas(name=SOURCE_NAME)

        # ── 3. Asset + Batch Definition ──────────────────────────────────────
        asset = datasource.add_dataframe_asset(name=ASSET_NAME)
        batch_definition = asset.add_batch_definition_whole_dataframe(
            name="full_dataframe_batch"
        )

        # ── 4. Récupérer le batch (on passe le DataFrame ici) ────────────────
        batch = batch_definition.get_batch(
            batch_parameters={"dataframe": df}
        )

        # ── 5. Validation Definition ─────────────────────────────────────────
        # ValidationDefinition relie une suite à une source de données
        try:
            context.validation_definitions.delete("water_quality_validation")
        except Exception:
            pass

        validation_def = context.validation_definitions.add(
            gx.ValidationDefinition(
                name="water_quality_validation",
                data=batch_definition,
                suite=suite,
            )
        )

        # ── 6. Exécuter la validation ─────────────────────────────────────────
        results = validation_def.run(
            batch_parameters={"dataframe": df}
        )

        # ── 7. Interpréter les résultats ──────────────────────────────────────
        success    = bool(results.success)
        statistics = results.statistics if hasattr(results, 'statistics') else {}

        # Nombre d'attentes évaluées / réussies / échouées
        evaluated  = statistics.get('evaluated_expectations',  len(suite.expectations))
        successful = statistics.get('successful_expectations', 0)
        failed     = statistics.get('unsuccessful_expectations', 0)

        logger.info(f"\n  {'SUCCES' if success else 'ECHEC'} Résultat global : {'SUCCÈS' if success else 'ÉCHEC'}")
        logger.info(f"  Attentes évaluées  : {evaluated}")
        logger.info(f"  Attentes réussies  : {successful}")
        logger.info(f"  Attentes échouées  : {failed}")

        # Détailler les échecs
        failed_results = []
        for er in results.results:
            if not er.success:
                col     = er.expectation_config.kwargs.get('column', 'N/A')
                exp     = er.expectation_config.type
                partial = er.result.get('partial_unexpected_list', [])
                logger.warning(
                    f"  [{col}] {exp} | "
                    f"Exemples invalides : {partial[:5]}"
                )
                failed_results.append({
                    'column':      col,
                    'expectation': exp,
                    'details':     er.result,
                })

        return {
            'success':    success,
            'statistics': statistics,
            'results':    failed_results,
            'skipped':    False,
        }

    except Exception as e:
        logger.error(f"  Erreur lors de la validation GX : {e}")
        import traceback
        traceback.print_exc()
        # On ne bloque pas le pipeline : on retourne un résultat dégradé
        return {'success': False, 'skipped': False, 'error': str(e)}


# ============================================================================
# FONCTION 1 : CHARGER LES DONNÉES BRONZE
# ============================================================================

def load_bronze_data(filepath: str) -> pd.DataFrame:
    try:
        logger.info(f"📂 Chargement des données : {filepath}")
        df = pd.read_csv(filepath, sep=SEPARATOR, encoding=ENCODING, low_memory=False)
        logger.info(f"{len(df)} lignes chargées")
        return df
    except FileNotFoundError:
        logger.error(f"Fichier non trouvé : {filepath}")
        return None
    except Exception as e:
        logger.error(f"Erreur lors du chargement : {e}")
        return None


# ============================================================================
# FONCTION 1.5 : RECONSTRUCTION PAR JOINTURE
# ============================================================================

def reconstruct_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reconstruit les lignes complètes en jointurant les données empilées.

    Stratégie :
      1. Sépare RESULT, PLV et COM par 'type_fichier'
      2. RESULT ← PLV  (sur id_prelevement  → dates, communes, conformité)
      3. result ← COM  (sur code_reseau      → détails réseau)
    """
    logger.info("\n🔗 RECONSTRUCTION DES DONNÉES (JOINTURES)")

    if 'type_fichier' not in df.columns:
        logger.warning("  Colonne 'type_fichier' absente — jointure impossible")
        return df

    df_result = df[df['type_fichier'] == 'RESULTATS'].copy()
    df_plv    = df[df['type_fichier'] == 'CONFORMITE_PLV'].copy()
    df_com    = df[df['type_fichier'] == 'COMMUNES'].copy()

    logger.info(f"  - RESULTATS      : {len(df_result)} lignes")
    logger.info(f"  - CONFORMITE_PLV : {len(df_plv)} lignes")
    logger.info(f"  - COMMUNES       : {len(df_com)} lignes")

    if len(df_result) == 0:
        logger.warning("  Aucune ligne RESULTATS — retour du DataFrame original")
        return df

    # ── Jointure RESULT ← PLV ────────────────────────────────────────────────
    if len(df_plv) > 0 and 'id_prelevement' in df_result.columns and 'id_prelevement' in df_plv.columns:
        cols_plv = [c for c in [
            'id_prelevement', 'code_reseau', 'code_insee_commune', 'nom_commune',
            'date_prelevement', 'heure_prelevement', 'conclusion_prelevement',
            'plv_conformite_bacterio', 'plv_conformite_chimique',
            'uge_lib', 'distributeur_lib', 'moa_lib'
        ] if c in df_plv.columns]

        df_plv_dedup = df_plv[cols_plv].drop_duplicates(subset=['id_prelevement'], keep='first')
        df_merged = pd.merge(df_result, df_plv_dedup, on='id_prelevement', how='left', suffixes=('', '_plv'))

        # Réconcilier colonnes dupliquées
        for col in ['nom_commune']:
            if f'{col}_plv' in df_merged.columns:
                df_merged[col] = df_merged[f'{col}_plv']
                df_merged.drop(columns=[f'{col}_plv'], inplace=True)

        logger.info(f"  Après jointure PLV : {len(df_merged)} lignes")
    else:
        logger.warning("  Jointure PLV ignorée (données ou clé manquantes)")
        df_merged = df_result.copy()

    # ── Jointure ← COM ───────────────────────────────────────────────────────
    if len(df_com) > 0 and 'code_reseau' in df_merged.columns and 'code_reseau' in df_com.columns:
        cols_com = [c for c in ['code_reseau', 'nom_reseau', 'debut_alimentation'] if c in df_com.columns]
        df_com_dedup = df_com[cols_com].drop_duplicates(subset=['code_reseau'], keep='first')
        df_merged = pd.merge(df_merged, df_com_dedup, on='code_reseau', how='left', suffixes=('', '_com'))
        logger.info(f"  Après jointure COM : {len(df_merged)} lignes")
    else:
        logger.warning("  Jointure COM ignorée (données ou clé manquantes)")

    del df_result, df_plv, df_com
    gc.collect()

    logger.info(f"  Reconstruction terminée : {len(df_merged)} lignes")
    return df_merged


# ============================================================================
# FONCTION 2 : NETTOYAGE
# ============================================================================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("\n🧹 NETTOYAGE DES DONNÉES")
    df_clean = df.copy()

    # 1. Dates → ISO 8601
    if 'date_prelevement' in df_clean.columns:
        try:
            df_clean['date_prelevement'] = (
                pd.to_datetime(df_clean['date_prelevement'], format='mixed', errors='coerce')
                .dt.strftime('%Y-%m-%d')
            )
            logger.info("  Dates converties (ISO 8601)")
        except Exception as e:
            logger.warning(f"  Conversion dates : {e}")

    # 2. Résultat → float
    if 'resultat' in df_clean.columns:
        df_clean['resultat'] = pd.to_numeric(df_clean['resultat'], errors='coerce')
        logger.info("  Résultats convertis (float)")

    # 3. Nettoyage des chaînes
    string_cols = [
        'nom_parametre', 'nom_commune', 'nom_reseau', 'code_reseau',
        'parametre_code_siseeaux', 'unite', 'conclusion_prelevement'
    ]
    for col in string_cols:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()

    logger.info("  Chaînes nettoyées (strip)")

    # 3b. Correction mojibake iso-8859-1 mal relu comme UTF-8
    #     Symptôme : "CONDUCTIVITÃ Ã 25Â°C" au lieu de "CONDUCTIVITÉ À 25°C"
    #     Cause    : fichier réellement UTF-8 mais lu en iso-8859-1 dans Bronze,
    #               puis resauvegardé tel quel — on répare ici.
    text_cols_to_fix = [c for c in ['nom_parametre', 'nom_commune', 'nom_reseau',
                                     'distributeur_lib', 'uge_lib', 'moa_lib']
                        if c in df_clean.columns]
    def _fix_mojibake(series: pd.Series) -> pd.Series:
        """Tente de réparer les chaînes mal encodées (latin-1 → UTF-8)."""
        def _fix(val):
            if not isinstance(val, str):
                return val
            try:
                return val.encode('iso-8859-1').decode('utf-8')
            except (UnicodeDecodeError, UnicodeEncodeError):
                return val  # déjà propre ou irréparable
        return series.map(_fix)

    fixed_count = 0
    for col in text_cols_to_fix:
        fixed = _fix_mojibake(df_clean[col])
        changed = (fixed != df_clean[col]).sum()
        if changed > 0:
            df_clean[col] = fixed
            fixed_count += changed
    if fixed_count:
        logger.info(f"  Encodage corrigé : {fixed_count} valeurs réparées (mojibake)")
    else:
        logger.info("  Encodage OK (aucun mojibake détecté)")

    # 4. Info sur les paramètres disponibles
    if 'nom_parametre' in df_clean.columns:
        n = df_clean['nom_parametre'].nunique()
        examples = ', '.join(df_clean['nom_parametre'].dropna().unique()[:5])
        logger.info(f"  ℹ️ {n} paramètres uniques — ex : {examples}")

    logger.info("Nettoyage terminé")
    return df_clean


# ============================================================================
# FONCTION 3 : DÉDUPLIQUAGE
# ============================================================================

def deduplicate_data(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("\n🔄 DÉDUPLIQUAGE")
    initial = len(df)

    if 'id_prelevement' in df.columns and 'code_parametre' in df.columns:
        key = ['id_prelevement', 'code_parametre']
    elif 'id_prelevement' in df.columns and 'nom_parametre' in df.columns:
        key = ['id_prelevement', 'nom_parametre']
    else:
        key = [c for c in ['station_id', 'date_prelevement', 'parametre'] if c in df.columns]

    if not key:
        logger.warning("  Aucune clé de déduplication — étape ignorée")
        return df

    logger.info(f"  Clé : {key}")
    dupes = df[key].duplicated().sum()
    logger.info(f"  Doublons détectés : {dupes}")
    df_out = df.drop_duplicates(subset=key, keep='first').reset_index(drop=True)
    logger.info(f"  Lignes supprimées : {initial - len(df_out)} | Restantes : {len(df_out)}")
    return df_out


# ============================================================================
# FONCTION 4 : VALIDATION PERSONNALISÉE (filet de sécurité)
# ============================================================================

def validate_custom(df: pd.DataFrame) -> list:
    """
    Validations métier légères, indépendantes de GX.
    Sert de filet de sécurité si GX n'est pas disponible.
    """
    logger.info("\nVALIDATION PERSONNALISÉE (fallback / complémentaire)")
    issues = []

    # Nulls sur clés métier (jamais acceptables)
    for col in ['id_prelevement', 'nom_parametre']:
        if col in df.columns:
            nulls = int(df[col].isnull().sum())
            if nulls > 0:
                pct = nulls / len(df) * 100
                logger.warning(f"  {col} : {nulls} NULL ({pct:.2f}%) — BLOQUANT")
                issues.append({'column': col, 'type': 'null_key', 'count': nulls, 'blocking': True})

    # Nulls sur résultat : normaux pour paramètres qualitatifs (ASPECT, ODEUR…)
    # On distingue les lignes sans résultat numérique des lignes sans aucune valeur
    if 'resultat' in df.columns:
        nulls_res = int(df['resultat'].isnull().sum())
        if nulls_res > 0:
            pct = nulls_res / len(df) * 100
            # Qualifier selon le taux
            if pct > 5:
                logger.warning(f"  resultat : {nulls_res} NULL ({pct:.2f}%) — taux élevé, vérifier")
                issues.append({'column': 'resultat', 'type': 'null_high', 'count': nulls_res, 'blocking': False})
            else:
                logger.info(f"  ℹ️ resultat : {nulls_res} NULL ({pct:.2f}%) — attendu (params qualitatifs)")

    # Coordonnées géo hors France
    if 'latitude' in df.columns and 'longitude' in df.columns:
        bad = df[
            df['latitude'].between(*GEO_BOUNDS['latitude']) &
            df['longitude'].between(*GEO_BOUNDS['longitude'])
            == False
        ]
        if len(bad):
            logger.warning(f"  {len(bad)} coordonnées hors limites France")
            issues.append({'type': 'invalid_geo', 'count': len(bad)})

    # Plages par paramètre
    if 'nom_parametre' in df.columns and 'resultat' in df.columns:
        for param, (lo, hi) in PARAMETER_RANGES.items():
            mask = (
                df['nom_parametre'].str.lower().str.contains(param.lower(), na=False) &
                ~df['resultat'].between(lo, hi)
            )
            n = mask.sum()
            if n:
                logger.warning(f"  {param} : {n} valeurs hors [{lo}, {hi}]")
                issues.append({'parametre': param, 'type': 'out_of_range', 'count': n})

    if not issues:
        logger.info("  Aucun problème détecté")
    return issues


# ============================================================================
# FONCTION 5 : ENRICHISSEMENT
# ============================================================================

def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("\n✨ ENRICHISSEMENT DES DONNÉES")
    df_e = df.copy()

    # ID unique par enregistrement
    if 'id_prelevement' in df_e.columns and 'code_parametre' in df_e.columns:
        import hashlib
        key_col = df_e['id_prelevement'].astype(str) + '_' + df_e['code_parametre'].astype(str)
        df_e['record_id'] = key_col.apply(lambda x: hashlib.md5(x.encode()).hexdigest()[:8])
    else:
        df_e['record_id'] = range(len(df_e))
    logger.info("  record_id généré")

    # quality_flag (vectorisé)
    df_e['quality_flag'] = 'OK'
    df_e.loc[df_e['resultat'].isnull(), 'quality_flag'] = 'UNKNOWN'
    if 'nom_parametre' in df_e.columns:
        mask_ecoli   = df_e['nom_parametre'].str.contains(r'ECOLI|E\.?\s*COLI', case=False, na=False) & (df_e['resultat'] > 0)
        mask_nitrate = df_e['nom_parametre'].str.contains(r'NITRATE|NO3', case=False, na=False) & (df_e['resultat'] > 50)
        df_e.loc[mask_ecoli,   'quality_flag'] = 'ALERT'
        df_e.loc[mask_nitrate, 'quality_flag'] = 'WARNING'
    logger.info("  quality_flag calculé")

    df_e['processed_date'] = datetime.now().isoformat()
    return df_e


# ============================================================================
# FONCTION 6 : SAUVEGARDE
# ============================================================================

def save_silver_data(df: pd.DataFrame, filename: str = "silver_clean.csv") -> bool:
    try:
        filepath = os.path.join(SILVER_PATH, filename)
        df.to_csv(filepath, sep=SEPARATOR, encoding='utf-8', index=False)
        size_kb = os.path.getsize(filepath) / 1024
        logger.info(f"💾 Silver sauvegardé : {filepath} ({size_kb:.2f} KB)")
        return True
    except Exception as e:
        logger.error(f"Erreur sauvegarde : {e}")
        return False


# ============================================================================
# PIPELINE PRINCIPALE
# ============================================================================

def main():
    logger.info("\n" + "=" * 80)
    logger.info("🔄 PIPELINE SILVER — TRANSFORMATION + VALIDATION GX")
    logger.info(f"Timestamp : {datetime.now().isoformat()}")
    logger.info("=" * 80)

    # 1. Charger Bronze
    df = load_bronze_data(BRONZE_PATH)
    if df is None:
        logger.error("Chargement Bronze impossible — pipeline arrêté")
        return
    logger.info(f"\nBronze : {len(df)} lignes × {len(df.columns)} colonnes")

    # 1.5. Reconstruire via jointures
    df = reconstruct_data(df)
    logger.info(f"Après reconstruction : {len(df)} lignes × {len(df.columns)} colonnes")

    # 2. Nettoyer
    df = clean_data(df)

    # 3. Dédupliquer
    df = deduplicate_data(df)

    # 4. Enrichir (avant validation, pour que quality_flag soit validé)
    df = enrich_data(df)

    # 5. Validation Great Expectations (API v0.18+)
    gx_result = validate_with_great_expectations(df)

    # 5b. Validation personnalisée (complémentaire / fallback)
    custom_issues = validate_custom(df)

    # 6. Sauvegarder
    success = save_silver_data(df)

    # ── Résumé final ──────────────────────────────────────────────────────────
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("RÉSUMÉ FINAL")
        logger.info("=" * 80)
        logger.info(f"  Lignes      : {len(df)}")
        logger.info(f"  Colonnes    : {len(df.columns)}")

        if 'nom_parametre' in df.columns:
            logger.info(f"  Paramètres  : {df['nom_parametre'].nunique()} uniques")
        if 'id_prelevement' in df.columns:
            logger.info(f"  Prélèvements: {df['id_prelevement'].nunique()} uniques")

        # Dates
        col_date = next((c for c in ['date_prelevement', 'date_prelevement_y', 'date_prelevement_x']
                         if c in df.columns), None)
        if col_date:
            dates = pd.to_datetime(df[col_date], errors='coerce')
            logger.info(f"  Période     : {dates.min().date()} → {dates.max().date()}")

        # GX
        if gx_result.get('skipped'):
            logger.info("  GX          : ignoré (non disponible)")
        else:
            gx_ok = 'SUCCES' if gx_result.get('success') else 'ECHEC'
            stats = gx_result.get('statistics', {})
            logger.info(f"  GX          : {gx_ok} | "
                        f"{stats.get('successful_expectations', '?')} / "
                        f"{stats.get('evaluated_expectations', '?')} attentes OK")

        logger.info(f"  Problèmes custom : {len(custom_issues)}")
        logger.info("=" * 80)
        logger.info("PIPELINE SILVER TERMINÉ\n")
    else:
        logger.error("Sauvegarde échouée — vérifier les droits d'écriture")


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