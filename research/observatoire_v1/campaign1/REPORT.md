# Campagne prospective 1 — inscrite et archivée, activation bloquée

21 octobre 2026. **Nouvelle cohorte inscrite avant J−1 ; découverte réelle et manifeste chiffrés, sauvegardés et retéléchargés. Aucun relevé cible ni déclencheur actif.** L'utilisateur a confirmé : « Aucun hôte disponible : documenter le blocage ». La campagne n'est donc pas présentée comme opérationnelle aux échéances. Le travail ne déclenche ni pari, achat, abonnement ou surveillance permanente.

## Historique initial conservé

Le manifeste initial du 21 octobre à `15:17:28.264762 UTC` est vérifié sans modification : SHA-256 `627d076a2a2f161942254d83f83751416e41ed18e54869d621f920838739031d`. Ses échéances et son archive initiale sont conservées.

À l'examen effectué le 21 octobre vers 16:08–16:11 UTC, **aucune des six échéances des trois candidats initialement inscrits n'était encore dépassée**. Il ne faut pas inventer une absence à une date future. En revanche, onze marchés tarifés avaient déjà dépassé J−1 lors de la découverte initiale et étaient exclus de l'inscription initiale : leurs onze J−1 sont consignés comme absents dans le nouvel état privé, sans prix reconstruit et avec `enrolled=false`. Les autres cibles restent signalées « en attente, non programmées ». L'absence de programmation ne devient pas une observation manquante avant la fermeture de sa fenêtre.

La capture de découverte initiale de 15:14 UTC n'a remplacé et ne remplacera aucun J−1. Le nouvel état contient une copie des statuts historiques, pas une réécriture du manifeste initial. Après chaque fermeture de fenêtre non observée, l'agrégateur classe la paire incomplète ; ne pas chercher de prix rétrospectif.

## Nouvelle découverte et inscription

Un contrôle **gratuit** `/v4/sports/` a confirmé HTTP 200 : 1 crédit utilisé sur le compte, 499 restants, coût du contrôle 0. Une seule nouvelle capture NBA/FanDuel `h2h` a ensuite été exécutée avec le collecteur existant. Elle a coûté **1 crédit**, portant le compteur fournisseur à 2 utilisés, **498 restants**. Elle constitue la découverte de cette campagne, pas un relevé cible.

Le [manifeste expurgé](manifest_redacted.json) ancre l'inscription à **2026-10-21T16:11:16.693034 UTC** et l'empreinte du nouvel état privé :

`92aa4f3d46bfec27bfc1ece46497cb8c3add29d9f76b91f70b8067df38148d98`

Trois événements disponibles avec deux issues correspondant aux participants, FanDuel et `h2h`, frais à la découverte et dont J−1 est futur, ont été sélectionnés dans l'ordre initial début/id. Leurs identifiants, les noms exacts des deux issues, le début initial, les deux cibles UTC et le corps de découverte sont privés, à l'intérieur de l'archive chiffrée. La nouvelle inscription porte sur les **mêmes trois événements encore admissibles que les candidats antérieurs** : ce n'est pas un élargissement indépendant de l'échantillon sportif. L'inscription et la découverte sont nouvelles ; les prix de découverte ne sont jamais réétiquetés en observations cibles et les deux cohortes ne doivent pas être comptées comme des événements indépendants.

| Tâche ponctuelle | Candidat | Cible UTC | Type |
|---|---|---|---|
| T1 | C1 | 21 octobre 2026 23:10 | J−1 |
| T2 | C2 | 22 octobre 2026 01:40 | J−1 |
| T3 | C1 | 22 octobre 2026 22:10 | H−1 |
| T4 | C3 | 22 octobre 2026 23:10 | J−1 |
| T5 | C2 | 23 octobre 2026 00:40 | H−1 |
| T6 | C3 | 23 octobre 2026 22:10 | H−1 |

Les heures de début sont des **proxies de début prévu**, pas des clôtures effectives. Un report d'heure, changement d'identité de marché/opérateur/issue, cote absente/non valide ou timestamp périmé exclut l'observation. Aucun échange d'opérateur ni sélection a posteriori des cotes n'est autorisé.

## Exécution ponctuelle préparée, non activée

[Six paires de fichiers systemd](systemd/) sont préparées : une date complète avec année pour chaque timer, sans récurrence, `Persistent=false` (pas de rattrapage automatique), sans délai aléatoire, service `Restart=no`. Leurs expressions de calendrier ont été vérifiées avec `systemd-analyze calendar`. Ils contiennent des chemins et utilisateur **à remplacer**, aucune clé. Aucun timer n'est installé ou activé.

