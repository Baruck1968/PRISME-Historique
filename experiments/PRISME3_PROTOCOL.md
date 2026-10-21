# PRISME 3 — Faisabilité des observations à dates calendaires fixes

Statut : protocole proposé avant exécution. PRISME 1 et PRISME 2 demeurent inchangés.

## Question
À probabilité courante comparable, la variation de probabilité pendant les 24 heures précédentes améliore-t-elle la prédiction de l'issue binaire sur des marchés historiquement ouverts à une date d'observation fixée sans connaissance de leur résolution ?

## Test de faisabilité (prioritaire)
1. Réutiliser les archives Manifold déjà contrôlées, sans télécharger inutilement 1 Go avant d'avoir vérifié les prérequis.
2. Définir à l'avance une grille hebdomadaire de dates UTC couvrant une portion documentée de l'archive, sans choisir les dates selon les issues. Pour chaque date t, déterminer les marchés créés avant t, non résolus à t selon les horodatages disponibles, puis identifier les limites de ce proxy (résolution anticipée, publication de l'issue, clôture et éditions).
3. Vérifier par audit manuel, sur un sous-échantillon déterministe indépendant des issues, si les données permettent de confirmer que le marché était négociable et l'issue inconnue à t. Ne pas confondre « non résolu dans le snapshot » et « résultat encore inconnu ».
4. Examiner la possibilité de reconstruire p(t), p(t-24 h), la fraîcheur des prix, les ordres exécutés et les changements de mécanisme DPM/CPMM. Contrôler la couverture effective de l'archive des transactions et les différences de dates des deux dumps.
5. Identifier les marchés qui représentent un même événement et documenter une règle de regroupement indépendante des résultats. Prévenir le chevauchement train/test, y compris pour les observations multiples d'un même marché.
6. Produire un tableau de flux (marchés considérés, exclusions, trajectoires complètes, observations vérifiées), un audit de fuite et un rapport de faisabilité avec sources, empreintes et tests.

## Analyse conditionnelle (uniquement si faisabilité validée)
- Une seule observation principale par marché, choisie par une règle temporelle déterministe sans consultation de l'issue. Des observations répétées sont réservées à une analyse de sensibilité groupée par marché et événement.
- Baseline : calibration flexible de p(t), âge du marché et autres covariables véritablement disponibles à t. Modèle enrichi : mêmes variables plus delta = p(t)-p(t-24 h).
- Comparer hors échantillon chronologique Brier et log-loss, avec incertitude regroupée par événement. Ne pas optimiser sur le test final.
- Rapporter les distributions de p(t), les effectifs par tranches de 0,05 et le recouvrement des directions delta >= +0,02 et <= -0,02. Ne pas fabriquer un recouvrement par réglage opportuniste.
- Si l'instant de négociabilité, l'inconnaissance de l'issue ou les prix historiques ne sont pas vérifiables, **arrêter avant le test prédictif**, indiquer les blocages et proposer des sources alternatives documentées.

## Invariants
Aucun résultat simulé présenté comme réel. Aucune transaction, aucun pari, aucun ordre, aucune opération financière ni contournement de restriction. Conserver intégralement les expériences précédentes.
