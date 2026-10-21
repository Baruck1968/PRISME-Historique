# Première tentative réelle — accès authentifié bloqué

21 octobre 2026, UTC. **Aucune capture de cotes réussie.** Aucun résultat de marché inventé, aucune alerte validée ou indicative, aucune collecte permanente programmée. Ce rapport complète le rapport de faisabilité sans le modifier.

## Opération effectivement exécutée

Le collecteur `research/observatoire_v1/pilot.py` du commit `e78c717` a été utilisé **sans modification** :

```sh
python research/observatoire_v1/pilot.py capture --sport basketball_nba --bookmaker fanduel
python research/observatoire_v1/pilot.py verify research/observatoire_v1/private
```

Choix technique borné : un sport, un bookmaker, `h2h`, format décimal, normalement un crédit par réponse non vide. NBA est un candidat à deux issues ; ce choix ne certifie pas les règles de FanDuel, les prolongations, annulations ou l'ouverture. Aucun marché n'a été validé faute de réponse utilisable. Le collecteur récupère le tableau du sport sélectionné ; une sélection locale de quelques événements futurs était prévue après contrôle, mais n'a pas pu être réalisée. Aucun autre bookmaker ni sport n'a été interrogé pour contourner l'échec.

Tentative de cotes : début `2026-10-21T15:04:17.593528+00:00` (heure exacte faisant foi dans `capture_attempts.json`), fin et empreinte dans ce même fichier. Le collecteur a enregistré un échec `HTTPError`, sans enregistrer ni afficher l'URL avec clé. Le journal privé contient une entrée, vérifiée par le collecteur. La capture échouée est conservée dans le dossier ignoré `private/`. Les métadonnées expurgées et son empreinte SHA-256 sont publiées dans [capture_attempts.json](capture_attempts.json) ; aucune donnée brute de cotes n'est publiée.

Un contrôle complémentaire sur le catalogue gratuit `/v4/sports/` a renvoyé `401`, code fournisseur **`INVALID_KEY`**. Le contrôle initial puis le contrôle reproductible consigné dans [access_probe.json](access_probe.json) ont donné le même résultat. Aucun retry automatique. Le second contrôle a eu lieu de `15:04:54.000341` à `15:04:54.325414 UTC`. Le script [probe_access.py](probe_access.py) n'affiche que des champs explicitement autorisés, refuse les redirections et ne publie jamais le corps ni l'URL authentifiée.

## Diagnostic de configuration

Le statut cloud indique : variable `THE_ODDS_API_KEY` présente, liaison secrète déclarée `ready`, observations courantes, réseau appliqué. L'API est joignable et répond : ce n'est pas un refus réseau.

La liaison secrète existante autorise **`the-odds-api.com` uniquement**. L'hôte effectivement appelé par le collecteur est **`api.the-odds-api.com`**. Ces noms sont distincts ; l'autorisation du premier ne démontre pas l'injection de la clé vers le second. Le brouillon et le runtime confirment cette différence. Le secret n'a été ni lu, ni affiché, ni copié. La réponse `INVALID_KEY` ne permet pas à elle seule de distinguer une clé fournisseur incorrecte d'une injection absente ; cette configuration est le premier point à corriger, sans présumer que la clé réelle est invalide.

**Action utilisateur précise** : dans les paramètres sécurisés de cet environnement, éditer la liaison existante `THE_ODDS_API_KEY` et ajouter **`api.the-odds-api.com`** à ses destinations HTTPS autorisées, en conservant le domaine déjà déclaré. Garder le même nom de variable et la valeur secrète existante ; ne pas créer une seconde variable ni transmettre la valeur dans le chat. Enregistrer/appliquer la modification ; publier l'environnement pour la pérenniser. Ensuite vérifier d'abord le catalogue gratuit, puis relancer une seule capture bornée. Si `INVALID_KEY` subsiste après confirmation de l'injection vers le bon domaine, vérifier la clé gratuite dans l'espace du fournisseur et remplacer sa valeur uniquement dans les paramètres sécurisés. Aucun abonnement payant n'est nécessaire pour ce contrôle.

La configuration d'une liaison existante nécessite son édition dans l'interface ; aucun remplacement de secret ni tentative de récupération de sa valeur n'a été entrepris. Les domaines réseau sont déjà autorisés : ajouter une règle réseau seule ne corrige pas la destination d'injection du secret.

## Bilan des contrôles demandés

| Contrôle | Résultat observé |
|---|---|
| Capture réelle réussie | Non : tentative réseau authentifiée échouée |
| Événements futurs et deux issues | Aucun événement observable ; impossibilité de sélectionner/valider un échantillon |
| Identifiants événement/marché | Aucun reçu ; `h2h` est seulement le marché demandé |
| Opérateurs effectivement présents | Inconnu ; `fanduel` est demandé, sa présence n'est pas démontrée |
| Horodatages des cotes / fraîcheur | Indisponibles ; ne pas remplacer par l'heure locale de requête |
| Règles / marché ouvert | Non vérifiés ; aucune alerte autorisée |
| Crédits consommés / restant | Non mesurables : pas d'en-têtes de quota reçus sur les contrôles 401 ; ne pas annoncer zéro crédit consommé sans compteur fournisseur |
| Stockage vérifié | Une entrée d'échec privée, chaîne et hash vérifiés ; empreinte publique sans corps fournisseur |
| Publication sensible | Ni clé, ni URL authentifiée, ni données brutes fournisseur |
| Programmation permanente | Aucune ; workflow Manifold antérieur inchangé |

Il n'existe ni paire J−1/H−1, ni variation de ±20 % calculée, ni conclusion prédictive ou économique. Après déblocage, les observations pourront rester indicatives séparément tant que les règles et l'ouverture ne sont pas prouvées. Les expériences précédentes et le collecteur `e78c717` sont conservés intégralement.
