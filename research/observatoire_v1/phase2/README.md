# Phase suivante — plan prospectif J−1/H−1, non activé

Préparé le 21 octobre 2026 à partir de la capture réelle documentée au commit `30903b6`. Aucun appel API supplémentaire n'a été effectué pour cette préparation. Le collecteur existant, le protocole et le seuil **±20 % inclusif** restent inchangés. Aucun ordonnanceur ni workflow de cotes créé.

## Faisabilité effectivement observée

Le corps privé de la capture du 21 octobre à 15:14 UTC est présent et son SHA-256 est vérifié. Sur ses 43 événements futurs, 14 ont un `fanduel/h2h` à deux issues correspondant aux deux participants, frais à la découverte. Pour 11 d'entre eux, J−1 est déjà passé à la création du manifeste. Les 29 autres n'ont pas le marché requis dans cette capture ; ils sont conservés comme absents dans le manifeste, sans supposer qu'ils resteront absents.

**Trois candidats sont prospectivement suivables aux deux cibles**, sous réserve qu'ils restent proposés et que l'heure ne change pas. Il est impossible aujourd'hui de garantir leur disponibilité future. Le tableau ci-dessous présente uniquement les échéances techniques ; identifiants, participants et deux issues sont conservés dans le manifeste privé.

| Candidat local | Début prévu UTC (proxy) | J−1 UTC | H−1 UTC |
|---|---|---|---|
| 1 | 22 octobre 23:10 | 21 octobre 23:10 | 22 octobre 22:10 |
| 2 | 23 octobre 01:40 | 22 octobre 01:40 | 23 octobre 00:40 |
| 3 | 23 octobre 23:10 | 22 octobre 23:10 | 23 octobre 22:10 |

Les trois J−1 sont postérieurs à l'inscription prospective du **21 octobre 2026 à 15:17:28.264762 UTC**. L'ancienne capture est une découverte et ne remplace aucun de ces J−1. Si l'autorisation ou la préparation du stockage arrivent trop tard, consigner J−1 manquant et exclure la paire ; ne pas relancer l'inscription pour contourner l'échéance passée. Les heures restent figées même si un match est reporté. Aucun résultat sportif futur n'est consulté pour sélectionner ces candidats.

## Manifeste privé créé

Le fichier `manifest_20261021T151728267195Z.json`, dans `research/observatoire_v1/private/`, conserve les 43 événements avec `event_id`, source, `sport`, `commence_time` initiale, type d'ancre `scheduled_start_proxy`, opérateur `fanduel`, marché `h2h`, noms exacts des deux issues quand présents, J−1/H−1 calculés, indicateur de candidature et motifs d'exclusion. Les règles restent inconnues (`rules_id=null`), l'ouverture inconnue. Les issues des marchés absents ne sont pas inventées. Les 14 marchés présents ont été validés structurellement par l'adaptateur, sans certifier leurs règles de règlement.

Le fichier ne contient pas la clé et n'est pas suivi par Git. Son empreinte SHA-256, publiée dans [manifest_summary.json](manifest_summary.json), est :

`627d076a2a2f161942254d83f83751416e41ed18e54869d621f920838739031d`

Le script [plan.py](plan.py) permet de reproduire l'algorithme hors ligne ; une nouvelle exécution ajoute un nouveau fichier sans écraser celui-ci, mais **ne remplace pas l'inscription publiée ni son heure**. Les candidats d'une exécution ultérieure peuvent différer si J−1 est passé ; toute nouvelle cohorte doit être identifiée explicitement. Aucune commande de planification n'effectue de capture.

```sh
python research/observatoire_v1/phase2/plan.py
python -m unittest discover -s tests -p 'test_observatoire*.py' -v
```

## Contrôles et comparaisons

Avant chaque relevé autorisé : vérifier que le manifeste correspond au hash publié, contrôler la chaîne de stockage et le budget, puis utiliser le collecteur existant une seule fois à la cible. La requête concerne le sport entier ; extraire ensuite les seuls événements inscrits sans changer l'opérateur ni rechercher une cote de remplacement chez un concurrent. Conserver le corps privé complet et toutes les exclusions. Début et fin de requête doivent être dans la fenêtre existante ±5 minutes ; prix du marché âgé de 0 à 120 secondes au début. Les six cibles sont distinctes : six appels de cotes prévus, pas une boucle de polling.

`assess(manifest, row, envelope, 'J1'/'H1')` vérifie l'inscription, le temps de capture, les identifiants, opérateur/marché, les deux noms d'issues, le sport/source, la fraîcheur et l'absence de changement d'heure. Un marché absent, trois issues, cote invalide, capture réseau échouée, timestamp absent/futur/périmé ou déplacement d'heure exclut l'observation. `envelope=None` signifie manquant, jamais prix nul ni report du dernier prix connu. Pas de backfill historique payant, d'interpolation ou de réutilisation de la découverte comme relevé cible.

