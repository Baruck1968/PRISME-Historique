# PRISME Observatoire V1 — faisabilité documentaire et technique

Audit du 21 octobre 2026, horodatages UTC. Application de [PRISME_OBSERVATOIRE_V1.md](PRISME_OBSERVATOIRE_V1.md). **Collecteur manuel préparé et testé ; aucune capture live de cotes, aucune paire J−1/H−1 et aucune alerte active.** Aucun achat, inscription, compte bookmaker, pari ou ordre. PRISME 1–4 et leurs données restent inchangés.

## Conclusion

Une collecte prospective gratuite en lecture seule est **documentairement réalisable avec une clé gratuite The Odds API**, dans un petit périmètre. Elle n'est pas démontrée opérationnellement ici : aucune clé n'est présente sous `ODDS_API_KEY`, `THE_ODDS_API_KEY` ou `THEODDSAPI_KEY`, et aucune liaison secrète n'est déclarée dans l'environnement observé. Aucune requête live authentifiée n'a été faite. Une clé gratuite est une condition d'accès, pas un achat autorisé implicitement.

Deux obstacles scientifiques subsistent indépendamment de la clé : la preuve que chaque marché est effectivement ouvert et la connaissance de ses règles exactes. Le flux peut conserver un marché suspendu pendant environ 15 minutes. Un `h2h` à deux prix ne garantit pas l'exhaustivité si un match nul, une annulation, un abandon ou un remboursement sont possibles. Le code refuse donc de transformer des variations candidates en alertes validées lorsque ces éléments manquent.

**TheOddsAPI (`theoddsapi.com`) a été vérifié séparément de The Odds API (`the-odds-api.com`).** Après des blocages initiaux du proxy, ses pages sont devenues accessibles. Il annonce une offre gratuite sans carte : **25 requêtes/jour, NFL/NBA/MLB, moneyline, opérateurs US**. Cette seconde option prospective est également conditionnée à une clé gratuite et à une validation du flux. Ses règles de conservation à long terme sont moins explicites que celles du premier fournisseur. Les conditions ne permettent pas d'identifier une personne morale enregistrée avec la précision du premier : elles indiquent « operated by TheOddsAPI » et une juridiction Delaware, ce qui ne suffit pas à établir une société enregistrée. Aucune clé n'a été envoyée à l'un ou l'autre. La FAQ de TheOddsAPI confirme explicitement que les domaines avec tirets et chemins `/v4/` désignent un autre service [S9].

## Comparaison des deux sources demandées

