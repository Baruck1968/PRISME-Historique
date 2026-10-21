# PRISME 3 — Observations à dates calendaires fixes

**Conclusion au 21 octobre 2026 : étude de faisabilité exécutée sur des données
réelles ; arrêt avant le test prédictif.** La grille indépendante des résolutions
est réalisable. Les sources examinées ne suffisent pas à vérifier ensemble la
négociabilité historique, l’issue encore inconnue, les deux prix et les événements
communs. Aucun effet, score prédictif, intervalle ou valeur p n’a été calculé.
Cela n’est ni une preuve d’absence de signal ni une impossibilité universelle.

Le protocole suivi est `experiments/PRISME3_PROTOCOL.md`, déjà présent sur `main`
avant cette exécution. Aucun fichier antérieur, y compris PRISME 1 et PRISME 2,
n’a été modifié. Les sources, scripts, réponses et résultats sont publiés séparément.

## 1. Grille et règle fixées avant le scan

Le plan local `experiments/prisme3/sampling_plan.json` fixe 78 lundis à **00:00 UTC**,
du **2 janvier 2023 au 24 juin 2024 inclus**. Il a été écrit avant le scan PRISME 3 ;
ce n’est pas un préenregistrement tiers. La fenêtre s’arrête avant les dates des
deux dumps (transactions du 4 juillet, marchés du 6 juillet 2024).

Tous les marchés `BINARY` du snapshot sont considérés, sans sélectionner YES/NO
ou un résultat final. Pour chacun : retenir **le premier lundi de la grille situé
au moins 48 h après sa création**. La date n’est pas remplacée si le marché est
ensuite exclu. Une observation principale par marché ; aucune optimisation sur
les issues, les prix ou un score. Les comptages hebdomadaires répétés servent
uniquement à l’audit de couverture, pas à créer des observations indépendantes.

À cette date, `resolutionTime > t` (ou absence de résolution dans un snapshot
explicitement non résolu) est un **proxy** de non-résolution. `closeTime > t` est
un **proxy** d’ouverture. Ces tests ne constituent pas des certifications de
l’état historique. La date t est indépendante des résolutions ; l’éligibilité
rétrospective utilise nécessairement les horodatages disponibles à t.

Deux compléments ont été précisés dans le plan après le scan des marchés mais
avant toute requête de prix : sonder les quatre premiers dossiers manuels et
toutes les questions NFL de cet échantillon ; vérifier ces deux jeux NFL dans un
calendrier externe. Ils n’affectent ni la grille, ni les seuils, ni la sélection
principale. Le sondage est un audit technique, pas une étude prédictive.

## 2. Sources réelles et intégrité

L’archive complète des marchés de PRISME 2 est réutilisée, sans nouveau
téléchargement : 91 427 545 octets ZIP, 130 091 identifiants uniques,
SHA-256 `63671168210deda1d96ba6c9e3d7fd1bb1bcd2a5a564c561f56ea12f5bceb8b7`.
L’empreinte et le CRC du contenu décompressé ont été vérifiés. Le parseur existant
est importé en lecture seule, sans exécuter l’expérience précédente.

L’archive des transactions d’environ 1 Go n’a pas été téléchargée intégralement.
Le préfixe réellement décodé et contrôlé par PRISME 2 confirme un schéma avec
`createdTime`, `probBefore` et `probAfter`, mais porte sur d’anciennes transactions
DPM : il n’établit pas la couverture de 2023–2024. Douze requêtes GET supplémentaires
à l’API publique ont été effectuées pour six marchés aux bornes calendaires.
Les réponses originales, URL, dates de collecte et SHA-256 sont conservés dans
`price_probe_responses.zip` et `price_probe.json`.

Les copies de documentation et de code source consultées sont dans `source_checks/`.
Le fichier `experiments/prisme3/source_manifest.json` fixe leurs empreintes et URL.
Le code source Manifold consulté est contemporain de cet audit : il montre que
la clôture est modifiable, mais ne reconstitue pas à lui seul le comportement
historique de chaque marché. Un chemin de source supposé pour un historique a
répondu 404 ; cela ne démontre pas qu’aucune autre interface d’historique n’existe.
Les dumps examinés, eux, ne contiennent pas le journal d’ouverture/fermeture et
d’édition nécessaire.

