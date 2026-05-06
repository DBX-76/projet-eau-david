# ============================================================================
# NOTEBOOK 1 : INGESTION DE DONNÉES BRUTES - COUCHE BRONZE
# ============================================================================
# Description : Ce notebook gère l'ingestion des données brutes depuis la plateforme
#               data.gouv.fr et leur stockage dans la couche Bronze du pipeline de données.
#
# Objectif : Télécharger les fichiers de données, effectuer une validation basique,
#            fusionner les données provenant de différentes sources, et les sauvegarder
#            dans un format brut pour les étapes de transformation ultérieures.
# ============================================================================

import requests
import pandas as pd
import os
import io
import zipfile
from datetime import datetime
import logging

# ============================================================================
# CONFIGURATION
# ============================================================================

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 2025 : Fichier ZIP 276 Mo - Résultats contrôle sanitaire eau
DATA_SOURCES = {
    "qualite_eau_2025": "https://www.data.gouv.fr/fr/datasets/r/7e38c236-dd3c-455e-a728-f0ecb84b1a7c"
   
}

# Dossier de sortie 
BRONZE_PATH = "./data/bronze"
os.makedirs(BRONZE_PATH, exist_ok=True)

# Paramètres de téléchargement
TIMEOUT = 300  # Délai d'attente maximal pour les requêtes HTTP (en secondes, soit 5 minutes)
ENCODING = 'iso-8859-1'  # Encodage des fichiers texte (ISO-8859-1 pour supporter les caractères accentués français)
SEPARATOR_CSV = ','  # Séparateur de colonnes standard dans les fichiers CSV
SEPARATOR_FR = ';'  # Séparateur français pour l'export des données (point-virgule au lieu de virgule)

# ============================================================================
# FONCTION PRINCIPALE : INGESTION
# ============================================================================