| Critère | The Odds API — `the-odds-api.com` | TheOddsAPI — `theoddsapi.com` |
|---|---|---|
| Preuve consultée | Pages officielles docs, prix, conditions, marchés, historique, intervalles : HTTPS 200, contenu vérifié | Docs, tarifs, conditions, FAQ, présentation et OpenAPI : HTTPS 200 après refus proxy initiaux |
| Identité | Conditions : The Odds API Pty Ltd, société australienne, ACN 627461947 | Conditions « operated by TheOddsAPI », droit du Delaware ; société enregistrée non identifiée [S8] |
| Gratuit | Starter : 500 crédits/mois, clé reçue après inscription, tous sports/marchés, **la plupart** des bookmakers [S1,S2] | 25 requêtes/jour, NFL/NBA/MLB, `h2h`, US books ; sans carte, clé requise [S7] |
| Tarifs payants, non souscrits | 20 000 : 30 USD/mois ; 100 000 : 59 ; 5 millions : 119 ; 15 millions : 249 [S2] | Professional 29 USD/mois : 20 000 (667/jour) ; Business 99 USD/mois : 200 000 (6 667/jour) ; pas de surcoût automatique annoncé [S7] |
| Historique | Payant uniquement ; marchés principaux depuis juin 2020, snapshots 10 min puis 5 min depuis septembre 2022 ; disponibilité variable des opérateurs [S3] | Business uniquement ; données annoncées depuis 2026-05-13 ; changements de prix, pas suppressions/clôtures [S7] |
| Collecte prospective | GET `/v4/sports/{sport}/odds/`, `bookmakers`, `markets=h2h`, `oddsFormat=decimal`, `dateFormat=iso` [S1] | GET `https://api.theoddsapi.com/odds/`, `sport_key`, `markets=h2h`, `bookmakers`, `oddsFormat=decimal` ; en-tête `x-api-key` [S7] |
| Coût live | Marchés × régions ; en sélection explicite, chaque groupe de 10 bookmakers compte comme une région ; une sélection d'un bookmaker et `h2h` coûte normalement 1 crédit non vide [S1] | Quota en requêtes/jour, remise à zéro 00:00 UTC ; 304 ETag annoncés gratuits, à confirmer avec compteurs ; pas de multiplication régions importée du voisin [S7,S9] |
| Horodatages | `commence_time`, `markets[].last_update` ; champ bookmaker déprécié ; UTC local début/fin de requête ajouté [S1] | `event_id`, `start_time` UTC, opérateur `book` ; documentation cite `last_update` et FAQ `updated_at` : contrat exact live à vérifier ; historique `captured_at` distinct de `last_update` [S7,S9] |
| Cadence annoncée | Marchés principaux : 60 s avant match, 40 s en jeu ; réduction progressive à partir de H−6 ; exchanges 20/10 s [S4] | Annonce jusqu’à 30 s pour sports US prioritaires, 60–300 s ailleurs ; pas de SLA standard, non mesuré ; applicabilité exacte au Free à confirmer [S8,S9] |
| État ouvert / fermeture effective | Pas de garantie d'acceptation des paris ni heure effective de clôture dans le schéma examiné ; suspension détectable seulement indirectement et avec retard [S1] | Pas de clôture effective attestée ; historique enregistre changements et non retraits de lignes [S7] |
| Règles / deux issues | `h2h` : gagnant équipe/joueur, inclut le nul au football ; règlement opérateur/prolongations non certifié par la seule clé du marché [S5] | `h2h` gratuit documenté ; règles opérateur/prolongations et exhaustivité non attestées [S7] |
| Conservation | Conditions autorisent conservation indéfinie, recherche et produits dérivés ; interdisent redistribution des données comme produit/flux brut autonome [S6] | Recherche et applications analytiques autorisées ; cache ETag documenté ; redistribution bulk concurrente interdite. Durée de conservation et droit après fin de licence non explicités : confirmation nécessaire pour archive permanente [S8,S9] |
| Résultats futurs | `/scores` pour certains sports, résultats récents jusqu'à 3 jours via `daysFrom`, coût 2 avec ce paramètre ; ne remplace pas un historique complet [S1] | `/historical/settlements` Business : résultats des edges notés et scores finaux, pas un service exhaustif de résultats gratuits ; pas de standalone live scores selon FAQ [S7,S9] |

Les 60 secondes sont une **cadence annoncée**, pas une mesure de latence ni un engagement d'exactitude. L'heure de capture ne doit pas être substituée à celle du prix. La précision de chaîne ISO ne prouve pas la précision de l'horloge. Les pages documentaires ne démontrent pas la couverture effective d'un match à J−1 puis H−1 ni l'accès à un opérateur précis dans le plan gratuit.

### Incertitudes propres à TheOddsAPI

L'OpenAPI public renvoie pour la réponse 200 de `/odds/` un schéma vide (`schema: {}`) ; il ne valide donc pas les champs attendus. La FAQ cite `updated_at` par opérateur tandis que la présentation cite `last_update`. La FAQ et la documentation divergent aussi sur des fonctionnalités historiques (FAQ : archive parfois présentée comme dérivable en Pro ; référence endpoint : Free et Pro refusés, Business requis). Retenir la restriction la plus explicite, sans achat ni essai payant. Les annonces de performances et d'« edges » ne sont pas des résultats indépendamment validés et ne sont pas reprises comme preuves scientifiques. Aucun endpoint d'arbitrage, de recommandation ou de pari n'est utilisé.

Les conditions autorisent expressément les applications de recherche mais la licence est révocable et cesse à la terminaison ; elles ne contiennent pas la permission explicite de conservation indéfinie du fournisseur avec tirets. Le cache opérationnel documenté ne vaut pas permission d'archive publique permanente. Avant de retenir ce flux comme archive scientifique durable, demander une confirmation écrite des droits de conservation privée, après résiliation et de publication des agrégats ; aucun message n'a été envoyé au fournisseur. Ne pas publier les données brutes.

