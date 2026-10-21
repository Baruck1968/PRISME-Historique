# PRISME 2 — Faisabilité historique et arrêt avant test prédictif

Exécution réelle le 21 octobre 2026, suivant `experiments/PRISME2_PROTOCOL.md`.
**Conclusion : non concluant. Corpus volumineux disponible, mais test prédictif
non exécuté faute de provenance temporelle suffisante. Aucune valeur p, aucun
Brier, aucune log-loss ni amélioration de modèle n'ont été calculés.**

## Données réellement vérifiées

- Archive officielle des marchés du 6 juillet 2024 : **91 427 545 octets ZIP**,
  463 420 663 octets décompressés. Lecture complète du JSON, contrôle MD5 fourni
  par le serveur et CRC ZIP réussis. SHA-256 :
  `63671168210deda1d96ba6c9e3d7fd1bb1bcd2a5a564c561f56ea12f5bceb8b7`.
- **130 091 identifiants uniques**, dont **100 325 marchés binaires**.
  Créations comprises entre décembre 2021 et juillet 2024.
- Archive des transactions du 4 juillet 2024 : **1 014 074 842 octets**, accessible.
  Une requête HTTP Range a téléchargé exactement **65 536 octets** du ZIP,
  dont dix enregistrements réellement décodés contiennent tous `createdTime`
  (millisecondes depuis l’époque Unix) et `probAfter` (probabilité entre 0 et 1).
  C’est un contrôle de schéma sur un préfixe, pas un échantillon représentatif.
  Le fichier complet n’a pas été téléchargé et son intégrité complète n’est pas
  revendiquée. Le préfixe a une empreinte conservée dans `trade_probe.json`.
- Sources : liens publics de la documentation officielle déjà conservée dans
  `results/source-check/data.md`. Métadonnées HTTP, tailles, générations des objets
  et URL sont dans `source_metadata.json`. Les paramètres `token` de ces URL sont
  les liens publics publiés par Manifold, pas des identifiants personnels.
- Les dumps sont annoncés pour usage personnel et non commercial. Cet audit de
  recherche ne constitue pas une autorisation de réutilisation commerciale.
  Le texte complet des conditions externes n’a pas fait l’objet d’un audit juridique.

## Règle de collecte et décompte

La règle a été écrite avant le téléchargement complet des marchés dans
`experiments/prisme2/sampling_plan.json` : examiner **tous** les marchés binaires
avec résolution YES/NO strictement antérieure au 4 juillet 2024 à 00:00 UTC.
Cette borne conservatrice évite d’utiliser les marchés résolus après la date de
l’archive des transactions ; elle ne prouve pas que tous les historiques antérieurs
sont complets. Aucun filtre ne dépend d’une performance ou du signe de la variation.
Le plan local n’est pas un préenregistrement tiers horodaté. Le protocole initial
était déjà présent sur GitHub avant cette collecte et n’a pas été modifié.

| Contrôle | Effectif |
|---|---:|
| Marchés archivés | 130 091 |
| Exclus : non binaires | 29 766 |
| Binaires sans résolution admissible YES/NO | 40 306 |
| Résolution hors borne commune ou horodatage absent | 146 |
| Population candidate restante | **59 873** |
| Avec `closeTime` | 59 873 |
| `closeTime == resolutionTime` | **30 767** |
| `closeTime < resolutionTime` | 28 953 |
| `closeTime > resolutionTime` | 153 |
| Échéances ex ante vérifiées par cet audit | **0** |
| Couverture vérifiée pour l’analyse prédictive | **0 %** |

Le corpus candidat représente près de 300 fois les 200 marchés de PRISME 1.
Les 59 873 candidats comprennent 26 712 YES et 33 161 NO ; ce sont des comptages
d’archive, pas un résultat sur la valeur prédictive du momentum.

## Pourquoi le test sans fuite n’est pas établi

L’inspection exhaustive des 89 noms de champs du snapshot ne révèle pas de date
initiale de clôture accompagnée de sa publication horodatée, ni d’historique
complet des changements de critères. Parmi les champs contenant close/deadline/
history/initial/original/event/edit, on trouve uniquement `closeTime`,
`closeEmailsSent` et `initialProbability`. Ce dernier est une probabilité initiale,
pas une échéance initiale. `createdTime` ne date pas séparément les versions des
textes et `lastUpdatedTime` ne reconstitue pas l’historique des éditions.

La documentation API conservée dans `results/source-check/api.md` décrit
`closeTime` comme le minimum entre la date choisie et `resolutionTime` et expose
une opération pour changer la clôture. L’égalité constatée dans 30 767 cas est
compatible avec une clôture à la résolution ; **elle ne prouve pas à elle seule
que tous ces marchés ont subi une fuite**. Les 153 dates de clôture postérieures
à la résolution montrent aussi qu’il ne faut pas supposer cette règle parfaitement
respectée par tous les anciens snapshots. Une clôture antérieure à la résolution
ne prouve pas davantage qu’elle était annoncée avant l’instant d’observation.

