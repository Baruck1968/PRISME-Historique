# PRISME — Étude de sources de cotes sportives (phase préalable)

Date : 2026-10-21. Statut : cadrage documentaire ; **aucune acquisition payante, aucun pari et aucune simulation de rendement exécutés**.

## Objet
Évaluer si les mouvements de cotes précédant un événement sportif contiennent une information prédictive additionnelle **et** si un éventuel signal reste économiquement positif aux cotes effectivement accessibles, après coûts. Aucune rentabilité n'est présumée.

## Sources candidates et contraintes
1. Football-Data (https://www.football-data.co.uk/downloadm.php) : résultats, cotes d'ouverture et de clôture sur plusieurs saisons ; **pas de trajectoires à dix minutes**. Le site annonce un usage privé et exclut notamment des usages automatisés/scraping/IA. Ne pas télécharger ni traiter automatiquement sans vérifier l'autorisation applicable.
2. The Odds API (https://the-odds-api.com/historical-odds-data/ et https://the-odds-api.com/liveapi/guides/v4/) : captures historiques annoncées à intervalles de cinq minutes depuis septembre 2022 ; accès historique payant. Vérifier tarifs, quotas, opérateurs effectivement couverts, droits d'utilisation et horodatages ; ne pas acheter sans autorisation explicite.
3. ANJ (https://www.anj.fr/offre-de-jeu-et-marche/operateurs-agrees) : vérifier les opérateurs agréés en France et les restrictions applicables ; un opérateur couvert par un fournisseur international n'est pas nécessairement accessible légalement depuis la France.

## Audit à effectuer avant collecte
- Comparer couverture réelle des opérateurs agréés en France, disponibilité des cotes pré-match horodatées à t-20, t-15, t-10 minutes, horodatages d'événement et disponibilité des issues.
- Distinguer l'heure annoncée de début du match, la fermeture réelle des paris et le moment où les cotes étaient effectivement disponibles. Ne jamais assimiler automatiquement le début du match à la clôture du marché.
- Distinguer les modifications de cotes (prix affichés) des mises ou décisions des bookmakers ; ne pas prétendre observer directement l'information privée ou les transactions d'initiés.
- Contrôler les marges intégrées (overround), le prix réalisable, les plafonds de mise, frais, annulations et changements de prix. La conversion 1/cote n'est pas une probabilité nette sans correction de marge.
- Éviter toute sélection après consultation des issues ; scinder les événements dans le temps, regrouper les marchés liés à un même match ; évaluer sur une période réservée.
- Évaluer d'abord la faisabilité et la conformité des sources ; pas de stratégie de mise ni d'automatisation de paris réels.

## Livrable attendu
Rapport comparatif documenté : couverture, conditions d'accès, limites, coût prévisionnel et recommandation d'une source admissible pour une **étude en lecture seule**. Si aucune source appropriée n'est trouvée, l'indiquer explicitement et ne pas inventer de résultats.

## Invariants
PRISME 1 à 4 inchangés. Aucun achat, pari, ordre, dépôt, transaction ou connexion à un compte de jeu.