`compare_pair` n'effectue de calcul que si les deux relevés passent ces contrôles : il appelle alors le comparateur existant (Decimal, ±20 %), conserve aussi les non-franchissements et n'émet **aucune alerte validée**. Les règles et l'ouverture restent inconnues dans l'adaptateur. Les variations restent indicatives même si le seuil est franchi. Le système n'infère pas une acceptation des paris à partir de la présence d'une ligne récente. Pour un résultat scientifique validé, il faudra une source documentée des règles et de l'ouverture ; les champs ne doivent pas être remplis artificiellement.

Conserver les doublons dans le journal, identifier un seul relevé primaire par événement et créneau (première requête entièrement dans la fenêtre, selon règle fixée avant collecte). Ne pas choisir après coup le prix le plus favorable. Une seconde capture éventuelle ne remplace pas silencieusement une première : motif et numéro de tentative requis. `compare_pair` rejette une paire non chronologique via le comparateur existant. Aucune gestion automatique des relances n'est activée.

## Budget et limites d'accès

Dernier compteur observé : **499 crédits restants**, après 1 crédit consommé le 21 octobre à 15:14 UTC. Ce n'est pas un solde actualisé ; d'autres utilisations de la clé peuvent le modifier. Les six captures prévues coûtent normalement 6 crédits pour `h2h` et un opérateur. Au maximum deux contrôles de cotes supplémentaires peuvent être envisagés dans un budget préparatoire de 8 crédits **uniquement après autorisation**, sans les transformer en relances automatiques. Le catalogue gratuit peut contrôler l'accès et le quota avant le premier relevé ; ne pas relancer sur 401/403/429. Vérifier les en-têtes après chaque appel. Un quota absent est « inconnu », pas zéro crédit. Si le solde est insuffisant/inconnu ou le coût différent du coût attendu, arrêter et documenter. Aucune montée de gamme ni facturation automatique.

## Stockage privé durable : prêt à raccorder, pas encore disponible

Le dossier local `private/` est ignoré par Git ; accès maintenant limité au propriétaire (dossier 0700, fichiers 0600). Il contient les captures antérieures, le journal append-only et le manifeste réel. **Ce stockage cloud local n'est pas une archive durable attestée.** Aucun espace privé externe avec persistance, chiffrement, sauvegarde/versionnage et authentification opérationnelle n'a été fourni ni testé pour cette tâche. Aucun compte ou service de stockage n'a été créé.

Cible proposée : volume privé persistant de l'utilisateur, chiffré au repos, avec sauvegarde/versionnage et accès minimum, monté hors du dépôt. [archive.py](archive.py) prépare une copie sous verrou vers une destination explicitement fournie, vérifie les noms autorisés, permissions, hash de chaque fichier et chaîne du journal. Il inclut le manifeste et les observations exclues sans écraser un snapshot précédent. Exemple **à exécuter seulement après fourniture d'un volume privé durable** :

```sh
python research/observatoire_v1/phase2/archive.py research/observatoire_v1/private /CHEMIN_VOLUME_PRIVE_DURABLE
```

La commande ne provisionne ni chiffrement ni sauvegarde et renvoie toujours `durability_confirmed=false` : un succès de copie ne prouve pas la persistance du support. Les tests utilisent un répertoire temporaire et ne constituent pas une sauvegarde réelle. Un export brut dans un dépôt GitHub, une issue, un artifact Actions public ou un service tiers non vérifié est exclu. Ne pas mettre les clés dans l'archive. La copie doit être réalisée dès que possible pour conserver le manifeste avant toute disparition du workspace, puis après chaque relevé autorisé. Tester une restauration sur un autre répertoire privé, vérifier les hash et la chaîne, et ancrer le dernier hash dans un rapport dépourvu de cotes. Préserver les fichiers orphelins après incident pour audit ; ne pas les supprimer.

## Tests et obstacles avant activation

[16 tests passent](validation.log), dont 7 nouveaux : inscription avant J−1 seulement, hash et absence de création antidatée, manque explicite, statut indicatif, déplacement d'heure/fraîcheur, copie vérifiée et détection d'altération, refus d'archive dans le dépôt, paire complète indicative et absence de calcul si un créneau manque. Les fixtures sont artificielles exclusivement pour les tests ; le manifeste et les comptes ci-dessus proviennent de la vraie capture. Aucun couple J−1/H−1 réel n'est encore disponible.

Les obstacles restants sont : destination privée durable et restauration à vérifier, disponibilité des trois marchés aux cibles, règles et état d'ouverture non prouvés, et autorisation explicite de programmation. Un ordonnanceur n'est pas installé : GitHub Actions peut être retardé et ne garantit pas la fenêtre. Avant toute activation, choisir un ordonnanceur et un hôte durable, fixer l'heure de lancement et le traitement des retards, et donner une nouvelle autorisation. Tant que cela manque, les échéances sont un plan et non des collectes promises. PRISME 1–4, le protocole et les fichiers précédents restent inchangés. Aucun achat, pari ou opération financière.