def extract_csv_from_zip(zip_bytes: bytes, source_name: str) -> pd.DataFrame:
    """
    Extrait et charge TOUS les fichiers CSV/TXT depuis un ZIP en mémoire.

    Args:
        zip_bytes (bytes) : Contenu du fichier ZIP
        source_name (str) : Nom de la source (pour logging)

    Returns:
        pd.DataFrame : DataFrame avec les données fusionnées de tous les fichiers, ou None en cas d'erreur
    """
    try:
        # Créer un objet BytesIO depuis les bytes
        zip_buffer = io.BytesIO(zip_bytes)

        # Ouvrir le fichier ZIP
        with zipfile.ZipFile(zip_buffer, 'r') as zip_ref:
            logger.info(f"Fichiers trouvés dans le ZIP :")
            file_list = zip_ref.namelist()
            for fname in file_list:
                logger.info(f"    - {fname}")

            # Chercher TOUS les fichiers CSV, TXT (CSV renommé) ou Excel
            csv_files = [f for f in file_list if f.lower().endswith('.csv')]
            txt_files = [f for f in file_list if f.lower().endswith('.txt')]
            excel_files = [f for f in file_list if f.lower().endswith(('.xlsx', '.xls'))]

            # Collecter tous les fichiers à traiter
            files_to_process = csv_files + txt_files + excel_files

            if not files_to_process:
                logger.error(f"ERROR :  Aucun fichier CSV/TXT/Excel trouvé dans le ZIP")
                return None

            logger.info(f"Traitement de {len(files_to_process)} fichier(s) trouvé(s)")

            # Traiter chaque fichier et collecter les DataFrames
            all_dfs = []

            for target_file in files_to_process:
                logger.info(f"\nTraitement du fichier : {target_file}")

                # Déterminer le type de fichier
                if target_file.lower().endswith('.csv'):
                    file_type = 'csv'
                elif target_file.lower().endswith('.txt'):
                    file_type = 'txt'
                else:
                    file_type = 'excel'

                # Lire le fichier selon son type
                if file_type in ['csv', 'txt']:
                    separator = SEPARATOR_CSV
                    content = zip_ref.read(target_file).decode(ENCODING)
                    df = pd.read_csv(io.StringIO(content), sep=separator)
                else:  # Excel
                    df = pd.read_excel(io.BytesIO(zip_ref.read(target_file)))

                logger.info(f"  INFO :  Chargé : {len(df)} lignes, {len(df.columns)} colonnes")

                # ============================================================================
                # RENOMMAGE DES COLONNES : Mapping selon le type de fichier
                # ============================================================================

                # Mapping spécifique selon le fichier (RESULT, PLV, ou COM)
                if 'RESULT' in target_file.upper():
                    # DIS_RESULT_2025.txt - Résultats d'analyse
                    column_mapping = {
                        'cddept': 'code_departement',
                        'referenceprel': 'id_prelevement',
                        'cdparametresiseeaux': 'parametre_code_siseeaux',
                        'cdparametre': 'code_parametre',
                        'libmajparametre': 'nom_parametre',
                        'libminparametre': 'nom_parametre_court',
                        'libwebparametre': 'nom_parametre_web',
                        'qualitparam': 'qualite_parametre',
                        'insituana': 'analyse_in_situ',
                        'rqana': 'qualite_resultat_analyse',
                        'cdunitereferencesiseeaux': 'unite_code_siseeaux',
                        'cdunitereference': 'unite',
                        'limitequal': 'limite_qualite',
                        'refqual': 'reference_qualite',
                        'valtraduite': 'resultat',
                        'casparam': 'cas_parametre',
                        'referenceanl': 'reference_analyse',
                    }
                    df['type_fichier'] = 'RESULTATS'

                elif 'PLV' in target_file.upper():
                    # DIS_PLV_2025.txt - Conformité PLV
                    column_mapping = {
                        'cddept': 'code_departement',
                        'cdreseau': 'code_reseau',
                        'inseecommuneprinc': 'code_insee_commune',
                        'nomcommuneprinc': 'nom_commune',
                        'cdreseauamont': 'code_reseau_amont',
                        'nomreseauamont': 'nom_reseau_amont',
                        'pourcentdebit': 'pourcentage_debit',
                        'referenceprel': 'id_prelevement',
                        'dateprel': 'date_prelevement',
                        'heureprel': 'heure_prelevement',
                        'conclusionprel': 'conclusion_prelevement',
                        'ugelib': 'uge_lib',
                        'distrlib': 'distributeur_lib',
                        'moalib': 'moa_lib',
                        'plvconformitebacterio': 'plv_conformite_bacterio',
                        'plvconformitechimique': 'plv_conformite_chimique',
                        'plvconformitereferencebact': 'plv_conformite_ref_bact',
                        'plvconformitereferencechim': 'plv_conformite_ref_chim',
                    }
                    df['type_fichier'] = 'CONFORMITE_PLV'

                elif 'COM' in target_file.upper():
                    # DIS_COM_UDI_2025.txt - Communes
                    column_mapping = {
                        'inseecommune': 'code_insee_commune',
                        'nomcommune': 'nom_commune',
                        'quartier': 'quartier',
                        'cdreseau': 'code_reseau',
                        'nomreseau': 'nom_reseau',
                        'debutalim': 'debut_alimentation',
                    }
                    df['type_fichier'] = 'COMMUNES'

                else:
                    # Fichier inconnu - mapping générique
                    column_mapping = {}
                    df['type_fichier'] = 'INCONNU'

                # Appliquer le renommage (seulement les colonnes qui existent)
                columns_to_rename = {old: new for old, new in column_mapping.items() if old in df.columns}

                if columns_to_rename:
                    df = df.rename(columns=columns_to_rename)
                    logger.info(f" {len(columns_to_rename)} colonnes renommées")
                else:
                    logger.warning(f"  WARN : Aucune colonne standardisée trouvée pour {target_file}")

                # Ajouter le nom du fichier source pour traçabilité
                df['fichier_source'] = target_file

                # Collecter ce DataFrame
                all_dfs.append(df)

            # ============================================================================
            # FUSION DE TOUS LES FICHIERS
            # ============================================================================

            if not all_dfs:
                logger.error("ERROR :  Aucun DataFrame valide extrait")
                return None

            if len(all_dfs) == 1:
                # Un seul fichier
                final_df = all_dfs[0]
                logger.info(f"INFO :  1 fichier traité : {len(final_df)} lignes totales")
            else:
                # Plusieurs fichiers - fusion intelligente
                logger.info(f"🔗 Fusion de {len(all_dfs)} fichiers...")

                # Identifier les clés de jointure potentielles
                common_columns = set.intersection(*[set(df.columns) for df in all_dfs])
                logger.info(f"  Colonnes communes : {sorted(common_columns)}")

                # Essayer de fusionner sur les clés les plus pertinentes
                merge_keys = []

                # Priorité aux clés de jointure
                if 'id_prelevement' in common_columns:
                    merge_keys.append('id_prelevement')
                if 'code_insee_commune' in common_columns:
                    merge_keys.append('code_insee_commune')
                if 'code_reseau' in common_columns:
                    merge_keys.append('code_reseau')
                if 'code_departement' in common_columns:
                    merge_keys.append('code_departement')

                if merge_keys:
                    logger.info(f"  Clés de fusion : {merge_keys}")

                    # Fusion en chaîne (left join successif)
                    final_df = all_dfs[0]
                    for i, df in enumerate(all_dfs[1:], 1):
                        logger.info(f"  Fusion {i}: {len(final_df)} lignes + {len(df)} lignes")
                        final_df = pd.merge(final_df, df, on=merge_keys, how='outer', suffixes=('', f'_{i}'))
                        logger.info(f"    Résultat : {len(final_df)} lignes")
                else:
                    # Pas de clés communes - concaténation simple
                    logger.warning("  WARN : Pas de clés de fusion communes - concaténation simple")
                    final_df = pd.concat(all_dfs, ignore_index=True, sort=False)

                logger.info(f"INFO :  Fusion terminée : {len(final_df)} lignes, {len(final_df.columns)} colonnes")

            return final_df
            
    except zipfile.BadZipFile:
        logger.error(f"ERROR :  Fichier ZIP invalide ou corrompu")
        return None
    except Exception as e:
        logger.error(f"ERROR :  Erreur lors de l'extraction du ZIP : {e}")
        return None


