# PRISME-Historique

Première expérience exploratoire : une hausse récente de probabilité contient-elle
une information sur l'issue d'un marché résolu, à probabilité terminale comparable ?

**État au 21 octobre 2026 : pilote exécuté sur 200 marchés réels. Après exclusions,
25 sont exploitables, sans recouvrement hausse/baisse à probabilité comparable.
Aucun effet ni valeur p ne peut être estimé selon le protocole retenu.**

## Sources et accès vérifiés

La [documentation officielle Manifold](https://github.com/manifoldmarkets/manifold/blob/main/docs/docs/data.md)
annonce des archives publiques depuis décembre 2021 : marchés au 6 juillet 2024
(87 MB), transactions au 4 juillet 2024 (967 MB). Ces deux dates diffèrent : une
étude fondée sur ces fichiers devra exclure les périodes sans couverture commune.
La documentation précise un usage personnel/non commercial ; vérifier les termes
avant tout autre usage. Ce pilote vise la recherche et utilise des requêtes GET
sur l'API publique, pour éviter le téléchargement initial de près de 1 Go.
L'archive complète et le pilote API ne constituent pas le même échantillon.

La [documentation API](https://github.com/manifoldmarkets/manifold/blob/main/docs/docs/api.md)
décrit `createdTime`, `probBefore`, `probAfter`, `resolution`, `resolutionTime`, et
la pagination des transactions. Les requêtes réelles ont confirmé des transactions contenant `createdTime` et
`probAfter` (5 enregistrements dans le contrôle d'accès).

Les vérifications réelles ont donné :

| Vérification | Résultat |
|---|---|
| Documents officiels sur GitHub | HTTP 200 |
| Archive marchés, requête HEAD | HTTP 200 ; contenu ZIP non téléchargé |
| Archive transactions, requête HEAD | HTTP 200 ; contenu ZIP non téléchargé |
| API des marchés résolus et historique, GET | HTTP 200 |
| Exécution du pilote | Voir résultats ci-dessous |

Les preuves horodatées, copies des documents et empreintes SHA-256 sont conservées
dans `results/source-check/`. Le rapport d'exécution est dans
`results/pilot/report.json`. Les exemples inclus dans la documentation API
n'ont pas été utilisés comme observations scientifiques.

## Reproduire

Python 3.12 ou supérieur ; bibliothèque standard uniquement, sans clé API.
Depuis `/workspace/PRISME-Historique` :

```bash
python experiments/check_sources.py
python experiments/momentum.py --limit 200 --output results/pilot
```

L'accès réseau doit autoriser `api.manifold.markets` et, pour contrôler les
archives, `firebasestorage.googleapis.com`. Ces ajouts ont été enregistrés dans le
brouillon de configuration cloud, en conservant les domaines prédéfinis existants.
Les accès fonctionnent maintenant dans cette instance après un refus initial
HTTP 403. Le brouillon reste à revoir/enregistrer et publier pour les futures
tâches. Aucun secret n'est nécessaire.

Le cache exact du pilote est conservé dans `data/manifold-pilot-cache.zip` ; son
empreinte figure dans `data/snapshot.json`. Pour rejouer **les mêmes réponses**,
sans réseau, dans un nouveau clone :

```bash
python -m zipfile -e data/manifold-pilot-cache.zip data/cache
python experiments/momentum.py --limit 200 --offline --output results/replay
```

Les réponses brutes sont mises en cache dans `data/cache/`, avec URL, date de
collecte et SHA-256 vérifié à la relecture. Conserver ce cache pour reproduire
l'échantillon : l'API est mutable. `report.json` décrit les paramètres, exclusions,
provenances et l'empreinte du script ; `observations.json` contient les variables
par marché. Toujours vérifier le statut et la date du rapport : un ancien fichier
d'observations ne constitue pas un résultat d'une exécution échouée. Une erreur
réseau ou de schéma arrête le calcul ; elle n'est pas traitée comme une exclusion
scientifique. Aucun appel d'écriture, pari, ordre ou transaction n'est effectué.

## Protocole du pilote

1. Prendre les 200 marchés binaires résolus les plus récemment **créés**, via
   `search-markets`, tri `newest`. Il s'agit d'un échantillon de convenance,
   sans prétention d'exhaustivité. Conserver seulement les résolutions YES/NO.
2. Une observation par marché. Fixer `t = resolutionTime - 24 h`, puis `t0 = t - 24 h`.
   La « probabilité finale » désigne ici la probabilité à la fin de cette fenêtre,
   **pas** la probabilité terminale 0/1 de règlement. Ne pas utiliser le champ
   courant `probability` d'un marché résolu comme prédicteur.
3. À chaque borne, retenir `probAfter` du dernier ordre initiateur sans
   `limitProb`, exécuté au plus tard à la borne. Exclure les enregistrements
   d’ordres limites : leurs exécutions différées peuvent mettre à jour les champs
   après leur création. Utiliser le maximum des horodatages de création et de
   remplissage pour les ordres retenus. Rejeter les historiques absents, les prix
   vieux de plus de 24 h et les horodatages simultanés aux prix contradictoires.
   Exclure les marchés créés après t0. Conserver les heures effectives des prix.
4. Définir `delta = p(t) - p(t0)`. Hausse : delta ≥ 0,02 ; baisse : delta ≤ −0,02.
   Les variations plus faibles sont conservées dans les observations mais ne
   participent pas au contraste principal. Il s'agit de points de probabilité,
   et non de pourcentages relatifs.
5. Comparer hausses et baisses à l'intérieur de tranches fixes de 5 points de
   probabilité p(t). Seules les tranches contenant les deux groupes contribuent.
   Pour réduire l'écart résiduel de probabilité, comparer les moyennes de
   `issue - p(t)`. Pondérer chaque différence par `n_hausse*n_baisse/n_tranche`.
   Un contraste positif est compatible avec un surplus d'information associé
   à la hausse ; il ne le prouve pas.
6. Calculer une valeur p bilatérale exploratoire par 10 000 permutations des
   étiquettes hausse/baisse **dans chaque tranche**, effectifs préservés,
   graine 20261021, correction `(extrêmes+1)/(permutations+1)`.
   Sans tranche avec recouvrement, aucun test n'est calculé.

## Résultats du pilote

| Sélection | Nombre |
|---|---:|
| Marchés résolus collectés | 200 |
| Trop jeunes : moins de 48 h avant résolution | 80 |
| Résolution autre que YES/NO ou type non admissible | 15 |
| Au moins un prix vieux de plus de 24 h | 61 |
| Au moins un instant sans ordre initiateur admissible | 19 |
| Marchés avec deux prix admissibles | 25 |
| Hausse d'au moins 2 points | 7 |
| Baisse d'au moins 2 points | 6 |
| Variation inférieure à 2 points | 12 |
| Marchés dans une tranche contenant hausse ET baisse | **0** |

**Le contraste conditionnel n'est pas estimable ; aucune permutation n'a été
exécutée et aucune valeur p n'est rapportée.** Ce résultat ne démontre ni un effet
ni l'absence d'effet. Les exclusions sont mutuellement exclusives selon leur
ordre de contrôle : un marché peut avoir d'autres défauts non comptabilisés.

L'audit des données a motivé l'exclusion des ordres limites avant le rapport final.
Le protocole a donc subi une correction de qualité après la première collecte :
il ne constitue pas un préenregistrement externe. Aucun seuil n'a été ajusté pour
obtenir un effet ou une significativité. Le test d’intégration a extrait le cache archivé dans un répertoire temporaire
et reproduit exactement observations, exclusions et résultat, sans réseau.
Les bornes temporelles et le décompte des exclusions ont également été contrôlés.
Une vérification a été exécutée et réussie :

```bash
python -m unittest discover -s tests -v
```

La branche statistique avec permutations n’a pas été exercée par ces données,
puisqu’elles ne présentent aucun recouvrement. Elle ne doit pas être présentée
comme validée empiriquement.

## Limites et suite scientifique

- La date de résolution est connue rétrospectivement et peut dépendre de
  l'événement. Cette expérience est descriptive, pas une stratégie prédictive
  déployable ; même 24 h avant résolution, l'issue peut déjà être publique.
  La documentation indique aussi que `closeTime` peut être tronqué à la
  résolution : ce champ n'offre pas une échéance ex ante fiable à lui seul.
- Le tri par création favorise les marchés récents rapidement résolus.
  Les marchés non résolus, annulés et les historiques incomplets sont exclus :
  risques de sélection et de survivance. Le seuil de fraîcheur change aussi la
  population étudiée.
- Le prix d'une dernière transaction est une approximation de la probabilité
  affichée ; les changements de liquidité et autres événements non transactionnels
  peuvent manquer. Une absence de transactions ne signifie pas absence d'information.
- Le conditionnement par tranches reste approximatif. La correction `issue-p`
  suppose implicitement une calibration locale satisfaisante. L'échangeabilité
  nécessaire à la permutation n'est pas établie ; la valeur p n'est pas une
  preuve confirmatoire d'information additionnelle conditionnelle.
- Les marchés peuvent partager sujet, issue, créateur ou participants. Le test
  actuel ignore ces dépendances et peut sous-estimer l'incertitude. Les probabilités
  extrêmes, le petit effectif et le faible recouvrement peuvent rendre le test peu
  informatif. Aucune interprétation causale, financière ou généralisable n'est permise.
- Pour la suite : auditer les observations, étendre la cohorte selon une règle fixée à l’avance,
  publier les effectifs par tranche et contrôler la couverture historique. Une confirmation devra
  utiliser une cohorte temporelle séparée, des échéances définies ex ante,
  un modèle flexible de p(t), puis l'ajout de delta, avec évaluation hors
  échantillon (Brier/log-loss) et incertitude regroupée par événement. Les essais
  de fenêtres et de seuils supplémentaires seront des analyses de sensibilité
  explicitement distinguées du protocole principal.