[launch.py](launch.py) sélectionne le dernier état privé, puis [campaign.py](campaign.py) exécute une tâche unique. Le drapeau `--durable-host-confirmed` est une condition technique, pas une nouvelle demande d'autorisation : il ne doit être utilisé que lorsqu'un hôte persistant et un état partagé exclusif existent réellement. Le code utilise `fcntl` via le collecteur : hôte **Linux** requis, pas une tâche Windows directement compatible.

À chaque tâche sur un hôte équipé :

1. Contrôler clé publique/sous-clé attendues, dépôt privé et droit push, dernier état privé et absence de rejeu. Utiliser un verrou global distinct du verrou du collecteur.
2. Refuser un appel trop tôt. Après cible +5 minutes, consigner `missing_late`, chiffrer/sauvegarder l'état sans appel de cotes. Aucun rattrapage. Si le timer n'a jamais démarré, l'agrégateur hors ligne traite la fenêtre expirée sans capture comme une paire manquante.
3. Vérifier le quota par le catalogue gratuit ; réserver sur disque une seule tentative, l'archiver avant appel. Recontrôler l'heure après la sauvegarde : ne pas lancer une capture devenue tardive pendant l'export.
4. Effectuer **un seul** GET NBA/FanDuel `h2h`. La totalité de l'intervalle requête/réponse doit tenir dans ±5 minutes ; fraîcheur de marché 0–120 secondes au début de requête. Le corps entier reste privé, seuls les événements inscrits sont appariés.
5. Contrôler quota et coût après réponse. Évaluer chaque membre de la tâche, conserver les absences, suspensions inconnues, prix invalides et exclusions ; **aucun deuxième appel de remplacement**. Erreur API ou compteur manquant/incohérent : campagne arrêtée et état sauvegardé. Une interruption laisse une réservation qui interdit le rejeu de cette tâche.
6. Créer un nouvel état immuable et une nouvelle archive `.gpg`, sans écrasement de version ; contrôler privée/push, transférer uniquement le `.gpg`, retélécharger ce commit et comparer son SHA-256. Échec de sauvegarde : arrêter, conserver le disque privé et l'état de réservation, ne pas redemander les cotes.

Une sauvegarde ne garantit pas qu'un lancement arrive dans la fenêtre. Même sur un hôte durable, une coupure réseau ou de machine peut rendre un créneau manquant ; le protocole l'exclut plutôt que reconstruire.

## Plafond de crédits et arrêt

Le plafond **12 crédits inclut la découverte**. Baseline fournisseur avant campagne : 1 utilisé ; après découverte : 2, soit **1 crédit de campagne consommé**. Six cibles à un crédit chacune donneraient normalement **7 crédits au total**, sans tentative de remplacement. Le plafond n'est pas un budget à dépenser.

Le runner vérifie les compteurs entiers `x-requests-used`, `remaining`, `last` : arrêt avant appel si quota absent, restant nul, différence au baseline négative (reset), différence ≥12 ou 12 tentatives déjà réservées. Après réponse, il exige une augmentation égale au coût déclaré et un coût de 1 ; différence inattendue, compteur absent ou dépassement ⇒ arrêt sans nouvel appel. Une autre utilisation de la même clé peut consommer le budget observé : ce choix est conservateur, il ne relâche pas le plafond. Ne pas partager cette clé avec d'autres campagnes pendant les cibles ; pas de crédits présumés gratuits ni de passage automatique au payant. La tarification inattendue du fournisseur n'est pas contrôlable rétroactivement : elle entraîne un arrêt immédiat, sans tentative supplémentaire.

Aucun autre appel de cotes n'a été exécuté pour tester le runner. Les scénarios d'erreur sont simulés dans des tests explicitement unitaires.

## Comparaisons et rapport actuel

Le runner conserve les évaluations par cible ; l'agrégateur hors ligne `aggregate(state, root, asof)` ne calcule une variation que si les deux relevés du même événement passent les contrôles temporels, d'identité et de fraîcheur via `plan.compare_pair`. Il conserve les paires sans franchissement et les paires absentes/invalides. Le seuil reste **`abs(100*(C_H1-C_J1)/C_J1) >= 20`**, cotes décimales et Decimal, inclusif dans les deux directions.