def download_data(source_name: str, url: str) -> pd.DataFrame:
    """
    Télécharge un fichier CSV ou ZIP depuis une URL.
    Gère les redirections et détecte automatiquement le format.
    
    Args:
        source_name (str) : Nom de la source (pour logging)
        url (str) : URL du fichier à télécharger
    
    Returns:
        pd.DataFrame : DataFrame pandas avec les données, ou None en cas d'erreur
    
    Raises:
        requests.RequestException : Erreur réseau
        pd.errors.ParserError : Erreur de parsing CSV
    """
    try:
        logger.info(f"Début du téléchargement : {source_name}")
        logger.info(f"   URL : {url[:80]}...")
        
        # Télécharger le fichier avec timeout et allow_redirects
        response = requests.get(url, timeout=TIMEOUT, allow_redirects=True, stream=False)
        response.raise_for_status()  # Lever une exception si statut HTTP erreur
        
        file_size_mb = len(response.content) / 1024 / 1024
        logger.info(f"INFO :  Fichier téléchargé ({file_size_mb:.2f} MB)")
        
        # Détecter le type de contenu
        content_type = response.headers.get('content-type', '').lower()
        logger.info(f"   Type de contenu : {content_type}")
        
        # Vérifier si c'est un ZIP
        is_zip = (
            content_type.startswith('application/zip') or 
            content_type.startswith('application/x-zip') or
            url.lower().endswith('.zip') or
            response.content[:2] == b'PK'  # Signature ZIP
        )
        
        if is_zip:
            logger.info(" Format détecté : ZIP")
            df = extract_csv_from_zip(response.content, source_name)
            if df is None:
                return None
        else:
            logger.info(" Format détecté : CSV")
            # Parser le CSV en DataFrame
            df = pd.read_csv(
                io.StringIO(response.text),
                sep=SEPARATOR,
                encoding=ENCODING,
                dtype_backend='numpy_nullable'  # Meilleure gestion des types
            )
        
        logger.info(f"INFO :  Parsing réussi : {len(df)} lignes, {len(df.columns)} colonnes")
        
        return df
        
    except requests.exceptions.Timeout:
        logger.error(f"Timeout lors du téléchargement ({TIMEOUT}s dépassé)")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau : {e}")
        return None
    except pd.errors.ParserError as e:
        logger.error(f"Erreur de parsing CSV : {e}")
        return None
    except Exception as e:
        logger.error(f"ERROR :  Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        return None


def save_to_csv(df: pd.DataFrame, filename: str) -> bool:
    """
    Sauvegarde un DataFrame en fichier CSV dans le dossier Bronze.
    
    Args:
        df (pd.DataFrame) : DataFrame à sauvegarder
        filename (str) : Nom du fichier (sans extension)
    
    Returns:
        bool : True si succès, False sinon
    """
    try:
        filepath = os.path.join(BRONZE_PATH, f"{filename}.csv")
        
        df.to_csv(
            filepath,
            sep=SEPARATOR_FR,  # Sauvegarde toujours en format français (;)
            encoding=ENCODING,
            index=False
        )
        
        logger.info(f"Fichier sauvegardé : {filepath} ({os.path.getsize(filepath) / 1024:.2f} KB)")
        return True
        
    except Exception as e:
        logger.error(f"ERROR :  Erreur lors de la sauvegarde : {e}")
        return False


def display_data_preview(df: pd.DataFrame) -> None:
    """
    Affiche un aperçu des données.
    
    Args:
        df (pd.DataFrame) : DataFrame à prévisualiser
    """
    logger.info("\n" + "=" * 80)
    logger.info(" APERÇU DES DONNÉES")
    logger.info("=" * 80)
    
    # Informations générales
    logger.info(f"\nDimensions : {df.shape[0]} lignes × {df.shape[1]} colonnes")
    
    # Colonnes et types
    logger.info("\nColonnes et types :")
    for col, dtype in df.dtypes.items():
        logger.info(f"  - {col}: {dtype}")
    
    # Premières lignes
    logger.info("\nPremières 5 lignes :")
    logger.info(df.head().to_string())
    
    # Statistiques de nullité
    logger.info("\nValeurs manquantes :")
    nulls = df.isnull().sum()
    for col, count in nulls[nulls > 0].items():
        pct = (count / len(df)) * 100
        logger.info(f"  - {col}: {count} ({pct:.2f}%)")
    
    logger.info("\n" + "=" * 80 + "\n")


def validate_raw_data(df: pd.DataFrame) -> dict:
    """
    Valide les données brutes à un niveau très basique.
    
    Args:
        df (pd.DataFrame) : DataFrame à valider
    
    Returns:
        dict : Dictionnaire avec les résultats de validation
    """
    validation_results = {
        "not_empty": len(df) > 0,
        "required_columns": [],
        "data_types_ok": True,
        "errors": []
    }
    
    # Vérifier que le DataFrame n'est pas vide
    if not validation_results["not_empty"]:
        validation_results["errors"].append("ERROR :  DataFrame vide")
        return validation_results
    
    # Vérifier la présence des colonnes essentielles
    required_columns = [
        'station_id', 'latitude', 'longitude', 'date_prelevement',
        'parametre', 'resultat', 'unite', 'laboratoire'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation_results["errors"].append(f"ERROR :  Colonnes manquantes : {missing_columns}")
    else:
        validation_results["required_columns"] = required_columns
    
    logger.info("\n📋 Résultats de validation :")
    for key, value in validation_results.items():
        if key != "errors":
            status = "INFO : " if value else "ERROR : "
            logger.info(f"{status} {key}: {value}")
    
    if validation_results["errors"]:
        for error in validation_results["errors"]:
            logger.warning(f"{error}")
    
    return validation_results


# ============================================================================
# PIPELINE PRINCIPALE
# ============================================================================

def main():
    """
    Fonction principale qui orchestre l'ensemble du processus d'ingestion des données brutes.

    Cette fonction coordonne les étapes suivantes :
    - Téléchargement des données depuis les sources externes
    - Validation basique des données téléchargées
    - Fusion des données provenant de différentes sources
    - Sauvegarde des données dans la couche Bronze
    """
    logger.info("\n" + "=" * 80)
    logger.info("DÉMARRAGE DU PIPELINE D'INGESTION (BRONZE)")
    logger.info(f"Timestamp : {datetime.now().isoformat()}")
    logger.info("=" * 80 + "\n")
    
    all_data = []  # Liste pour accumuler les DataFrames de chaque source traitée avec succès

    # Itération sur chaque source de données à traiter
    for source_name, url in DATA_SOURCES.items():
        logger.info(f"\nTraitement de la source : {source_name}")
        logger.info(f"URL : {url}")

        # Étape 1 : Téléchargement des données depuis la source externe
        df = download_data(source_name, url)

        if df is None:
            logger.warning(f"Source {source_name} ignorée en raison d'une erreur lors du téléchargement")
            continue

        # Étape 2 : Validation basique des données téléchargées
        validation = validate_raw_data(df)

        if not validation["not_empty"]:
            logger.warning(f"Source {source_name} ignorée car les données sont vides")
            continue

        # Étape 3 : Affichage d'un aperçu des données pour vérification
        display_data_preview(df)

        # Étape 4 : Ajout de métadonnées pour la traçabilité des données
        df['source_donnee'] = source_name
        df['ingestion_date'] = datetime.now().isoformat()

        # Étape 5 : Sauvegarde individuelle des données de cette source
        success = save_to_csv(df, f"bronze_{source_name}")

        if success:
            all_data.append(df)
        else:
            logger.warning(f"Erreur lors de la sauvegarde des données de {source_name}")

    # Étape 6 : Fusion de toutes les sources traitées avec succès
    if all_data:
        logger.info(f"\nFusion de {len(all_data)} source(s) de données...")
        df_combined = pd.concat(all_data, ignore_index=True)
        logger.info(f"Données fusionnées : {len(df_combined)} lignes au total")

        # Étape 7 : Sauvegarde du fichier combiné regroupant toutes les sources
        save_to_csv(df_combined, "bronze_combined")

        # Étape 8 : Génération du résumé final de l'ingestion
        logger.info("\n" + "=" * 80)
        logger.info("RÉSUMÉ DE L'INGESTION")
        logger.info("=" * 80)
        logger.info(f"Total lignes : {len(df_combined)}")
        logger.info(f"Total colonnes : {len(df_combined.columns)}")
        logger.info(f"Colonnes disponibles : {list(df_combined.columns)}")

        # Vérifier les colonnes temporelles disponibles
        if 'date_prelevement' in df_combined.columns:
            logger.info(f"Dates couvertes : de {df_combined['date_prelevement'].min()} à {df_combined['date_prelevement'].max()}")
        else:
            logger.warning("WARN : Colonne 'date_prelevement' non trouvée dans ce fichier")
            logger.info("   Ce fichier contient probablement uniquement les résultats d'analyse")
            logger.info("   Les dates de prélèvement sont dans un autre fichier (PLV ou COM)")

        # Vérifier les colonnes de localisation
        if 'code_departement' in df_combined.columns:
            logger.info(f"Départements couverts : {df_combined['code_departement'].nunique()} départements")
        else:
            logger.warning("WARN : Colonne 'code_departement' non trouvée")

        # Vérifier les colonnes de source
        if 'source_donnee' in df_combined.columns:
            logger.info(f"Sources de données : {df_combined['source_donnee'].unique().tolist()}")
        else:
            logger.warning("WARN : Colonne 'source_donnee' non trouvée")

        # Vérifier les paramètres
        if 'nom_parametre' in df_combined.columns:
            logger.info(f"Paramètres mesurés : {df_combined['nom_parametre'].nunique()} paramètres différents")
        else:
            logger.warning("WARN : Colonne 'nom_parametre' non trouvée")

        logger.info("=" * 80)
        logger.info("\nINFO :  INGESTION TERMINÉE AVEC SUCCÈS")
        logger.info(f"Fichier prêt pour la transformation (Silver) : {BRONZE_PATH}/bronze_combined.csv\n")
        
    else:
        logger.error("ERROR :  Aucune donnée n'a pu être téléchargée. Vérifiez les URLs.")


# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == "__main__":
    import io  # Import ici pour éviter les erreurs
    
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\nWARN : Pipeline arrêté par l'utilisateur (Ctrl+C)")
    except Exception as e:
        logger.critical(f"ERROR :  Erreur critique : {e}")
        import traceback
        traceback.print_exc()