La documentation Manifold réserve les dumps gratuits à un usage personnel et non
commercial. Ce travail est un audit de recherche ; il ne confère pas de licence
commerciale. Les URL `token` enregistrées sont les liens publics des archives,
pas des secrets personnels. Aucun accès authentifié de négociation n’a été utilisé.

## 3. Tableau de flux

| Étape principale | Marchés |
|---|---:|
| Snapshot complet considéré | 130 091 |
| Non binaires exclus | 29 766 |
| Marchés binaires considérés | **100 325** |
| Sans date principale dans la grille | 814 |
| Avec une date principale | 99 511 |
| Résolution déjà enregistrée à t, selon le proxy | 28 422 |
| Clôture finale antérieure ou égale à t, selon le proxy | 1 696 |
| Apparemment ouverts et non résolus à t | **69 393** |
| Parmi eux : étiquette finale YES/NO dans le dump | 33 862 |
| Parmi eux : encore non résolus dans le dump | 32 324 |
| Parmi eux : autre résolution finale | 3 207 |
| Dossiers manuels déterministes | **20** |
| Dossiers avec ouverture ET issue inconnue certifiées à t | **0 vérifié** |
| Marchés sondés pour les deux prix | **6** |
| Paires de prix admissibles fraîches dans ce sondage | **0 sur 6** |
| Trajectoires entièrement certifiées pour la prédiction | **0 vérifié** |

Les trois dernières catégories d’issues finales décrivent la disponibilité des
étiquettes après l’observation ; elles ne servent pas à choisir t et ne sont pas
des covariables. Le taux de certification complète par cet audit est nul. Le taux
réel d’éligibilité des 69 393 candidats reste **inconnu**, pas démontré nul.

`calendar_flow.json` publie les décomptes pour chacun des 78 lundis. Par exemple,
5 726 marchés passent les proxies au 2 janvier 2023 et 32 480 au 24 juin 2024.
Ces effectifs répétés ne doivent pas être additionnés pour calculer un échantillon
indépendant. La liste principale complète est dans `calendar_candidates.zip`.

## 4. Ouverture historique et résultat encore inconnu

Les 20 identifiants de l’audit manuel sont les premiers par SHA-256 dans la liste
des candidats, sans utilisation de leur issue, prix ou volume. Les snapshots
complets et les notes sont publiés dans `manual_audit_markets.json` et
`manual_review.json`.

Leur état final ne renseigne pas les éventuelles clôtures, réouvertures,
résolutions puis révisions à t. Un `lastUpdatedTime` ou une description actuelle
ne reconstruit pas une version du marché à la date calendaire. Une transaction
antérieure à t prouve une exécution à cet instant antérieur ; elle ne prouve pas
à elle seule que le marché était négociable exactement à t.

Les cas examinés comprennent des critères subjectifs, des questions dont la
résolution dépend d’une information publique ou privée déjà existante, des
textes quasi vides et des descriptions enrichies après le début du marché.
L’audit ne prétend pas que leurs résultats étaient déjà connus : il n’a pas
établi l’inverse à t. Un type `BINARY` peut aussi avoir une résolution PROB ou
un critère quantitatif ; il ne suffit pas à garantir une issue objective YES/NO.

