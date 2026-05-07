# Guide Personnel — Concepts et Technologies du Projet Qualité d'Eau

> Document de révision personnel. Tous les concepts abordés dans le projet, expliqués avec des analogies et des exemples concrets.

---

## Table des matières

1. [L'architecture Médaillon (Bronze / Silver / Gold)](#1-larchitecture-médaillon)
2. [Delta Tables et Delta Lake](#2-delta-tables-et-delta-lake)
3. [Databricks et l'écosystème Spark](#3-databricks-et-lécosystème-spark)
4. [Great Expectations — La validation qualité](#4-great-expectations--la-validation-qualité)
5. [FastAPI — Exposer les données via une API REST](#5-fastapi--exposer-les-données-via-une-api-rest)
6. [L'orchestration — Faire tourner les pièces dans le bon ordre](#6-lorchestrtion--faire-tourner-les-pièces-dans-le-bon-ordre)
7. [Azure Databricks — Ce qui aurait été fait en cloud](#7-azure-databricks--ce-qui-aurait-été-fait-en-cloud)
8. [Le Data Load Tool (DLT)](#8-le-data-load-tool-dlt)
9. [Pandas vs PySpark — Deux moteurs, deux contextes](#9-pandas-vs-pyspark--deux-moteurs-deux-contextes)
10. [Unity Catalog et la gouvernance des données](#10-unity-catalog-et-la-gouvernance-des-données)
11. [Swagger UI — La documentation vivante d'une API](#11-swagger-ui--la-documentation-vivante-dune-api)
12. [GitHub Actions — L'intégration et le déploiement continus (CI/CD)](#12-github-actions--lintégration-et-le-déploiement-continus-cicd)
13. [La vue d'ensemble — Comment tout s'assemble](#13-la-vue-densemble--comment-tout-sassemble)

---

## 1. L'architecture Médaillon

### C'est quoi ?

L'architecture médaillon est une façon d'organiser la transformation des données en **trois couches successives**, chacune plus propre et plus utile que la précédente.

Les trois couches s'appellent **Bronze**, **Silver** et **Gold**.

### L'analogie du minerai

Imagine une mine d'or.

```
[La montagne]         →    Tu extrais la roche brute
      ↓
[Bronze — la roche]   →    Tout ce qui sort de la mine, sans tri
      ↓
[Silver — le minerai] →    On a retiré les impuretés, c'est propre
      ↓
[Gold — l'or pur]     →    Ce qu'on présente, ce qui a de la valeur métier
```

### Ce que ça donne concrètement dans ce projet

**Couche Bronze**

- Source : data.gouv.fr (fichiers CSV bruts)
- Ce qu'on fait : téléchargement + fusion des fichiers, aucune transformation
- Ce qu'on garde : **tout**, même les lignes douteuses, les doublons, les valeurs manquantes
- Pourquoi : si on se plante plus tard, on peut toujours revenir à la source sans retélécharger
- Résultat : `bronze_combined.csv` — 13 millions de lignes, brut de fonderie

**Couche Silver**

- Source : Bronze
- Ce qu'on fait : nettoyage, dédoublonnage, validation des types, enrichissement
- Ce qu'on supprime : lignes incomplètes, doublons, valeurs hors plage
- Résultat : `silver_clean.csv` — 12,5 millions de lignes, fiables et cohérentes

**Couche Gold**

- Source : Silver
- Ce qu'on fait : agrégations métier (moyennes par département, top 10 communes, etc.)
- Ce qu'on produit : des **indicateurs prêts à consommer** par un analyste ou une API
- Résultat : 5 fichiers CSV légers, directement utilisables pour des graphiques ou des rapports

### Pourquoi trois couches et pas une seule ?

Parce que chaque transformation est **irréversible** si on ne garde pas l'étape précédente.

Si tu supprimes une ligne en Silver et que tu te rends compte plus tard que c'était une erreur, tu peux revenir au Bronze et recommencer. Sans Bronze, cette donnée est perdue pour toujours.

> **Règle d'or** : on ne supprime jamais les données en Bronze. On ajoute, on enrichit, mais on ne détruit pas.

---

## 2. Delta Tables et Delta Lake

### C'est quoi un format de fichier ?

Avant de comprendre Delta, il faut comprendre pourquoi le format d'un fichier compte.

Un CSV, c'est pratique mais limité :
- Pas de types de données garantis (une date peut être stockée comme du texte)
- Pas d'historique des modifications
- Impossible de faire une transaction (modifier plusieurs lignes d'un coup de façon fiable)
- Lent à lire quand le fichier est énorme

**Delta Lake** résout tous ces problèmes.

### L'analogie du carnet de caisse

Imagine un commerçant qui tient sa caisse.

Un CSV, c'est une feuille où il écrit les montants. S'il se trompe, il rature. On ne sait pas ce qu'il y avait avant.

Une **Delta Table**, c'est un livre de caisse avec :
- Chaque opération horodatée
- La possibilité de consulter le solde à n'importe quel moment passé (**time travel**)
- Une validation que les montants sont bien des nombres et pas du texte
- Un journal des transactions pour garantir qu'une opération incomplète ne corrompt pas le livre

### Techniquement, comment ça marche ?

Une Delta Table, c'est en réalité deux choses :

```
dossier_ma_table/
├── _delta_log/          ← Le journal (liste de toutes les opérations)
│   ├── 000.json         ← "J'ai créé la table avec ces colonnes"
│   ├── 001.json         ← "J'ai ajouté 10 000 lignes"
│   └── 002.json         ← "J'ai modifié les lignes où dept=75"
└── part-00001.parquet   ← Les données réelles, en format Parquet
```

Le format **Parquet** (utilisé sous le capot) est un format **colonnaire** : au lieu de stocker ligne par ligne, il stocke colonne par colonne. Pour une requête qui ne touche que 3 colonnes sur 50, c'est drastiquement plus rapide.

### Ce que ça apporte dans ce projet

Dans Databricks, les fichiers Gold CSV sont chargés en Delta Tables managées. Ça permet à Databricks de :
- Interroger les données avec du SQL natif (`spark.table("gold_kpis")`)
- Garantir le schéma (une colonne déclarée `float` ne peut pas recevoir du texte)
- Mettre à jour les tables sans tout réécrire

---

## 3. Databricks et l'écosystème Spark

### C'est quoi Apache Spark ?

Spark, c'est un moteur de calcul distribué. Distribué veut dire qu'il répartit le travail sur plusieurs machines (ou plusieurs cœurs) en parallèle.

### L'analogie du chantier

Imagine que tu dois peindre 1 000 maisons.

- **Pandas** = un seul peintre très efficace. Parfait pour 10 maisons, mais pour 1 000, ça prend du temps.
- **Spark** = une entreprise de 50 peintres. Chaque peintre prend 20 maisons. Le chantier finit bien plus vite.

La différence fondamentale : Spark ne charge **pas tout en mémoire d'un coup**. Il découpe les données en **partitions** et les traite en parallèle sur un **cluster** (un ensemble de machines).

### C'est quoi Databricks alors ?

Databricks, c'est la **plateforme** qui encapsule Spark pour le rendre utilisable facilement.

Sans Databricks, utiliser Spark c'est complexe : il faut configurer le cluster, gérer les dépendances, écrire beaucoup de code infrastructure.

Databricks fournit :
- Des **notebooks** interactifs (comme Jupyter, mais connectés à un cluster Spark)
- La gestion automatique des clusters (démarrage, arrêt, redimensionnement)
- L'intégration native avec les services cloud (Azure, AWS, GCP)
- Unity Catalog pour la gouvernance des données

### PySpark : Spark depuis Python

PySpark, c'est l'API Python de Spark. On écrit du Python, mais l'exécution se fait sur le cluster distribué.

```python
# Exemple simple : lire un CSV et compter les lignes par département
df = spark.read.csv("/Volumes/eau/gold/gold_departements.csv", header=True)
df.groupBy("code_departement").count().show()
```

Ce code peut tourner sur 13 millions de lignes réparties sur 10 machines sans que tu aies à gérer la distribution toi-même.

### La Community Edition vs la version Pro

La Community Edition de Databricks est gratuite mais limitée :
- Un seul cluster, pas de clustering avancé
- Pas de Workflows avec DAG visuel
- Pas de SQL Endpoint (impossible d'exposer une table comme une API SQL directe)
- Pas d'intégration Azure / AWS native

Dans ce projet, ces limites ont imposé des contournements (notebook maître, export JSON, FastAPI).

---

## 4. Great Expectations — La validation qualité

### C'est quoi le problème qu'on résout ?

Les données arrivent rarement parfaites. Entre la source et le pipeline, des choses peuvent mal tourner :
- Une colonne censée être un pourcentage contient des valeurs négatives
- Un champ "nom de commune" est vide pour 30 % des lignes
- Un type float reçoit du texte suite à un bug d'export

Sans validation, ces erreurs silencieuses se propagent jusqu'aux tableaux de bord. Les décisions métier sont alors prises sur des données fausses.

**Great Expectations (GX)** permet de définir ce qu'on *attend* des données et de vérifier automatiquement que c'est respecté.

### L'analogie du contrôle qualité en usine

Dans une usine automobile, avant de sortir une voiture, on vérifie :
- Que les 4 roues sont bien fixées
- Que le moteur démarre
- Que la peinture n'a pas de défaut

Great Expectations, c'est la **liste de contrôle qualité** pour les données.

Chaque vérification s'appelle une **Expectation**. Quelques exemples :

```python
# La colonne "global_conformity_rate" ne doit jamais être vide
ExpectColumnValuesToNotBeNull(column="global_conformity_rate")

# Cette valeur doit être entre 0 et 100 (c'est un pourcentage)
ExpectColumnValuesToBeBetween(column="global_conformity_rate", min_value=0, max_value=100)

# Cette colonne doit contenir des flottants
ExpectColumnValuesToBeOfType(column="pollution_score", type_="float64")
```

### Les concepts clés de GX 1.x

L'API de Great Expectations a beaucoup changé entre les versions 0.x et 1.x. Voici les briques importantes dans la version utilisée (1.17+) :

```
[context]               ← Le point d'entrée. Tout passe par lui.
    └── [DataSource]    ← La connexion à une source de données (ici : Pandas)
          └── [Asset]   ← Un dataset précis dans cette source
                └── [BatchDefinition]  ← "Je veux tout le dataframe d'un coup"
                      
[Suite]                 ← Un ensemble d'expectations groupées par table

[ValidationDefinition]  ← Lie une Suite à une BatchDefinition
    └── .run()          ← Lance la validation et retourne un résultat
```

### Ce qui a changé entre 0.x et 1.x (les bugs rencontrés)

| Ancienne API (0.x) | Nouvelle API (1.x) |
|---|---|
| `context.sources` | `context.data_sources` |
| `add_dataframe_asset(dataframe=df)` | `add_dataframe_asset()` puis df dans `.run()` |
| `gx.expectations.expect_column_values_to_not_be_null` | `gx.expectations.ExpectColumnValuesToNotBeNull` |

> Le passage au PascalCase est un choix de cohérence : toutes les Expectations sont désormais des classes Python, donc elles suivent la convention de nommage des classes (PascalCase).

### PASS / FAIL : ce que ça signifie

Quand la validation tourne, GX retourne :
- `PASS` : toutes les expectations sont satisfaites
- `FAIL` : au moins une ne l'est pas

Dans ce projet, le rapport est sauvegardé en JSON pour en garder une trace :

```json
{
  "gold_kpis": "PASS",
  "gold_departements": "PASS",
  "gold_communes_best": "PASS",
  "gold_communes_worst": "PASS",
  "gold_critical": "FAIL"
}
```

Un `FAIL` n'arrête pas nécessairement le pipeline, mais il permet au data engineer de savoir exactement quelle table pose problème.

---

## 5. FastAPI — Exposer les données via une API REST

### C'est quoi une API REST ?

Une API (Application Programming Interface) REST, c'est une façon standardisée d'exposer des données ou des fonctions via le protocole HTTP.

### L'analogie du restaurant

Imagine un restaurant.

- **La cuisine** = la base de données (personne n'y entre directement)
- **Le menu** = la documentation de l'API (ce qu'on peut commander)
- **Le serveur** = l'API (il prend les commandes et revient avec les plats)
- **Toi** = le client (une appli, un tableau de bord, un autre service)

Tu ne vas pas en cuisine chercher ton plat toi-même. Tu passes par le serveur (l'API), qui te ramène exactement ce que tu as demandé, dans le bon format.

### Les verbes HTTP

Une API REST utilise des **verbes** pour indiquer ce qu'on veut faire :

| Verbe | Usage courant | Exemple dans ce projet |
|-------|---------------|------------------------|
| `GET` | Lire des données | `GET /api/kpis` → retourne les KPIs |
| `POST` | Créer une ressource | `POST /api/data` → envoyer de nouvelles données |
| `PUT` | Modifier une ressource | `PUT /api/data/1` → mettre à jour |
| `DELETE` | Supprimer | `DELETE /api/data/1` → supprimer |

Dans ce projet, seuls des `GET` sont utilisés (on expose des données, on ne les modifie pas).

### Ce que FastAPI apporte

FastAPI est un framework Python qui permet de créer une API REST très rapidement.

```python
from fastapi import FastAPI
import json

app = FastAPI()

@app.get("/api/kpis")
def get_kpis():
    with open("exports/api_exposition.json") as f:
        data = json.load(f)
    return data["kpis"]
```

Ce code crée un endpoint accessible à `http://localhost:8000/api/kpis`. Simple et lisible.

### Swagger UI : la documentation automatique

FastAPI génère automatiquement une interface Swagger à `/docs`. C'est une page web interactive qui liste tous les endpoints disponibles et permet de les tester directement dans le navigateur.

```
http://localhost:8000/docs
```

C'est particulièrement utile pour montrer à un jury ou à un client ce que l'API peut faire, sans avoir à écrire la documentation soi-même.

### Pourquoi FastAPI et pas Flask ou Django ?

- **Flask** : plus simple mais sans validation automatique des types
- **Django** : très complet mais beaucoup plus lourd, conçu pour des applications web entières
- **FastAPI** : moderne, rapide, génère la doc automatiquement, valide les types Python nativement

Pour une API de données légère comme celle-ci, FastAPI est le bon outil.

---

## 6. L'orchestration — Faire tourner les pièces dans le bon ordre

### C'est quoi le problème ?

Un pipeline de données, c'est une chaîne d'étapes. Chaque étape dépend de la précédente.

```
Créer les tables  →  Valider la qualité  →  Exporter les dashboards
```

Si l'étape 1 plante, l'étape 2 ne doit **pas** se lancer. Sinon, on validerait des tables vides ou corrompues, et on exporterait des graphiques faux.

L'orchestration, c'est le mécanisme qui :
- Lance les étapes dans le bon ordre
- Arrête la chaîne si une étape échoue
- Fournit des logs pour comprendre ce qui s'est passé

### L'analogie de la chaîne de montage

Dans une usine automobile, la voiture passe par des postes successifs : châssis → moteur → carrosserie → peinture → contrôle qualité.

Si le moteur n'est pas posé, on n'envoie pas la voiture à la peinture. C'est une **dépendance stricte**.

L'orchestration, c'est exactement ça appliqué aux données.

### Databricks Workflows (version Pro)

En version Pro/Enterprise, Databricks propose un outil Workflows avec :
- Un **DAG** visuel (Directed Acyclic Graph) : un graphe qui montre les étapes et leurs dépendances
- Des logs par étape
- Des alertes en cas d'échec
- Un scheduling (lancer le pipeline tous les jours à 6h, par exemple)

```
[01_Create_Tables] ──→ [02_Validate_GE] ──→ [03_Visualise_Export]
```

Si `01_Create_Tables` échoue, les deux suivantes sont bloquées automatiquement.

### Le notebook maître (version Community Edition)

Sans Workflows, on simule ce comportement avec un notebook maître et `%run` :

```python
%run ./01_gold_delta_tables
%run ./02_quality_validation
%run ./03_visualisation_export
```

`%run` est une commande Databricks (et Jupyter) qui exécute un autre notebook dans le contexte courant. Si le premier notebook lève une exception, Python s'arrête et les suivants ne sont pas exécutés. Le comportement est identique.

### C'est quoi un DAG ?

DAG = **Directed Acyclic Graph** (graphe orienté sans cycle).

- **Orienté** : les flèches vont dans un sens (A → B, pas B → A)
- **Sans cycle** : on ne peut pas revenir au point de départ en suivant les flèches

```
    A
   / \
  B   C
   \ /
    D
```

Dans ce DAG, B et C peuvent tourner en parallèle (tous deux dépendent de A), et D ne tourne que quand B et C sont terminés. C'est le modèle standard des outils d'orchestration comme **Airflow**, **Prefect**, **Dagster** — et Databricks Workflows.

---

## 7. Azure Databricks — Ce qui aurait été fait en cloud

### L'écosystème Azure autour des données

Azure (le cloud de Microsoft) propose un ensemble de services qui s'intègrent nativement avec Databricks. Voici ce qui aurait été utilisé dans la version cloud complète du projet.

### Azure Data Lake Storage Gen2 (ADLS Gen2)

C'est le système de stockage de fichiers dans Azure.

**Analogie** : pense à un disque dur externe, mais dans le cloud, accessible depuis n'importe quelle machine, scalable à l'infini, et avec des permissions granulaires par dossier.

Dans ce projet, ADLS Gen2 aurait stocké :
- Les fichiers CSV bruts (Bronze)
- Les fichiers Silver nettoyés
- Les fichiers Gold agrégés

À la place, on a utilisé les **Unity Catalog Volumes** de Databricks Community Edition (un système de stockage interne à Databricks, moins puissant mais disponible gratuitement).

### Azure Data Factory (ADF)

C'est l'outil d'orchestration et d'ingestion d'Azure.

**Analogie** : si Databricks Workflows orchestre les notebooks, ADF orchestre tout l'écosystème Azure (copier des fichiers depuis une API externe vers ADLS, déclencher un pipeline Databricks, envoyer un email si ça échoue, etc.).

Dans ce projet, ADF aurait automatisé :
- Le téléchargement des fichiers depuis data.gouv.fr vers ADLS Gen2
- Le déclenchement du pipeline Databricks à la réception de nouveaux fichiers

À la place, on a utilisé `requests` en Python local.

### Azure SQL Endpoint / SQL Warehouse

Databricks Pro/Enterprise permet d'exposer une table Delta directement comme un endpoint SQL.

**Analogie** : imagine que ta Delta Table gold_kpis devient accessible via une URL SQL standard. N'importe quel outil BI (Power BI, Tableau, Metabase) peut s'y connecter comme à une base de données classique.

Dans ce projet, cet endpoint était indisponible. D'où l'export en JSON et la construction d'une API FastAPI pour simuler cet accès.

### Azure Key Vault

C'est le coffre-fort des secrets dans Azure : tokens d'accès, mots de passe, clés API.

**Analogie** : au lieu de mettre tes clés SSH sous le paillasson (dans le code source), tu les déposes dans un coffre. Les services Azure qui en ont besoin vont les chercher directement, sans que personne ne les voie.

Dans ce projet, les tokens Databricks sont stockés dans un fichier `.env` local (exclu de Git via `.gitignore`). C'est la solution minimaliste équivalente.

### Managed Identity

Dans Azure, une **Managed Identity** permet à un service (par exemple, Data Factory) d'accéder à un autre service (par exemple, ADLS) **sans avoir besoin d'un mot de passe**.

**Analogie** : c'est comme un badge d'entreprise. Le Data Factory a son badge, Azure vérifie que ce badge est autorisé à accéder à ADLS, et la porte s'ouvre. Pas de mot de passe à gérer, pas de risque de fuite.

---

## 8. Le Data Load Tool (DLT)

### C'est quoi ?

Le **Data Load Tool** est un outil d'ingestion de données mentionné dans l'énoncé du projet. Son rôle est d'automatiser le téléchargement et le chargement de données depuis des sources externes (APIs, fichiers, bases de données) vers un environnement cible.

### Pourquoi il n'a pas été utilisé ici ?

Deux raisons principales :

1. **Contexte** : le DLT prend tout son sens dans un écosystème Azure complet, avec des services d'authentification (Key Vault, Managed Identity) et de stockage (ADLS) déjà en place. Sans eux, il perd une partie de sa valeur ajoutée.

2. **Pragmatisme** : en phase d'exploration sur des données inconnues, `requests` + `pandas` offre un contrôle total sur ce qu'on télécharge et comment on le transforme. C'est plus simple à déboguer.

### Quand l'utiliser en production ?

Le DLT deviendrait le bon choix si :
- Les données sont mises à jour régulièrement (tous les jours par exemple)
- Le pipeline tourne en production dans Azure, avec des contraintes de sécurité (authentification managée, audit des accès)
- On a besoin de **retry policies** (si le téléchargement échoue, réessayer automatiquement 3 fois avant d'alerter)

---

## 9. Pandas vs PySpark — Deux moteurs, deux contextes

### La question fondamentale

Quand utiliser l'un plutôt que l'autre ?

La réponse tient en une phrase : **utilise le plus simple qui répond au besoin**.

### Tableau de décision

| Critère | Pandas | PySpark |
|---------|--------|---------|
| Volume de données | < 1 Go confortablement, jusqu'à ~10 Go avec optimisation | Scalable à l'infini (Go → To) |
| Vitesse de développement | Rapide, syntaxe intuitive | Plus verbeux, plus de configuration |
| Débogage | Facile (tout est en mémoire, affichage immédiat) | Plus complexe (exécution distribuée) |
| Exécution | Séquentielle sur un seul cœur (par défaut) | Parallèle sur plusieurs machines |
| Contexte idéal | Exploration, prototypage, petits volumes | Production, gros volumes, cloud |
| Modèle d'exécution | Eager (résultat immédiat à chaque opération) | Lazy (rien ne s'exécute tant qu'on n'a pas demandé le résultat) |

### L'évaluation lazy de Spark

C'est un concept important. Avec Spark, quand tu écris :

```python
df = spark.read.csv("huge_file.csv")
df_filtered = df.filter(df["score"] > 50)
df_grouped = df_filtered.groupBy("dept").count()
```

**Rien ne s'exécute** à ces trois lignes. Spark construit un plan d'exécution.

Ce n'est qu'à la ligne suivante (`.show()`, `.collect()`, `.write()`) que le plan est exécuté en une seule passe optimisée.

**Avantage** : Spark peut optimiser le plan avant de l'exécuter. Il peut par exemple décider de filtrer les données **avant** de les charger entièrement, réduisant drastiquement la quantité de données traitées.

**Inconvénient** : le débogage est moins intuitif. Une erreur peut n'apparaître qu'au moment du `.collect()`, loin de la ligne qui la cause.

### Dans ce projet : la combinaison pragmatique

```
Local (Pandas) : Bronze + Silver + Gold
    → Volumes gérables (~6,8 Go), besoin de flexibilité pour explorer
    → Itération rapide, débogage facile

Databricks (PySpark) : Chargement Delta + Validation + Export
    → Intégration avec l'environnement Databricks
    → Spark est déjà là, autant l'utiliser pour les opérations sur cluster
```

---

## 10. Unity Catalog et la gouvernance des données

### C'est quoi la gouvernance des données ?

La gouvernance, c'est l'ensemble des règles qui définissent **qui peut accéder à quoi**, et dans quel format les données sont organisées.

Sans gouvernance, dans une grande entreprise :
- Deux équipes créent deux tables avec le même nom et des définitions différentes
- Personne ne sait quelle version est la bonne
- Un analyste accède à des données confidentielles sans le savoir

**Unity Catalog** est la solution de Databricks pour centraliser cette gouvernance.

### La structure à trois niveaux

Unity Catalog organise les données en trois niveaux :

```
[Catalog]          ← Le niveau le plus haut (ex: "workspace")
    └── [Schema]   ← Un espace de noms (ex: "default", "eau", "finance")
          └── [Table / View / Volume]  ← Les objets réels
```

Dans ce projet :
```
workspace.default.gold_kpis         ← Table Delta Gold
workspace.default.gold_departements ← Table Delta Gold
/Volumes/workspace/default/eau/     ← Stockage de fichiers (CSV, JSON, HTML)
```

### Les Volumes

Un **Volume** dans Unity Catalog, c'est un espace de stockage de fichiers (pas de tables). C'est l'équivalent d'un dossier dans ADLS Gen2, mais géré directement par Databricks.

Dans ce projet, les Volumes ont servi à :
- Stocker les fichiers CSV Gold importés depuis la machine locale
- Stocker les exports HTML des dashboards
- Stocker le rapport JSON de validation Great Expectations

---

## 11. Swagger UI — La documentation vivante d'une API

### Le problème de la documentation classique

La documentation classique (un fichier Word, un PDF) vieillit mal. Le code change, la doc reste en retard. Quelques mois plus tard, personne ne sait si la doc est à jour.

**Swagger UI** résout ce problème en générant la documentation **directement depuis le code**.

### Comment ça marche avec FastAPI ?

FastAPI utilise les **annotations de types Python** pour inférer automatiquement le schéma de chaque endpoint.

```python
@app.get("/api/departments", response_model=list[DepartmentKPI])
def get_departments():
    """Retourne le top 10 des départements par score de pollution."""
    ...
```

FastAPI lit cette définition et génère automatiquement :
- La liste des endpoints disponibles
- Les paramètres attendus et leurs types
- Les exemples de réponses
- Un bouton "Try it out" pour tester en live

### OpenAPI

Swagger UI est basé sur le standard **OpenAPI** (anciennement Swagger). C'est un format JSON/YAML qui décrit une API de manière standardisée.

L'URL `/openapi.json` dans FastAPI retourne ce document. N'importe quel outil compatible OpenAPI peut l'importer et générer des clients automatiquement.

---

## 12. GitHub Actions — L'intégration et le déploiement continus (CI/CD)

### C'est quoi le problème qu'on résout ?

Quand un projet de données grandit, plusieurs personnes (ou toi à des moments différents) modifient le code. À chaque modification, une question se pose : **est-ce que j'ai cassé quelque chose sans le savoir ?**

Sans automatisation, la réponse c'est : "je ne sais pas, j'espère que non."

**GitHub Actions** permet de répondre automatiquement à cette question à chaque fois que du code est poussé sur le dépôt.

### C'est quoi le CI/CD ?

Deux concepts liés :

**CI — Intégration Continue (Continuous Integration)**
À chaque push sur GitHub, une série de vérifications se lance automatiquement :
- Les tests passent-ils toujours ?
- Le code respecte-t-il les conventions de style ?
- Les agrégats Gold donnent-ils les bons résultats ?

Si quelque chose échoue, GitHub t'avertit immédiatement. Tu sais exactement quel commit a cassé quoi.

**CD — Déploiement Continu (Continuous Deployment)**
Si tous les tests passent, le code est automatiquement déployé en production (sur un serveur, dans le cloud, etc.) sans intervention manuelle.

Dans ce projet, le CD n'est pas implémenté (pas de serveur de prod). Mais le CI, lui, est mentionné comme perspective d'amélioration.

### L'analogie du filet de sécurité

Imagine un acrobate qui fait des figures de plus en plus complexes.

Sans filet : chaque nouvelle figure est risquée. Une erreur = chute directe.

Avec filet (GitHub Actions) : il peut essayer, tester, se rater. Le filet attrape l'erreur avant qu'elle n'atteigne la production.

### Comment ça marche concrètement ?

GitHub Actions lit des fichiers YAML placés dans `.github/workflows/` à la racine du dépôt.

Voici un exemple concret pour ce projet — un workflow qui vérifie les agrégats Gold à chaque push :

```yaml
# .github/workflows/validate_gold.yml

name: Validation des agrégats Gold

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - name: Récupérer le code
        uses: actions/checkout@v3

      - name: Installer Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Installer les dépendances
        run: pip install -r requirements.txt

      - name: Lancer les tests de non-régression
        run: python tests/test_gold_aggregates.py
```

### Décomposition du fichier YAML

```
on: push / pull_request   ← Quand déclencher le workflow
jobs:                      ← Ce qu'on veut faire
  runs-on: ubuntu-latest   ← Sur quel type de machine (GitHub en fournit gratuitement)
  steps:                   ← Les étapes dans l'ordre
    - checkout             ← Télécharger le code du dépôt
    - setup-python         ← Installer Python
    - pip install          ← Installer les dépendances
    - python test.py       ← Lancer les tests
```

### Un test de non-régression, c'est quoi ?

C'est un test qui vérifie qu'une valeur calculée ne change pas de façon inattendue.

```python
# tests/test_gold_aggregates.py
import pandas as pd

def test_global_conformity_rate():
    df = pd.read_csv("data/gold/gold_kpis.csv")
    rate = df["global_conformity_rate"].iloc[0]
    # On sait que le taux de conformité doit être entre 85% et 100%
    assert 85 <= rate <= 100, f"Taux de conformité anormal : {rate}"

def test_nombre_departements():
    df = pd.read_csv("data/gold/gold_departements.csv")
    # La France a 101 départements (DOM inclus)
    assert len(df) <= 101, f"Trop de départements : {len(df)}"

if __name__ == "__main__":
    test_global_conformity_rate()
    test_nombre_departements()
    print("Tous les tests passent.")
```

Si demain une modification du pipeline Silver change le calcul du taux de conformité de façon inattendue, le test échoue immédiatement sur GitHub. Tu es prévenu avant même de merger le code.

### Le statut visible sur GitHub

Après chaque push, GitHub affiche un badge vert (succès) ou rouge (échec) directement sur la page du dépôt et sur chaque commit.

```
✅ All checks passed   ← Le pipeline est sain
❌ 1 check failed      ← Quelque chose a cassé, voir les logs
```

C'est ce que les recruteurs et les jurys voient quand ils visitent un dépôt : un projet avec des checks verts montre une démarche de qualité professionnelle.

### Ce qui aurait été fait dans ce projet

La perspective mentionnée dans la documentation : intégrer dans GitHub Actions la **validation des agrégats Gold**.

Concrètement, à chaque push sur le dépôt :
1. Recalculer les agrégats Gold depuis le Silver
2. Vérifier que les valeurs clés (taux de conformité global, nombre de départements, etc.) sont dans les plages attendues
3. Bloquer le merge si une régression est détectée

C'est la brique qui transforme un projet académique en projet à maturité professionnelle.

---

## 13. La vue d'ensemble — Comment tout s'assemble

### Le fil conducteur du projet

```
1. INGESTION (Bronze)
   data.gouv.fr → requests/Python → CSV brut local

2. NETTOYAGE (Silver)
   CSV brut → Pandas (nettoyage, dédup, validation GX locale) → CSV propre

3. AGGREGATION (Gold)
   CSV propre → Pandas (groupBy, moyennes, top10) → 5 CSV Gold

4. INTÉGRATION DATABRICKS
   5 CSV Gold → Upload vers Unity Catalog Volumes → PySpark → Delta Tables

5. VALIDATION QUALITÉ
   Delta Tables → Great Expectations → rapport JSON (PASS/FAIL par table)

6. EXPOSITION
   Delta Tables → PySpark → Fichiers HTML (dashboards Plotly) + JSON

7. API
   JSON Gold → FastAPI → Endpoints REST → Swagger UI
```

### Pourquoi ce projet est représentatif du métier de Data Engineer

Un Data Engineer, son travail c'est exactement ça :

- **Ingérer** : aller chercher les données là où elles sont
- **Transformer** : les rendre propres, cohérentes, utilisables
- **Stocker** : dans le bon format, au bon endroit, avec les bonnes permissions
- **Valider** : garantir que la qualité est au rendez-vous
- **Exposer** : rendre les données accessibles aux consommateurs (analystes, APIs, dashboards)

Chaque technologie utilisée dans ce projet répond à l'un de ces besoins. Ce n'est pas un empilement arbitraire d'outils : c'est une architecture qui reflète les décisions techniques réelles du terrain.

---

> *Ce document est personnel et évolutif. N'hésite pas à y ajouter des notes au fil des projets suivants.*