Les règles et l'ouverture réelle restent non vérifiées : **aucune alerte validée**, même si une paire indicative valide franchit le seuil. Pas de prétention d'information privée ni de rentabilité.

[Rapport agrégé initial](aggregate_report.json) : trois paires en attente, zéro paire complète, zéro comparaison et zéro alerte validée. Aucun prix ni identifiant source sensible n'est publié. Après une exécution réelle, il faudra publier un nouveau rapport expurgé et l'empreinte de l'archive correspondante ; aucune publication automatique de prix ou d'état privé n'est préparée.

## Archivage réellement effectué

La clé publique principale et la sous-clé attendues ont été revérifiées. Le nouvel état, les statuts initiaux, la découverte réelle et tout l'historique privé existant ont été chiffrés par le `vault.py` existant. Le dépôt privé a été contrôlé avant/après, l'archive retéléchargée et son hash vérifié : [reçu](archive_receipt.json).

- Fichier : `campaign1_20261021T161135891269Z_770079b2.gpg`.
- Commit privé : `33e70374cd46b1f8b07a7ead3d16d37daaee8ae8`.
- SHA-256 : `07228e86cbcf047c65bcc69a0b1cfb4c9c07b9110132ab837cf4786aceea4882`.
- Taille chiffrée : 68 866 octets.

Les versions précédentes ne sont ni écrasées ni supprimées. Le dépôt public reçoit seulement code, cibles expurgées, reçus, compteurs et agrégats. Pas de clés API, mots de passe, tokens, clé privée, cotes brutes ou noms d'issues. La restauration complète de cette archive reste à tester avec la clé privée utilisateur sur Windows ; le cloud vérifie seulement le ciphertext et son intégrité de retour. Le format interne reste le même, avec maintenant **trois captures journalisées** (dont l'échec initial) et le manifeste initial épinglé obligatoire. Attention : le vérificateur Python actuel importe `pilot.py`, qui dépend de `fcntl` (Linux) ; son exécution Windows native nécessite un portage du verrou ou un environnement compatible. Aucune restauration Windows native réussie n'est affirmée. GnuPG Windows peut déchiffrer localement le ZIP, dont les fichiers peuvent être contrôlés avec leurs SHA-256, sans fournir la clé privée au cloud.

## Tests et blocage d'activation

**31 tests réussis**, dont 11 nouveaux garde-fous de campagne : quotas absents/non entiers, plafond/reset/restant, bords de fenêtre et réponse tardive, refus sans hôte, refus d'un dépôt public, snapshots immuables, retard sans appel API, rejeu réservé interdit, erreur API sans retry, compteur post-capture absent et timers finis sans rattrapage. Le test d'archivage existant a été adapté pour compter les entrées réellement journalisées plutôt que supposer qu'il en existe toujours deux ; aucun critère scientifique n'a été modifié.

L'environnement cloud ne fournit pas de scheduler durable attesté ; `at` et `crontab` ne sont pas disponibles. L'intégration GitHub renvoie **403** pour les paramètres Actions et la liste des secrets dans les dépôts concernés. La disponibilité de `THE_ODDS_API_KEY` dans ce cloud ne prouve pas qu'elle soit disponible dans GitHub Actions ; aucune valeur n'en a été extraite pour la recopier ailleurs. Un runner GitHub éphémère ne peut pas simplement déchiffrer l'état précédent sans clé privée, que nous ne lui demandons pas ; un état privé partagé et persistant reste nécessaire dans cette architecture.

L'utilisateur a confirmé ne disposer d'aucun hôte Linux persistant et demandé de documenter le blocage. **Aucune exécution ponctuelle n'est donc active.** Il reste à fournir un hôte durable, y installer Python 3/GnuPG/gh, transférer/restaurer de façon privée l'état initial, mettre la clé publique en lecture seule et configurer les secrets hors dépôt. Adapter les chemins/utilisateur des unités et l'authentification GitHub vers le dépôt privé ; ne pas mettre de token ou clé dans les unités versionnées. Tester l'accès au catalogue gratuit et l'archivage sans capture de cotes supplémentaire. Puis installer/activer uniquement les six timers encore futurs sur cet hôte, en excluant les échéances déjà passées. Pas de daemon de polling ni de workflow permanent.

Si aucun hôte n'est disponible avant les fenêtres, la campagne restera une inscription prospective avec observations absentes, pas une expérience exécutée. Les dates ne seront pas déplacées. Une nouvelle cohorte éventuelle devra être identifiée et inscrite séparément avant J−1.