Une vérification externe limitée a été effectuée pour les deux questions NFL
présentes dans l’échantillon fixe, à partir du calendrier réel
[nflverse/nfldata](https://github.com/nflverse/nfldata/blob/master/data/games.csv).
Le [dictionnaire nflreadr](https://github.com/nflverse/nflreadr/blob/main/data-raw/dictionary_schedules.csv)
documente les heures en fuseau Eastern. Après conversion :

| Marché | t UTC | Début indiqué par le calendrier UTC | Écart |
|---|---|---|---:|
| Texans–Steelers | 18 septembre 2023, 00:00 | 1 octobre 2023, 17:00 | 329 h |
| Patriots–Dolphins | 18 septembre 2023, 00:00 | 18 septembre 2023, 00:20 | 20 min |

Cela soutient la plausibilité d’une observation précédant le match, et identifie
deux événements. Ce calendrier historique courant n’est pas une version publiée
avant t ; il ne certifie ni l’état de la plateforme ni l’absence de toute
information exceptionnelle. Aucun score ni cote NFL n’est utilisé dans la
sélection ou le calcul : seules les dates et identités de match sont examinées.
Les autres dossiers n’ont pas fait l’objet d’un audit exhaustif de presse,
annonces ou horaires externes. Le contrôle d’inconnaissance reste incomplet.

## 5. Reconstruction technique des prix : résultat du sondage

Les requêtes sont bornées par `beforeTime=t+1`, respectivement `t−24h+1`, en
millisecondes, avec au plus 1 000 enregistrements. Le script sélectionne une
probabilité `probAfter` d’ordre initiateur sans `limitProb`, exclut les apports
initiaux, remboursements, montants nuls et remplissages non datés ou postérieurs
à la borne. Il rejette les prix simultanés contradictoires et les pages dont la
limite empêche une conclusion. Aucun prix final du marché résolu n’est utilisé.

Sur les **12 bornes** réellement sondées :

- **9** derniers prix admissibles ont plus de 24 h ;
- **2** bornes ne contiennent aucun ordre admissible (même marché NFL) ;
- **1** borne a un prix admissible frais ;
- **aucun des six marchés** n’a deux bornes fraîches.

Un prix ancien ne doit pas devenir artificiellement une variation nulle. Une
réponse sans transaction ne signifie ni marché fermé ni perte certaine dans le
dump : elle peut aussi correspondre à une absence d’activité. Le sondage contient
137 apparitions d’enregistrements, avec répétitions entre bornes ; 92 ont un
`updatedTime` postérieur à leur borne. Une mise à jour tardive ne prouve pas que
le prix a changé, mais interdit de supposer que tous les champs courants étaient
immuables à t.

Même une paire fraîche ne suffirait pas à certifier le prix exact : les événements
de liquidité, remplissages différés et changements DPM/CPMM doivent être reconstruits.
188 candidats possèdent un `cfmmConversionTime` ; son absence ne constitue pas
une preuve générale d’absence de transformation. Le mécanisme du snapshot ne
peut pas être appliqué sans contrôle à toute sa trajectoire historique.

La couverture effective du dump complet, ses jonctions et ses trous ne sont pas
établis. Les derniers lundis retenus précèdent sa date annoncée, mais cela ne
certifie pas la complétude. Aucune extrapolation du taux de succès des six sondages
aux 69 393 candidats n’est faite. Les seuils de 24 h n’ont pas été relâchés.

## 6. Événements communs : liens possibles, partition non validée

Le contrôle de titres normalisés NFKC/casse/espaces repère **544 groupes** de titres
répétés, concernant **1 448 marchés**. `event_grouping_audit.json` publie leurs
membres. Ce sont des liens candidats, pas une partition certifiée : un même
événement peut avoir plusieurs formulations, et un titre générique peut être
réutilisé pour des événements différents. Les appartenances à des thèmes,
présentes sur 64 014 candidats, sont trop larges pour servir de clés d’événement.

L’examen de titres identifie sept questions liées à la même élection présidentielle
américaine de 2024, malgré des candidats politiques différents ; elles doivent
être traitées comme dépendantes. Ces exemples figurent dans
`event_link_examples.json`. Les deux événements NFL sont identifiés dans
`external_schedule_check.json`. Ces correspondances partielles ne couvrent pas
le corpus ni l’ensemble des marchés reliés indirectement.

Aucun découpage train/test n’a été créé. Un simple découpage par marché ou par date
laisserait des événements communs traverser les deux périodes. Il faudrait une
partition auditée et une règle de traitement des groupes chevauchant la frontière,
fixées avant tout score.

## 7. Décision et limites

Le changement de dates résout la dépendance mécanique du choix de t à la résolution.
Il ne résout pas l’absence d’historique d’état et de connaissance publique. Les
conditions cumulatives du protocole ne sont pas établies ; la branche prédictive
est donc arrêtée, sans ajustement, Brier, log-loss, contraste ou valeur p.

Les distributions de probabilités et les effectifs de momentum par strates de
0,05 ne sont pas mesurés sur un corpus certifié. `conclusion.json` les indique
explicitement comme non calculés ; aucune cellule manquante n’est présentée
comme un effectif nul. Les prix du sondage servent seulement à l’audit technique.
L’archive elle-même est un snapshot survivant, pas une preuve d’exhaustivité des
marchés ayant existé puis été supprimés. Les étiquettes manquantes à sa date
créent aussi un risque de censure si l’on sélectionnait ensuite seulement YES/NO.

## 8. Sources et étapes concrètes pour poursuivre

- **Manifold, export historique versionné** : la documentation officielle
  [Data](https://github.com/manifoldmarkets/manifold/blob/main/docs/docs/data.md),
  conservée ici, décrit les dumps et un contact de données. Il faut demander ou
  trouver explicitement les journaux de création/édition, clôture/réouverture,
  résolution/révision, liquidité et conversions. L’offre publiée ne garantit pas
  qu’un tel journal complet soit disponible : cette capacité reste à confirmer.
- **Sous-cohorte d’événements externes vérifiables** : les calendriers nflverse
  et leur dictionnaire déjà contrôlés donnent un point de départ pour les matchs.
  Ils doivent être complétés par des versions d’horaires et publications de résultats
  datées, puis par la preuve de négociabilité Manifold et une couverture de prix
  suffisante. Une cohorte sportive restreinte serait une nouvelle règle à fixer
  avant ses scores, pas une réparation silencieuse de la cohorte actuelle.
- **Collecte prospective en lecture seule** : la
  [documentation API Manifold](https://github.com/manifoldmarkets/manifold/blob/main/docs/docs/api.md)
  décrit marchés et transactions. Des captures régulières horodatées et hachées
  de l’état permettraient de documenter les prochaines dates calendaires. Elles
  ne reconstruiraient pas rétroactivement 2023–2024 et ne remplaceraient pas l’audit
  des événements et de l’information publique.

Le téléchargement intégral des transactions n’est pas nécessaire avant de lever
ces obstacles indépendants des prix. Aucun secret ou permission de négociation
n’est requis pour les contrôles réalisés.

## 9. Reproduire et vérifier

Python 3.12+, bibliothèque standard. Depuis la racine du dépôt :

```bash
python experiments/prisme3/fetch_sources.py
python experiments/prisme3/calendar_audit.py
python experiments/prisme3/price_probe.py --offline
python experiments/prisme3/schedule_crosscheck.py
python -m unittest discover -s tests -p test_prisme3.py -v
```

`fetch_sources.py` vérifie les sources déjà présentes et ne télécharge que celles
qui manquent, dont l’archive des marchés de 91 Mo si nécessaire. Les sources à URL
mutable ne sont acceptées que si leur SHA-256 correspond au contenu figé.
Aucun fichier existant n’est écrasé par le téléchargement. Les réponses API déjà
publiées sont rejouées sans réseau ; une nouvelle collecte doit utiliser un
nouveau cache, pas écraser celui-ci.

Les six tests ont réussi, sans aucun saut, dont un **rejeu intégral** du scan dans
un répertoire temporaire. Ils contrôlent le décompte, l’unicité des observations,
la grille, l’indépendance du choix de t vis-à-vis des résultats, la sélection
manuelle, les bornes d’exécution des prix et le caractère partiel des événements.
Ils vérifient le comportement des garde-fous, pas la réussite d’un test prédictif
qui n’a pas eu lieu. `validation.json` conserve le résultat réel ;
`artifact_manifest.json` contient les empreintes des artefacts publiés et
`preservation_check.json` les contrôles des fichiers précédents.

Toutes les opérations sont en lecture seule vis-à-vis de Manifold : aucun pari,
ordre, transaction, mouvement de fonds ni contournement de restriction.
