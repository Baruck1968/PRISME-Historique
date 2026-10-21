# Cotes sportives avant événement — audit de faisabilité

Audit du **21 octobre 2026**, en application de
[SPORTS_ODDS_SOURCE_FEASIBILITY.md](SPORTS_ODDS_SOURCE_FEASIBILITY.md).

**Décision : The Odds API est une candidate techniquement et contractuellement
adaptée à une étude de recherche, mais sa couverture historique française à
−20/−15/−10 minutes n’est pas encore validée. Aucun avantage prédictif ou économique
net n’est démontré. Football-Data n’est pas retenu pour cette fenêtre temporelle
et aucune acquisition automatisée n’y a été effectuée.**

Aucun compte créé, abonnement souscrit, paiement, pari, ordre, dépôt ou connexion
à un compte de jeu. Aucun calcul de rendement ni modèle prédictif exécuté.
PRISME 1–4 et le cahier des charges sont inchangés.

## 1. Ce qui a réellement été vérifié

Les documents officiels The Odds API et ANJ ont été obtenus en HTTP 200 après un
refus initial du proxy cloud. Les URL, dates UTC, tailles et SHA-256 figurent dans
[le journal documentaire](sports_odds_audit/evidence/2026-10-21-verified/access_report.json)
et [ses compléments ANJ](sports_odds_audit/evidence/2026-10-21-verified/supplementary_sources.json).

Un **échantillon historique public de The Odds API**, explicitement lié depuis
sa documentation, a été téléchargé sans clé et sans abonnement : snapshot
Bundesliga du **18 octobre 2022 à 01:55:39 UTC**, 18 événements, 12 clés de
bookmakers [S1, S6]. C’est un fichier d’exemple du fournisseur, pas une nouvelle
requête historique authentifiée ni un échantillonnage représentatif de son archive.
Les données brutes restent dans un cache local ignoré par Git ; seules références,
empreintes et diagnostics sont publiés, conformément à la restriction de
redistribution de données brutes [S4].

Les résultats communautaires OpenFootball pour la **Ligue 1 2023/24** ont également
été contrôlés : **306 matchs, tous avec score final**, sous dédicace au domaine
public [S8]. Aucune de ces données n’a été transformée en résultats statistiques
sur les mouvements de cotes.

## 2. Comparaison des deux sources demandées

| Critère | The Odds API | Football-Data |
|---|---|---|
| Trajectoires pré-match à trois instants | Snapshots nominaux de 5 min depuis septembre 2022 ; techniquement compatibles avec une fenêtre de 10–20 min, sous contrôle des temps réels | Le cadrage fourni décrit ouverture/clôture, pas une trajectoire à dix minutes ; ne permet pas de reconstruire les trois instants |
| Début global de l’historique | Marchés principaux depuis le 6 juin 2020, alors à pas de 10 min ; marchés additionnels depuis le 3 mai 2023 [S1–S2] | Non réaudité automatiquement |
| France actuelle | Région `fr`, cinq clés explicitement françaises, rapprochées des listes ANJ ci-dessous [S3, S5] | Couverture française par opérateur non vérifiée dans cet audit |
| Historique réel de chaque opérateur français | **Non établi** : le début global d’un sport n’est pas celui d’un bookmaker | Non établi ; aucune donnée téléchargée |
| Conditions pour la recherche/IA | Recherche, stockage indéfini et entraînement de modèles statistiques/ML explicitement autorisés par les conditions du 31 août 2026 [S4] | Le cahier des charges signale une exclusion de l’automatisation/scraping/IA ; autorisation applicable non établie |
| Diffusion brute sur GitHub | Ne pas redistribuer sous forme de source de données autonome ; publier méthodes, références, empreintes et résultats dérivés, pas une copie brute de l’archive [S4] | Aucun droit de redistribution établi |
| Accès historique | Uniquement forfaits payants ; pas de clé historique disponible ici ; aucune souscription [S1–S2] | Prix/droits actuels non vérifiés, aucun achat |
| Résultats des matchs | `/scores` couvre certains sports et les événements terminés jusqu’à trois jours auparavant ; pas une archive générale des résultats 2023 [S2] | Résultats annoncés dans le cadrage, mais non téléchargés ni utilisés |
| Conclusion | **Candidate conditionnelle** ; demander d’abord la preuve de couverture FR et un échantillon autorisé | **Non retenue pour l’objectif minute** ; une autorisation ne créerait pas les trajectoires temporelles manquantes |