## Audit concret et traçabilité

Les journaux `research/observatoire_v1/access_*.json` contiennent chaque URL documentaire, heure de tentative, résultat HTTP ou erreur proxy, taille et SHA-256 des pages accessibles. Les originaux sont conservés localement sous `.cache/` et ne constituent pas une base de cotes publiée. Le premier essai de la page des intervalles avait un mauvais chemin (`odds-update-intervals.html`) : redirection vers `/404.html`, HTTP 200, donc échec documentaire. La page liée officiellement `update-intervals.html` a ensuite été lue et vérifiée. Le script marque désormais les soft 404 connues. Les anciens essais restent conservés.

Le réseau est restreint. L'ajout de `theoddsapi.com`, `www.theoddsapi.com` et `api.theoddsapi.com` est **enregistré dans le brouillon** en préservant les autres domaines ; il ne prouve pas l'application au runtime. Les pages documentaires ont finalement répondu HTTP 200 ; conserver les refus initiaux comme trace du diagnostic. Le domaine API a été ajouté après identification dans les docs, sans appel authentifié. Pour pérenniser ces accès, revoir et enregistrer les paramètres de l’environnement puis le publier. Aucun domaine API n’a été deviné. Aucun contournement du proxy.

## Contrat de validité du pilote

L'observation porte sur une **variation de cote décimale** : `100 × (C_H1 − C_J1) / C_J1`. Une hausse de cote n'est pas une hausse de probabilité implicite. Le seuil inclusif est +20 % ou −20 %, calculé en décimal exact. Aucun résultat prédictif ou économique ne peut être conclu d'une variation seule.

Le comparateur exige même fournisseur, événement, sport, opérateur, marché, règles et noms des deux issues. Il ne calcule aucune variation si ces identités changent. Il rejette trois issues, doublons d'identifiants, données absentes, prix non finis ou ≤1, déplacement d'heure et capture hors fenêtre. Les règles devront inclure prolongations, annulations, abandons et règlement des matchs nuls. Les marchés « draw no bet » ne deviennent pas exhaustifs par simple suppression du prix du nul. Le choix précis sport/opérateur reste à valider sur de vraies observations et un règlement public versionné ; NBA constitue seulement un candidat technique, pas une validation implicite des règles.

En l'absence de clôture effective, l'ancre est `commence_time` connue à J−1 et étiquetée `scheduled_start_proxy`. Toute modification observée à H−1 exclut la paire ; aucun réalignement rétrospectif à l'heure réelle ne doit introduire de lookahead. Le manifeste prospectif et l'ordonnanceur restent à ajouter avant déploiement. Tolérances proposées et codées : ±5 minutes pour chacune des deux cibles, requête entière incluse ; âge maximal du prix 120 secondes au début de la requête ; dates futures et timestamp marché manquant exclus. Ces paramètres devront être préenregistrés avant la première paire, sans les élargir après lecture des mouvements.

La documentation actuelle précise que `markets[].last_update` représente la dernière fois où le fournisseur a vu les cotes de ce marché ; lors d'une suspension/fermeture, il cesse d'avancer et le marché est retiré après environ 15 minutes [S1, « More info » de GET odds]. Un prix récent peut donc déjà être suspendu. L'adaptateur préparé garde `open_status=unknown`, refuse toute alerte validée et conserve les motifs. Ni un identifiant de règlement entré en ligne de commande ni une clé API ne lèvent ce blocage. Il faut obtenir un indicateur source explicite ou une confirmation fournisseur exploitable et documentée ; sinon rester au stade d'observation de prix indicatifs, en modifiant préalablement le protocole si l'utilisateur l'accepte.

## Livrables et vérifications

