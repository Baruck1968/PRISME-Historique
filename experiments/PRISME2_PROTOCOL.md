# PRISME 2 — Protocole prospectivement fixé (avant nouvelle collecte)

Date : 2026-10-21. Statut : plan d'expérience, **aucune nouvelle collecte ni analyse exécutée**.

## Question et hypothèses
Pour des marchés binaires résolus, la variation récente de probabilité \(\Delta p\) apporte-t-elle de l'information sur \(Y\in\{0,1\}\) **conditionnellement** à la probabilité courante \(p_t\), à l'horizon avant l'échéance et aux caractéristiques observables du marché ?

- H0 : à covariables fixées, l'ajout de \(\Delta p\) n'améliore pas la prédiction hors échantillon.
- H1 : l'ajout de \(\Delta p\) améliore la prédiction hors échantillon.
- Direction positive (continuation) et négative (retour à la moyenne) restent toutes deux possibles.

## Principes de conception
1. **Conserver PRISME 1 inchangé** : code, cache, résultats et limitations.
2. Avant la collecte, identifier une source publique historique avec prix horodatés, issues binaires et, autant que possible, échéance annoncée à l'avance. Vérifier termes d'utilisation, complétude, unités et identifiants. Privilégier un historique étendu plutôt qu'une sélection des 200 marchés les plus récemment créés.
3. Fixer \(t\) par rapport à une **échéance connue ex ante**, non à \(resolutionTime\). Vérifier manuellement un sous-échantillon pour exclure toute connaissance publique du résultat à \(t\). Si l'échéance fiable est absente, étiqueter l'étude descriptive et ne pas faire de revendication prédictive.
4. Mesures principales : \(p_t\), \(p_{t-24h}\), \(\Delta p=p_t-p_{t-24h}\), \(Y\). Documenter le dernier prix disponible et sa fraîcheur, les prix extrêmes, la liquidité et les changements de marché. Garder une seule observation principale par marché et une clé d'événement commun.
5. Fixer la fenêtre principale à 24 h, le seuil descriptif à \(\pm0{,}02\) point de probabilité et les strates descriptives de \(p_t\) à 0,05. Ne pas assouplir les seuils après observation des issues pour fabriquer du recouvrement. Publier tous les effectifs par strate.
6. Si le recouvrement hausse/baisse est insuffisant, **ne pas calculer de contraste apparié ni de valeur p**. Augmenter l'échantillon par la règle de collecte préfixée ; publier les exclusions et le taux de couverture. Les variantes de seuils et de fenêtres seront explicitement exploratoires.
7. Évaluation principale : comparer sur une **période chronologiquement postérieure non utilisée pour ajuster les modèles** (a) une calibration flexible de \(p_t\), de l'horizon et des covariables admissibles, (b) la même calibration avec \(\Delta p\). Comparer Brier et log-loss, avec intervalles d'incertitude regroupés par événement ; décrire calibration et couverture. Empêcher qu'un même événement apparaisse dans entraînement et test.
8. Ne pas choisir les hyperparamètres, la source ou les filtres à partir des performances sur le test final. Si trop peu d'événements indépendants, signaler « non concluant ».
9. Fournir script reproductible, dépendances minimales, cache ou références immuables, empreintes, contrôles d'horodatage, tests de non-fuite, rapports machine-lisibles et README.
10. **Lecture seule** : aucun pari, ordre, transaction, fonds ou contournement de restriction géographique.

## Critère de décision
PRISME 2 ne conclura à un signal prédictif additionnel que si le modèle avec variation améliore la prédiction sur la période réservée, avec une incertitude compatible avec un effet non trivial, et sans fuite temporelle ni dépendance non traitée. Sinon : effet non démontré ; en cas de données insuffisantes : test non concluant.

## Première action technique
Auditer les archives historiques Manifold déjà repérées (marchés et transactions, dates de couverture différentes) et comparer la faisabilité d'un corpus plus large, avant de lancer une collecte volumineuse. Produire un rapport de faisabilité et les règles d'échantillonnage figées. Ne pas modifier les fichiers du pilote.