### Portée exacte de la vérification Football-Data

Le [cahier des charges du dépôt](SPORTS_ODDS_SOURCE_FEASIBILITY.md) signale déjà
une restriction d’usage par IA et d’automatisation. Aucune requête automatisée n’a
été envoyée à `football-data.co.uk`, y compris pour télécharger des pages, CSV ou
copies miroirs. Ses conditions actuelles n’ont donc **pas** été relues par un outil
et aucune interdiction nouvelle n’est présentée ici comme un constat indépendant.

Une lecture humaine des [conditions du site](https://www.football-data.co.uk/)
et, si nécessaire, une autorisation écrite de l’éditeur sont requises avant tout
traitement automatisé. Même avec cette autorisation, des cotes d’ouverture et de
clôture ne datent pas trois observations à −20/−15/−10 minutes. On ne doit pas
interpoler une trajectoire et la présenter comme historique réel.

## 3. Priorité France : rapprochement documentaire et limites historiques

La région `fr` de l’annuaire actuel contient exactement ces cinq clés [S3]. Les
sites correspondants figurent pour les paris sportifs dans les deux pages ANJ
consultées [S5]. Il s’agit d’une concordance **actuelle** de noms/sites, pas d’une
preuve que leurs prix étaient tous capturés en 2022, ni d’un accès effectif à chaque
prix pour un utilisateur situé en France.

| Clé fournisseur | Site ANJ correspondant | Entité figurant sur la page ANJ | Historique aux trois instants |
|---|---|---|---|
| `betclic_fr` | `betclic.fr` | Betclic Enterprises Limited | Non testé / première date inconnue |
| `netbet_fr` | `netbet.fr`, `netbetsport.fr` | Netbet FR SAS | Non testé / première date inconnue |
| `pmu_fr` | `pmu.fr` | Pari Mutuel Urbain | Non testé / première date inconnue |
| `unibet_fr` | `unibet.fr` | Fdj Online Betting and Gaming France | Non testé / première date inconnue |
| `winamax_fr` | `winamax.fr` | Winamax | Non testé / première date inconnue |

Points déterminants :

- La documentation prévient explicitement qu’un bookmaker, sport ou marché n’est
  disponible historiquement **qu’à partir de son ajout au service** [S2]. Sa table
  donne le premier timestamp de **Ligue 1** au `2020-07-16T00:55:00Z` et de Ligue 2
  au `2020-07-16T01:45:00Z`, sans garantir la présence des cinq opérateurs [S1].
- L’échantillon public de 2022 contient notamment les anciennes clés `betclic`
  et `unibet_eu`, mais **aucune des cinq clés françaises actuelles**. Cela ne prouve
  pas l’absence historique de la France ; cela impose une table de correspondance
  des anciens identifiants et des versions nationales, fournie par l’éditeur.
- Le lien de l’annuaire pour « Betclic (FR) » mène à `betclic.com`, alors que l’ANJ
  liste `betclic.fr`. L’étiquette `_fr` est une indication documentaire, mais cette
  différence doit être clarifiée avant d’affirmer que les cotes sont exactement
  celles de l’offre française. Aucun site de bookmaker n’a été visité.
- Un nom comme `betsson` en région EU ne suffit pas à établir une couverture de
  `betsson.fr`. De même, `winamax_de` n’est pas `winamax_fr`.
- L’ANJ liste aussi des sites sportifs comme `bwin.fr`, `betsson.fr`, `bet365.fr`
  et `vbet.fr`, sans clé FR correspondante dans le tableau français lu. Le
  fournisseur ne doit pas être présenté comme couvrant tout le marché français.
- Les pages ANJ « opérateurs » et « canaux » ne donnent pas des listes parfaitement
  identiques. Leur intersection confirme les cinq correspondances ci-dessus,
  sans permettre un décompte juridique exhaustif. Il faut aussi contrôler la
  validité de l’agrément **à la date historique**, la compétition et le type de
  résultat autorisé via la liste sport [S5], pas seulement l’agrément actuel.

**Verdict sur la couverture historique réelle : non validée.** Aucune requête
payante n’a été effectuée sur les cinq flux nationaux. Une disponibilité affichée
aujourd’hui n’est pas une preuve rétrospective de continuité, de fraîcheur ou de
profondeur historique.

## 4. Horodatages : ce que cinq minutes permettent et ne permettent pas

Il faut conserver séparément : date demandée, `timestamp` du snapshot renvoyé,
`previous_timestamp`, `next_timestamp`, `bookmakers[].last_update`, éventuel
`markets[].last_update`, `commence_time` tel qu’observé à cette date, et réception
locale UTC. La documentation renvoie le snapshot le plus proche **antérieur ou
égal** à la date demandée [S1–S2].

Le fichier public testé illustre cette distinction : la documentation demande
`2022-10-18T02:00:00Z`, le snapshot est `01:55:39Z`, soit **4 min 21 s auparavant**.
Ses matchs commencent plusieurs jours plus tard. Ce fichier ne constitue donc
**pas** un test de couverture à −20/−15/−10 minutes.

Un intervalle nominal de cinq minutes ne garantit ni des ticks exactement alignés,
ni une actualisation de chaque opérateur à chaque tick. Deux demandes peuvent
renvoyer le même snapshot ; elles ne deviennent pas deux observations distinctes.
Un prix inchangé dans deux vrais snapshots doit aussi être distingué d’un prix
ancien simplement reconduit par le fournisseur.

L’exemple abrégé de documentation pour les marchés additionnels affiche un
snapshot `2023-11-29T22:40:39Z` et un `last_update` de marché `22:40:55Z` [S1].
Ce n’est pas une preuve de fuite dans l’archive : l’exemple peut être illustratif
ou refléter une construction asynchrone. C’est une raison de faire préciser ces
sémantiques et de vérifier les horodatages de chaque réponse réelle. Ne pas
réparer silencieusement un décalage, ni utiliser une mise à jour après le cutoff.

Pour une étude exécutable, l’ancre temporelle doit être l’heure de début **annoncée
et connue avant l’observation**. Un horaire final corrigé après coup peut servir à
un audit rétrospectif, mais pas à simuler un décideur qui le connaissait à l’avance.
Le début annoncé, le début réel, la suspension des paris et leur clôture chez
chaque opérateur sont quatre faits différents. La seule présence d’une cote ne
certifie pas son acceptation ; vérifier aussi les états pré-match/en jeu et les
annulations. Aucun de ces états d’exécution n’a été testé ici.

## 5. Tarifs, quotas et budget conditionnel — aucun achat

Prix mensuels affichés le 21 octobre 2026 [S7] :

| Forfait | Crédits/mois | Prix affiché en USD/mois | Historique |
|---|---:|---:|---|
| Starter | 500 | Gratuit | Non, selon la restriction explicite aux forfaits payants |
| 20K | 20 000 | **30** | Oui |
| 100K | 100 000 | **59** | Oui |
| 5M | 5 000 000 | **119** | Oui |
| 15M | 15 000 000 | **249** | Oui |

Aucune conversion en euros ni taxe non vérifiée n’est ajoutée. Le tarif facturé,
les taxes applicables et les conditions doivent être reconfirmés avant tout achat.
Les forfaits payants sont facturés immédiatement puis renouvelés mensuellement ;
les paiements sont annoncés non remboursables, sous réserve des exceptions prévues
par les conditions [S4, S7]. Aucun bouton de souscription n’a été utilisé.

Pour l’endpoint historique des marchés principaux, le coût documenté est
`10 × nombre de marchés demandés × nombre de régions`. Avec `bookmakers`, un
groupe allant jusqu’à **10** bookmakers équivaut à une région [S2]. Les cinq
clés FR ne multiplient donc pas à elles seules le budget par cinq. Le marché
football `h2h`/1X2 est une clé, malgré ses trois issues.

**Scénarios de dimensionnement, pas des requêtes exécutées ni des rendements :**

| Hypothèse : 3 snapshots/événement, 1 marché, 1 région, requêtes non mutualisées | Requêtes de cotes | Crédits de cotes | Plus petit forfait affiché couvrant ces crédits seuls |
|---|---:|---:|---|
| 306 matchs — nombre réel du fichier Ligue 1 contrôlé | 918 | **9 180** | 20K, 30 USD pour un mois |
| 1 000 événements — volume de travail hypothétique | 3 000 | **30 000** | 100K, 59 USD pour un mois |

Les requêtes de découverte historique coûtent un crédit si elles retournent des
événements ; les scores récents coûtent deux crédits avec `daysFrom` [S2]. Ajouter
les contrôles, répétitions utiles et requêtes supplémentaires. Les réponses vides
et marchés absents peuvent modifier le décompte ; lire les en-têtes
`x-requests-last`, `x-requests-used`, `x-requests-remaining`.
La mutualisation de matchs ayant les mêmes horaires peut réduire les appels.
Ces scénarios ne sont donc ni un devis ferme ni une preuve de données présentes.

## 6. Conditions d’utilisation et publication

Les conditions The Odds API, datées du **31 août 2026**, autorisent explicitement
le stockage indéfini, les articles de recherche, les valeurs dérivées et
l’entraînement de modèles statistiques et de machine learning [S4]. Elles
interdisent de revendre/reconditionner/redistribuer les données comme produit brut
autonome ou source concurrente. La publication intégrale des réponses sous forme
de fichiers téléchargeables sur GitHub ne doit pas être présumée autorisée.

Pour la suite : données de cotes en stockage privé, clés hors dépôt et hors logs,
code et requêtes reproductibles sans secret, identifiants/empreintes et résultats
agrégés publiés ; demander une confirmation écrite pour tout échantillon brut que
l’on souhaiterait redistribuer. Aucun message n’a été envoyé à un fournisseur.

Le service se décrit comme agrégateur indépendant, sans affiliation ni garantie
d’approbation par les bookmakers. Il documente des erreurs et retards possibles,
y compris des erreurs persistantes dans les snapshots historiques [S2, S4].
Une permission contractuelle de recherche ne garantit pas la qualité temporelle
ou l’exécutabilité des cotes.

## 7. Résultats disponibles et jonction aux cotes

L’endpoint The Odds API `/scores` peut retourner les matchs terminés des **trois
derniers jours**, pour les sports pris en charge ; ce n’est pas une API générale
permettant de récupérer tous les résultats de 2023 [S2]. Une collecte prospective
pourrait les archiver régulièrement, mais aucun compte ni collecteur n’a été
créé pour cette source.

Le fichier OpenFootball Ligue 1 2023/24 réellement lu contient 306 scores finaux,
306 champs horaires, **aucun champ explicite de fuseau** [S8]. Le README dédie
schéma, données et scripts au domaine public. Le fichier est publié ici pour
reproduction, contrairement aux données brutes The Odds API, qui ne le sont pas.

Cette alternative prouve une disponibilité de résultats pour une saison, pas
leur caractère officiel, l’heure réelle de coup d’envoi ou le règlement d’un pari.
Il faudra contrôler les scores auprès de sources sportives autorisées, les dates
reportées, les annulations et l’identité du match. Une jonction noms d’équipes/date
ne suffit pas sans traitement des alias, fuseaux et doublons. Ne pas confondre
score à 90 minutes, prolongation, tirs au but et conditions du marché utilisé.
Aucune jonction cotes françaises/résultats n’a été validée dans cet audit.

## 8. Information prédictive et avantage net : deux vérifications distinctes

Pour l’information : choisir avant accès aux issues une compétition/période,
les trois cutoffs, la fraîcheur maximale et les règles de manque. Comparer à
probabilité courante comparable une baseline calibrée à la fin de la fenêtre
avec le même modèle enrichi de la variation récente. Grouper toutes les observations
et bookmakers d’un même match, puis réserver une période chronologiquement
postérieure, avec incertitude par événement. Aucun réglage sur cette période.

Pour les cotes décimales `o_i`, `sum(1/o_i)-1` mesure l’overround du marché complet.
La normalisation `(1/o_i)/sum(1/o_j)` est une correction descriptive possible,
pas une probabilité vraie. Estimer/calibrer les transformations sur l’entraînement.
La marge est déjà incorporée aux cotes payées : ne pas la soustraire deux fois
lors du calcul économique.

Un gain de Brier ou log-loss n’implique pas un avantage économique. Pour une issue
binaire payée à cote décimale `o`, l’espérance théorique unitaire est `p*o-1` avant
coûts additionnels et règles de règlement. Ici ni p ni le prix accepté ne sont
estimés. Il manque notamment :

- la cote réellement accessible à la date/country/account autorisés, au moment
  où la décision aurait pu être prise, et la latence du flux ;
- l’acceptation, les changements de prix, suspensions, plafonds et capacité ;
- frais effectifs, règles d’annulation/remboursement, éventuelles commissions et
  coût fixe des données ; aucun taux de frais ou de fiscalité n’est inventé ;
- les règles de sélection de la meilleure cote, fixées avant le test, sans choisir
  après coup un opérateur ou une période favorable.

Les archives d’un agrégateur ne contiennent pas nécessairement ces faits. Elles
peuvent soutenir une étude de prix et une évaluation théorique conditionnelle,
**pas une rentabilité nette réalisable démontrée**. Aucune opération financière
n’est nécessaire ni autorisée dans cette phase. Un mouvement de cote n’est pas
une observation des mises, du flux d’ordres ou de l’information privée d’initiés.

## 9. Recommandation et prérequis précis

**Retenir The Odds API comme candidate pour un contrôle de données, pas pour un
achat immédiat.** Demander d’abord à l’éditeur, sans créer d’abonnement :

1. Pour chaque clé FR : domaine national réellement capturé, premiers/derniers
   timestamps par sport/marché et correspondances des anciennes clés (`betclic`,
   `unibet_eu`, etc.). Vérifier ensuite les agréments historiques auprès de l’ANJ.
2. Un petit échantillon autorisé de vrais événements français et de leurs trois
   snapshots avant début, choisi par dates/identifiants prédéfinis, pas par leur
   résultat ou leur mouvement. Le fichier public de Bundesliga ne répond pas à
   ce besoin.
3. Les sémantiques exactes des horodatages, les interruptions du flux, états
   pré-match/en jeu, la disponibilité des prix et la gestion des reports.
4. Une confirmation des droits du projet : analyse/ML, conservation privée,
   publication agrégée, limites éventuelles de diffusion d’extraits bruts.
5. La disponibilité de résultats historiques et d’horaires fiables, ou une méthode
   de jonction externe autorisée ; puis seulement un budget de requêtes validé.

Aucune clé Odds API n’est présente sous les noms contrôlés `ODDS_API_KEY` et
`THE_ODDS_API_KEY` ; le constat n’exclut pas l’existence d’un compte extérieur,
mais aucun droit d’accès historique n’a été fourni ou testé ici. Toute future
souscription nécessite une nouvelle autorisation explicite ; aucune n’est demandée
pour publier le présent rapport.

**Aucune source n’est entièrement validée à ce stade pour le double objectif
historique français et avantage économique net.** Le verrou prioritaire n’est
plus l’existence d’une API à cinq minutes : c’est la couverture historique
nationale réelle, puis les horodatages/conditions de prix réalisables.

## 10. Sources et reproduction

Toutes les pages indiquées « consultées » ont été obtenues le 21 octobre 2026.
Les exemples de documentation ne sont pas traités comme nos observations.

- **S1 — consulté :** [The Odds API — Historical Odds Data](https://the-odds-api.com/historical-odds-data/), couverture globale, dates par sport et exemples publics.
- **S2 — consulté :** [Documentation API v4](https://the-odds-api.com/liveapi/guides/v4/), sections historical odds/events, bookmakers et scores.
- **S3 — consulté :** [Annuaire des bookmakers](https://the-odds-api.com/sports-odds-data/bookmaker-apis.html), région FR et liens nationaux.
- **S4 — consulté :** [Terms and Conditions](https://the-odds-api.com/terms-and-conditions.html), dernière mise à jour affichée : 31 août 2026.
- **S5 — consultés :** [ANJ, opérateurs agréés](https://www.anj.fr/offre-de-jeu-et-marche/operateurs-agrees), [sites/canaux autorisés](https://anj.fr/offre-de-jeu-et-marche/categories-de-jeux-et-canaux-de-distribution) et [paris sportifs/liste sport](https://anj.fr/les-paris-sportifs#listesport).
- **S6 — consulté :** [Échantillon public historique Bundesliga](https://public-odds-api-sample-data.s3.amazonaws.com/historical-bundesliga.json), lié par S1 ; diagnostic et empreinte dans [public_sample_check.json](sports_odds_audit/evidence/public_sample_check.json).
- **S7 — consulté :** [Tarifs affichés](https://the-odds-api.com/#pricing), USD/mois, consultation sans souscription.
- **S8 — consultés et figés :** [Licence OpenFootball](https://github.com/openfootball/football.json/blob/e6744429ee395bc86f247348c6184bb08d4eb361/README.md#license) et [Ligue 1 2023/24](https://github.com/openfootball/football.json/blob/e6744429ee395bc86f247348c6184bb08d4eb361/2023-24/fr.1.json).
- **S9 — consulté et figé :** [Code officiel historique The Odds API](https://github.com/the-odds-api/samples-python/blob/dc344b7e93b70003d0fef35584c8edd78a4c40fb/historical_odds.py). Aucun script tiers n’a été exécuté.
- **Football-Data — non consulté automatiquement :** [page de téléchargements](https://www.football-data.co.uk/downloadm.php), restriction signalée par le cahier des charges ; vérification humaine/autorisation requise.

```bash
python research/sports_odds_audit/audit_sources.py --output /tmp/prisme-sports-audit-new
python research/sports_odds_audit/check_public_sample.py
python -m unittest discover -s tests -p test_sports_odds_sources.py -v
```

Le premier script ne contacte pas Football-Data, n’accepte aucune clé et interdit
les endpoints de cotes payants. Le second lit seulement le fichier d’exemple public
S6 ; il ne publie pas sa réponse brute. Les quatre tests ont réussi ; leur sortie réelle est conservée dans
`sports_odds_audit/validation.log`. Ils portent sur les garde-fous et les artefacts
réels, pas sur une performance prédictive. Choisir un répertoire de sortie
inexistant pour chaque nouvel audit ; aucune exécution ne remplace les preuves
publiées. Les pages HTML et données de
cotes brutes sont en cache ignoré, non ajoutées au dépôt. Les sources web peuvent
changer ; leurs empreintes attestent le contenu lu, sans garantie d’immuabilité
chez l’éditeur. Une première URL de conditions renvoyait une page 404 sous statut
HTTP 200 : ce faux positif a été diagnostiqué, la bonne URL consultée et le journal
initial conservé séparément comme non probant pour les conditions.
