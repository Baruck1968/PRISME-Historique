# PRISME 4 — Collecteur prospectif borné

Première capture réelle réussie le 21 octobre 2026 : 30 marchés, 61 réponses GET,
0 erreur réseau ; le premier échec de schéma est conservé et documenté.
Stockage brut horodaté, SHA-256, chaîne de manifestes et rejeu hors ligne vérifiés.
Aucun pari, ordre ou transaction. Aucun score statistique calculé.

Le pilote de 56 jours et l’horaire quotidien 06:00 UTC ont été explicitement
confirmés par l’utilisateur. Fin : 16 décembre 2026 à 13:39:07 UTC.

**État à cette publication technique : capture locale confirmée, workflow GitHub
Actions à publier puis à contrôler. Aucune collecte autonome déclarée active.**

Le workflow proposé contient un déclenchement quotidien à 06:00 UTC, un test
contrôlé au premier push, une commande manuelle, la sauvegarde des données dans
le dépôt et un arrêt de capture à 56 jours. Une exécution réelle du workflow reste
à confirmer. Un fichier cron seul ne prouve pas une programmation effective.

La cohorte est figée aux 30 premiers candidats ouverts binaires retournés par
la recherche publique anonyme, tri newest, à l’initialisation. Pas de remplacement
ni de sélection selon l’issue. Tous les états ultérieurs sont conservés, y compris
après fermeture ou résolution. Ce sont des candidats, pas encore une population
scientifique admissible : règles objectives, issue encore inconnue et événements
communs doivent être audités. Le registre manuel déterministe est en attente.

```bash
python experiments/prisme4/collector.py verify
python -m unittest discover -s tests -p test_prisme4.py -v
python experiments/prisme4/collector.py capture --purpose validation
```

La dernière commande effectue une nouvelle capture réelle, dans un nouveau dossier,
sans remplacer une journée manquante. Les réponses se trouvent dans
`store/runs/<UTC_unique>/raw.zip`, avec manifestes, observations et journal d’erreurs.
Le fichier `state.json` est un index mutable ; les captures terminées sont immuables.
Les exécutions quotidiennes utilisent `--purpose daily`, avec idempotence par jour UTC.
Les métadonnées enregistrent les temps réels, pas un instant 06:00 fictif.

La première capture de faisabilité n’est pas alignée à 06:00 ; aucune paire à
24 heures n’est disponible aujourd’hui. Le diagnostic de tolérance de 300 secondes
n’autorise pas à lui seul une observation scientifique et doit être accepté avant
analyse. Aucun historique manquant n’est remplacé par la valeur courante.

Voir `collection_plan.json` et `deployment.json` dans `experiments/prisme4`,
`diagnosis_initial_failure.json`, `clock_check.json` et le registre manuel.
Le rapport d’autonomie sera complété après publication et contrôle du workflow.
