# PRISME Observatoire — spécification V1

Date : 2026-10-21. Phase : faisabilité. Aucun relevé effectif encore collecté ; aucune alerte active.

## Décision utilisateur
- Toutes sources de cotes fiables, y compris hors France, acceptées pour **observation scientifique**.
- Sports / marchés à exactement deux issues exclusives et exhaustives (h2h/moneyline, prolongations incluses ou exclues selon règlement clairement identifié). Exclure les marchés 1X2 et les règles ambiguës.
- Relevés ciblés à T−24 h et T−1 h, où T est **l'heure effective de clôture des paris si disponible** ; sinon heure prévue de début d'événement, explicitement étiquetée comme proxy et non présentée comme heure de clôture.
- Cotes décimales pour chacune des deux issues ; surveiller hausses et baisses ; signaler |100×(C_H1−C_J1)/C_J1| >= 20 %.
- L'utilisateur décide de toute action éventuelle ; PRISME ne transmet aucune mise ni ordre.

## Contraintes de validité
- Même événement, même marché et règles, même issue, **même bookmaker** entre les deux observations. Jamais de comparaison inter-bookmakers pour une variation individuelle.
- Horodatages UTC de la capture, de la dernière mise à jour du bookmaker, et de l'événement ; provenance et identifiants source. Exclure les observations absentes, périmées, suspendues, décalées, ou modifiées.
- Si plusieurs bookmakers sont disponibles, présenter les variations individuelles et éventuellement une synthèse robuste sur les bookmakers appariés, sans confondre prix et information privée.
- Conserver également les non-alertes ; journal append-only, audit des doublons et décalages d'heure, absence de lookahead.
- Aucune prétention de rentabilité, de faible risque ou d'accès aux transactions d'acteurs informés.

## Sources à auditer
- The Odds API : https://the-odds-api.com/liveapi/guides/v4/ ; https://the-odds-api.com/historical-odds-data/ ; archives payantes, snapshots 5 minutes depuis septembre 2022. Vérifier conditions, prix, accès live et couverture.
- TheOddsAPI : https://theoddsapi.com/docs/ ; https://theoddsapi.com/pricing ; **fournisseur distinct** du précédent, avec couverture et tarification propres.
- Toute autre source légale, fiable et compatible avec un usage automatisé ; pas de scraping non autorisé.

## Premier livrable technique
Audit de faisabilité **sans achat ni clé API supposée** : comparaison sourcée de deux à trois fournisseurs, possibilités d'un essai gratuit en lecture seule, champs exacts, latence, quotas, prix et conditions. Puis proposition d'une collecte pilote horodatée, de son stockage et de ses tests. Ne pas activer d'alertes avant vérification d'un flux de données. Ne pas promettre une précision temporelle que GitHub Actions ne garantit pas.

## Invariants
Préserver PRISME 1–4. Ne pas engager d'argent, ni connecter de compte bookmaker, ni publier de secrets.