L’échantillon manuel était fixé aux **12 premiers identifiants par SHA-256** de
la population candidate. Leurs enregistrements complets et notes figurent dans
`manual_audit_markets.json` et `manual_review.json`. Certains textes annoncent
un horaire de match ou de vol ; d’autres ont un événement d’arrêt dépendant de
l’issue, une description vide, ou un texte enrichi après le début du marché.
Aucun de ces douze snapshots n’atteste une version du critère publiée avant t.
Les horaires historiques externes et le moment de connaissance publique de l’issue
n’ont pas été vérifiés : cette condition reste **non établie**, pas « satisfaite ».

Autres prérequis non résolus :

- `id` identifie un marché, pas un événement commun. Une table d’événements auditée
  est nécessaire pour empêcher qu’un même événement apparaisse en apprentissage
  et en test et pour regrouper les intervalles d’incertitude.
- La liquidité, les compteurs de participants et le texte du snapshot sont mesurés
  après l’instant d’observation. Les utiliser comme covariables serait une fuite
  potentielle ; il faudrait reconstruire leur état historique.
- Les dix anciennes transactions du préfixe ont des champs DPM ; le snapshot des
  59 873 candidats indique CPMM. L’archive possède `cfmmConversionTime` sur
  1 680 marchés au total. Le régime historique ne doit pas être déduit du seul
  mécanisme final ; conversions et remplissages différés doivent être audités.
- Les couvertures des deux archives diffèrent. Nous n’avons pas démontré leur
  jonction exhaustive ni la fraîcheur des deux prix par marché.

**Zéro échéance vérifiée signifie zéro observation admise par les contrôles de cet
audit, pas qu’aucun marché exploitable n’existe dans Manifold.** Une sous-cohorte
avec horaires historiques indépendamment attestés pourrait permettre la suite.

## Analyse exécutée et analyses non exécutées

Le script a exécuté l’inventaire complet, le décompte d’admissibilité d’archive,
la recherche des champs de provenance, le classement de l’échantillon manuel
et les contrôles d’intégrité. Le fichier ZIP `candidate_deadline_audit.zip`
contient la liste exhaustive des 59 873 candidats, avec leurs dates de snapshot
et le statut `not_verified`. Il ne transforme aucune clôture en échéance ex ante.

Le contrôle de provenance a arrêté la branche prédictive **avant** extraction de
p(t), calcul de delta, ajustement des modèles ou réservation d’un test final.
Les 20 strates de probabilité ne sont donc pas mesurées : leurs effectifs sont
**indisponibles**, et non des zéros observés. Aucun diagnostic de recouvrement,
contraste apparié, permutation ou effet additionnel n’est rapporté.
Il n’y a pas non plus d’étude descriptive de momentum calculée en substituant
`resolutionTime` à une échéance fiable : cela répéterait la limite de PRISME 1.

L’audit n’implémente pas de modèles tant que ces conditions ne sont pas satisfaites.
Aucun résultat statistique n’a été fabriqué. Aucun pari, ordre ni transaction
financière n’a été effectué ; seules des lectures publiques ont été utilisées.

## Reproduction

Python 3.12+, bibliothèque standard uniquement. Depuis la racine du dépôt :

```bash
python experiments/prisme2/audit_archives.py
python experiments/prisme2/probe_trade_archive.py
python -m unittest discover -s tests -p test_prisme2.py -v
```

Le premier script télécharge l’archive si absente et vérifie son empreinte figée
par `experiments/prisme2/source_lock.json`. Si le serveur remplace l’objet, le
script échoue plutôt que d’accepter silencieusement une nouvelle source. L’archive
complète reste localement dans `data/prisme2/markets.zip` ; elle n’est pas envoyée
sur GitHub. Ses références, génération et empreinte sont publiées. Ne pas supprimer
ni écraser un téléchargement partiel : fournir un autre chemin avec `--archive`.

Pour rejouer l’audit complet sans réseau après téléchargement :

```bash
python experiments/prisme2/audit_archives.py --offline
```

Les quatre tests s’appuient exclusivement sur les enregistrements réels publiés :
cohérence des effectifs, rejet d’un JSON réel tronqué, intégrité du préfixe et
horodatages présents, et contrôle des 59 873 statuts de provenance avec sélection
manuelle conforme à la règle. Ils ont tous réussi. Ils ne démontrent pas l’absence
de fuite dans un futur modèle ; aucun modèle n’a été exécuté.
Les empreintes des artefacts figurent dans `artifact_manifest.json`.

## Conditions concrètes pour poursuivre

Il faut une source historique versionnée des critères/échéances (ou des calendriers
externes attestés avant t pour une sous-cohorte définie sans consulter les scores),
une vérification manuelle du moment de connaissance publique de l’issue et une
clé d’événement commune auditée. Ensuite seulement : téléchargement et jonction
complets des transactions, vérification des deux prix et de leur fraîcheur,
reconstruction des covariables, séparation chronologique par événement, puis
comparaison Brier/log-loss avec incertitude regroupée.

Aucun réglage des seuils et aucune augmentation de volume ne répare à lui seul
l’absence de provenance temporelle. Le constat actuel porte sur les sources
vérifiées, pas sur une impossibilité universelle de conduire PRISME 2.