- [Guide reproductible](observatoire_v1/README.md), [collecteur et comparateur](observatoire_v1/pilot.py), [audit public](observatoire_v1/audit.py).
- [Tests](../tests/test_observatoire_v1.py) : seuils exacts ±20 %, non-alertes conservées, appariement, règles, décalages, suspension inconnue, prix périmés/futurs, rejet 1X2, absence de clé sans appel réseau, altération du stockage. Fixtures **artificielles unitaires explicitement nommées**, jamais présentées comme observations réelles.
- [Journal de validation](observatoire_v1/validation.log) : 9 tests exécutés, 9 réussis. Aucun test d'intégration live, aucune statistique issue de données de marché nouvellement collectées.
- Capture privée horodatée, corps exact, hash et journal chaîné sous verrou ; pas d'écrasement ni suppression. Les erreurs réseau après prévalidation sont journalisées sans URL secrète. Les doublons sont conservés et les comparaisons de captures identiques sont exclues.
- SHA-256 détecte des altérations accidentelles ; sans ancrage externe, ce n'est pas un stockage inviolable. Sauvegarde durable privée, contrôle des fichiers orphelins après panne, manifeste prospectif, historique des règles et limiteur de budget seront nécessaires pour un service autonome.

Aucun workflow de cotes n'est activé. GitHub Actions peut retarder les lancements ; une capture ratée doit rester manquante. Aucun abonnement, aucune clé demandée au nom de l'utilisateur. La collecte Manifold antérieure est distincte et n'est pas modifiée.

## Actions restantes, sans achat

1. Pérenniser le réseau décrit ci-dessus. Pour choisir TheOddsAPI, clarifier conservation longue durée, personne morale et champs live exacts, puis demander soi-même une clé gratuite distincte ; ne pas utiliser le collecteur `/v4/` de ce dépôt pour ce fournisseur.
2. Si le choix reste The Odds API, demander soi-même la clé **Starter gratuite**, puis la configurer sous `THE_ODDS_API_KEY` dans les paramètres sécurisés. Ne pas la transmettre dans le chat. Aucun secret n'est supposé ou enregistré par ce travail.
3. Confirmer un opérateur réellement accessible et un marché à deux issues avec règlement versionné ; clarifier l'indicateur d'ouverture. Effectuer une première capture en lecture seule, vérifier ses timestamps et son quota, puis deux captures aux cibles séparées de 23 heures. Tant que les critères manquent, conserver les exclusions et ne pas activer les alertes.
4. Avant automatisation : manifeste figé avant J−1, budget de crédits borné, stockage privé durable, programmateur et contrôle des retards. Le plafond théorique de 250 paires à deux crédits n'est pas un rendement de collecte garanti. Un budget initial conservateur peut réserver 100 des 500 crédits aux vérifications et erreurs ; aucun dépassement ni passage automatique au payant.

La valeur prédictive et un éventuel avantage économique net ne sont **pas évalués ici** : il manque les observations appariées valides, les résultats officiels et le traitement préenregistré des marges, frais, remboursements et biais de sélection. Aucune rentabilité ni information privée ne peut être inférée.

## Sources primaires

Pages consultées le 21 octobre 2026, empreintes et heures exactes dans les journaux d'accès.

- [S1 — The Odds API, documentation V4](https://the-odds-api.com/liveapi/guides/v4/) : GET odds, coûts, horodatages, suspensions, GET events/scores.
- [S2 — The Odds API, prix](https://the-odds-api.com/#pricing) : gratuit et offres mensuelles ; l'historique gratuit est explicitement exclu par S1/S3.
- [S3 — The Odds API, historique](https://the-odds-api.com/historical-odds-data/) : couverture et cadence des snapshots, accès payant.
- [S4 — The Odds API, intervalles](https://the-odds-api.com/sports-odds-data/update-intervals.html).
- [S5 — The Odds API, définition des marchés](https://the-odds-api.com/sports-odds-data/betting-markets.html).
- [S6 — The Odds API, conditions](https://the-odds-api.com/terms-and-conditions.html), version affichée 31 août 2026 : usages autorisés, conservation, restrictions de redistribution et absence de garantie.
- [S7 — TheOddsAPI, documentation](https://theoddsapi.com/docs/) (mise à jour affichée 20 octobre 2026), [tarifs](https://theoddsapi.com/pricing) (3 juillet 2026) et [OpenAPI](https://theoddsapi.com/openapi.json).
- [S8 — TheOddsAPI, conditions](https://theoddsapi.com/terms), version 29 avril 2026, et [présentation](https://theoddsapi.com/about).
- [S9 — TheOddsAPI, FAQ](https://theoddsapi.com/faq), version affichée 8 juin 2026 : quotas, UTC, ETag, cadence, absence de flux scores, distinction des domaines.
