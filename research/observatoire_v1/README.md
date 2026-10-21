# Pilote PRISME Observatoire V1 — préparé, non activé

Python 3.12, bibliothèque standard uniquement. Aucun service à démarrer ni dépendance à installer. Depuis la racine du dépôt :

```sh
python research/observatoire_v1/audit.py
python -m unittest discover -s tests -p test_observatoire_v1.py -v
python research/observatoire_v1/pilot.py --help
```

`audit.py` télécharge uniquement les pages documentaires explicitement listées. Chaque exécution ajoute un journal d'accès UTC avec URL, statut, empreinte SHA-256 et éventuel blocage ; les pages originales restent dans `.cache/`, ignoré par Git. Un HTTP 200 peut être une soft 404 : examiner `soft_404` et le contenu. Les journaux initiaux conservent les refus proxy de TheOddsAPI, puis les accès réussis après propagation réseau. Le premier journal conserve l'erreur de chemin de la page des intervalles, corrigée dans le second.

## Capture conditionnelle, pas de flux déjà vérifié

L'utilisateur doit lui-même demander une **clé gratuite Starter** à The Odds API et la fournir sous `THE_ODDS_API_KEY` via un gestionnaire de secrets / les paramètres sécurisés de l'environnement. Ne pas mettre sa valeur dans une commande, un fichier suivi ou une conversation. Aucun compte ni abonnement n'a été créé ici. Une clé de `theoddsapi.com` n'est pas interchangeable.

Après confirmation des conditions et du bookmaker accessible dans le plan gratuit :

```sh
python research/observatoire_v1/pilot.py capture --sport basketball_nba --bookmaker fanduel
python research/observatoire_v1/pilot.py verify research/observatoire_v1/private
```

Cette commande est un exemple d'identifiants du fournisseur, **pas une validation des règles de FanDuel ni une recommandation d'opérateur**. Elle demande un sport, `h2h`, un opérateur, format décimal et dates ISO, en GET HTTPS seulement. Aucun endpoint de pari, aucune écriture distante, aucun accès historique payant. Pas de redirection avec la clé. Les exceptions ne révèlent pas les URL contenant la clé. Un appel non vide coûte normalement un crédit ; l'offre ne garantit pas l'accès à chaque opérateur. Examiner les en-têtes de quota conservés. Pas de retries automatiques ni de polling actif.

Le dossier `private/` est ignoré. Ne pas changer sa destination vers un dossier publié ; les données brutes ne doivent pas devenir un flux de redistribution. Les captures enregistrent début et fin de requête UTC, corps reçu et son empreinte, fournisseur, paramètres non secrets, quota et échecs réseau. Un nom UUID et une création exclusive évitent les écrasements ; verrou interprocessus Linux, fsync, journal append-only et chaîne SHA-256. Toutes les captures, doublons et non-alertes restent conservées. Une panne peut laisser un fichier orphelin : le conserver et l'auditer avant reprise. Une chaîne locale sans ancrage extérieur ne prouve pas l'absence de suppression de sa fin ; prévoir stockage privé durable, sauvegarde et ancrage signé du dernier hash. Le stockage temporaire cloud ne suffit pas.

## Appariement hors ligne

```sh
python research/observatoire_v1/pilot.py compare CHEMIN_PRIVE_J1 CHEMIN_PRIVE_H1 --event IDENTIFIANT --bookmaker OPERATEUR
```

Le comparateur utilise exclusivement l'heure prévue de début **proxy** lue à J−1, jamais l'heure réelle future. Une modification de cette heure à H−1 exclut la paire. Fenêtres préfixées ±5 minutes autour de J−1 et H−1 ; la requête entière doit tenir dans la fenêtre. Mise à jour du **marché** obligatoire, âgée de 0 à 120 secondes au début de la requête. Pas de repli sur le champ bookmaker désormais déprécié. Pas de comparaison entre sources, événements, opérateurs, marchés, règles ou noms d'issues différents. Deux issues distinctes correspondant aux deux participants seulement ; 1X2 refusé. Annulations, remboursements et matchs nuls doivent être traités selon un règlement vérifié : deux prix ne prouvent pas deux issues exhaustives.

`--rules-id` est seulement une référence documentaire commune, vide par défaut ; il ne certifie rien. Une version future devra associer à chaque capture le règlement source, sa version, ses règles de prolongation/abandon et l'état ouvert vérifié. **L'adaptateur actuel ne reçoit pas d'état d'ouverture explicite et renvoie toujours `open_status=unknown`**. Il ne peut donc produire aucune alerte valide, même avec une clé et un identifiant de règlement. Ne pas modifier les relevés pour contourner ce blocage. Les `candidate_changes` sont des calculs exploratoires non validés, avec motifs d'exclusion, et non des signaux. L'algorithme conserve les non-alertes et utilise Decimal : ±20 % inclus, variation de cote décimale et non variation de probabilité. Aucun envoi de notification n'est implémenté.

Les tests contiennent des valeurs **artificielles explicitement unitaires**, sans prétendre représenter des marchés réels. Aucun résultat de pilote ni aucune statistique prédictive n'est dérivé de ces fixtures.

## Plan de collecte à valider

Découvrir les événements avant J−1 (endpoint `/events`, quota nul selon la documentation), figer un manifeste d'événements, participants, opérateurs et règles, puis programmer les deux cibles UTC. Le collecteur manuel ne fait pas encore cette découverte ni cet ordonnancement : ne pas prétendre disposer d'un pilote autonome. Conserver les exclusions et événements absents, ne pas sélectionner seulement les mouvements. Une paire nécessite deux vraies observations séparées d'environ 23 heures ; deux appels consécutifs ne conviennent pas.

Pour un sport, un marché, un opérateur, deux appels par jour représentent environ 60 crédits / mois de 30 jours ; ce n'est **pas** une couverture J−1/H−1 de tous les événements. Avec 500 crédits, 250 paires constitue un plafond théorique sans erreurs, scores, répétitions ni réserves ; plusieurs événements peuvent partager un appel et les horaires réels peuvent au contraire exiger beaucoup plus d'appels. Prévoir 100 crédits de réserve, arrêter sur quota insuffisant, figer le budget avant automatisation. Ce limiteur n'est pas encore codé : ne pas lancer de boucle automatique.

GitHub Actions n'offre pas de précision à la minute et peut être retardé ; toute capture hors fenêtre doit être exclue. Aucun nouveau workflow n'est créé. Une programmation seule ne valide pas un flux, et un flux seul ne prouve pas une paire exploitable. Rapport principal : [faisabilité](../PRISME_OBSERVATOIRE_V1_FEASIBILITY_REPORT.md).
