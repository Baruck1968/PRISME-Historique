# PRISME 4 — Pilote prospectif borné, protocole préalable

Statut : protocole publié **avant la première capture**. Ce fichier n'atteste ni une collecte en cours ni une programmation automatique.

## Question
À probabilité courante p(t) comparable, la variation p(t)-p(t-24 h) améliore-t-elle la prévision d'une issue binaire encore inconnue à t ? Distinguer cet objectif des prévisions de mouvements de prix ultérieurs.

## Phase 0 — faisabilité de la collecte
- Vérifier une méthode autorisée de captures publiques **en lecture seule** de Manifold, sans clé de négociation, et une infrastructure capable de fonctionner selon une cadence prédéfinie sans intervention manuelle.
- Ne pas affirmer que la collecte est programmée tant qu'une tâche réelle n'a pas été installée, déclenchée et contrôlée.
- Tester une capture et son rejeu, vérifier UTC, identifiants, version des règles et horodatage local de réception ; empreintes SHA-256 et journal d'erreurs. Ne jamais substituer les valeurs actuelles aux données historiques manquantes.
- Vérifier que les issues et la négociabilité ne sont pas déjà connues à t ; documenter les cas ambigus et les exclure du test prédictif.

## Cadre borné
- Durée initiale proposée : **8 semaines à partir de la première capture réellement réussie** ; cadence proposée : **une capture quotidienne à heure UTC fixe**. Ces paramètres doivent être confirmés avant le déploiement.
- Population : marchés binaires publics ouverts, avec règles de résolution suffisamment objectives et vérifiables ; fixer le mécanisme de sélection avant la collecte. Ne pas sélectionner d'après les issues.
- Capturer les états bruts et leurs métadonnées, sans modifier les marchés : identifiant, question, dates, probabilité courante, type/mécanisme, état de résolution, disponibilité des transactions, et informations permettant d'auditer les événements communs. Capturer les mises à jour de marché si l'API le permet ; ne pas inventer les historiques d'édition.
- Observation principale par marché : premier t admissible avec deux captures à 24 h d'intervalle ; une observation indépendante par marché pour l'analyse principale. Conserver les autres captures pour audit et sensibilité.
- Fraîcheur des prix : définir un contrôle séparé de l'actualité de la dernière transaction ; la probabilité effectivement affichée dans une capture horodatée n'est pas une transaction nécessairement récente.
- Exclure les marchés dont l'issue était déjà publiquement connue à t ; audit externe déterministe sur une sous-cohorte. Identifier et regrouper les marchés du même événement avant découpage train/test.
- Critère descriptif secondaire : delta >= +0,02 et <= -0,02 ; strates de probabilité de largeur 0,05. Ne pas modifier les seuils après consultation des résultats.

## Évaluation
- Baseline : p(t), avec éventuelle calibration estimée **sans données du test** ; modèle enrichi : mêmes covariables disponibles à t, plus delta.
- Comparaison Brier/log-loss hors échantillon chronologique et par événements indépendants, avec incertitude groupée par événement. Aucun score si les conditions ne sont pas réunies.
- Publier tous les effectifs, exclusions, manques de captures, erreurs réseau et diagnostics de recouvrement.
- Si le volume de marchés résolus indépendants est insuffisant au terme des huit semaines, déclarer « non concluant » plutôt que prolonger automatiquement ou assouplir les règles.

## Décision finale
À l'échéance, choisir explicitement entre : (1) poursuivre avec puissance statistique justifiée et infrastructure validée ; (2) redéfinir une question de recherche distincte, sans présenter celle-ci comme une confirmation ; (3) arrêter PRISME. Une absence d'effet ou de données admissibles doit être rapportée sans embellissement.

## Invariants
Conserver PRISME 1–3 inchangés. Aucune transaction, aucun pari, ordre, mouvement de fonds ou contournement de restriction. Aucune collecte automatique n'est créée par ce document.
