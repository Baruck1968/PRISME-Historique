# PRISME-Archives privé — préparation et vérification du chiffrement

21 octobre 2026. Choix utilisateur : dépôt GitHub privé distinct `Baruck1968/PRISME-Archives`, conservation temporaire d'archives chiffrées et seconde copie Windows. **Solution préparée et restauration cryptographique testée localement ; dépôt privé non créé et aucune archive envoyée.** Deux prérequis externes restent nécessaires : création du dépôt avec des droits suffisants et clé publique dont l'utilisateur contrôle la clé privée Windows.

## Résultat GitHub concret

L'API authentifiée `GET /user` confirme le compte `Baruck1968`. `GET /repos/Baruck1968/PRISME-Archives` renvoie 404 : le dépôt n'est pas accessible avec l'intégration actuelle ; ce résultat seul ne distingue pas absence et dépôt privé hors périmètre.

La tentative autorisée `POST /user/repos` a demandé explicitement `private=true`, initialisation d'un README et désactivation des issues/wiki. Elle a été refusée : **HTTP 403, `Resource not accessible by integration`**. Un contrôle après ce refus renvoie toujours 404. Il n'y a aucune preuve de création et aucune archive n'a été téléversée. Ce n'est pas un rejet d'approbation automatique ni une raison de rendre le dépôt public : les droits de l'intégration sont insuffisants. Aucun jeton n'a été affiché, extrait ou enregistré.

**Action nécessaire** : depuis le compte GitHub existant, créer un dépôt nommé `PRISME-Archives`, sélectionner **Private**, initialiser un README. S'il existe déjà, vérifier son propriétaire et sa visibilité privée sans le recréer. Ensuite autoriser l'intégration GitHub utilisée par cet environnement à accéder spécifiquement à ce dépôt, si cette option est disponible. Ne pas envoyer de token dans le chat. L'accès en écriture à `PRISME-Historique` ne prouve pas l'accès au nouveau dépôt. À la reprise, vérifier par API `private=true`, `visibility=private`, propriétaire `Baruck1968` et droits d'écriture avant toute transmission, puis vérifier de nouveau après publication. Ne jamais utiliser le dépôt public existant comme repli pour des archives, même chiffrées.

## Choix du chiffrement et état des secrets

L'utilisateur a confirmé ne pas posséder de clé OpenPGP. Aucune clé permanente n'a été générée dans le cloud : elle devra être créée **sur Windows** et sa clé privée y restera, protégée par une phrase secrète. Seule la clé publique et son empreinte complète seront transmises au cloud pour chiffrer.

L'outil [vault.py](vault.py) utilise GnuPG installé ici. Il ne demande aucune phrase secrète pour chiffrer, n'utilise pas de clé privée, ne contacte aucun serveur de clés, vérifie que l'empreinte demandée appartient à la clé publique importée et crée un nouveau fichier sans écrasement. Le trousseau temporaire de production ne reçoit que la clé publique. Aucun mot de passe ni jeton n'est nécessaire dans le dépôt. Les paramètres de connexion restent gérés séparément par les outils d'authentification.

L'archive ZIP est construite en mémoire avant chiffrement OpenPGP ; le fichier persistant produit est uniquement le ciphertext `.gpg`, accompagné de son SHA-256. Le contenu sélectionné est limité aux captures JSON, manifestes et journal ; ni `.env`, ni dossier `.git`, ni trousseau, ni export des variables du processus. Une vérification refuse les valeurs actuellement liées à `THE_ODDS_API_KEY`, `GH_TOKEN` et `GITHUB_TOKEN` si elles apparaissent dans les fichiers sélectionnés ; ce contrôle ne prétend pas reconnaître tous les secrets possibles. Le mécanisme de sélection stricte reste la protection principale. Le répertoire de sortie doit être hors du dépôt public.

Le paquet contient les identifiants et issues des événements, les cotes et leurs horodatages tels que reçus, les corps source déjà conservés, le manifeste prospectif, les deux entrées du journal (dont l'échec initial) et un inventaire SHA-256 de chaque fichier. La chaîne du journal et les hashes des corps sont contrôlés avant emballage et après restauration. Les noms et prix restent à l'intérieur du paquet chiffré. Une archive ne contient pas la clé API utilisée pour récupérer les cotes.

## Manifeste initial préservé

Le manifeste privé du **21 octobre 2026 à 15:17:28.264762 UTC**, non réécrit, garde ses cibles initiales. Son SHA-256 est épinglé dans le vérificateur :

`627d076a2a2f161942254d83f83751416e41ed18e54869d621f920838739031d`

Les six cibles UTC restent : 21 octobre 23:10 ; 22 octobre 01:40, 22:10 et 23:10 ; 23 octobre 00:40 et 22:10. La capture de découverte de 15:14 UTC n'est **jamais** une observation J−1 de remplacement. Si une échéance est ratée, conserver l'absence et exclure la paire selon le plan ; ne pas modifier l'heure d'inscription ni recréer une cohorte équivalente antidatée. Aucune collecte ni programmation n'est effectuée par les outils de chiffrement ou restauration.

## Vérifications effectuées

[Quatre tests dédiés ont réussi ici](validation.log), non sautés :

1. Paquet préparé à partir des **vrais fichiers privés existants**, chiffré, déchiffré et restauré dans un dossier temporaire ; chaque fichier restauré égale l'original, manifeste et deux captures du journal compris.
2. SHA-256 du ciphertext vérifié ; un ciphertext altéré a un hash différent et le déchiffrement termine en erreur.
3. Modification du manifeste initial détectée malgré un JSON éventuellement encore valide ; contrôle de l'inventaire et de la chaîne à la restauration. Les chemins ZIP traversants et l'écrasement d'une destination sont refusés.
4. Un fichier inattendu de type `.env` est refusé avant constitution du paquet.

**Clé de test exclusivement** : une clé RSA 2048 temporaire, sans phrase secrète pour le test automatisé, a été générée dans un répertoire privé temporaire hors dépôt et détruite avec lui. Ce n'est pas une clé de sauvegarde utilisateur. Aucune archive de production n'est prétendue récupérable avec cette clé, aucun ciphertext de ce test n'a été publié. Le choix de clé Windows recommandé ci-dessous est distinct. Les données originales restent conservées, avec les copies locales de staging précédentes.

La restauration **sur Windows** n'a pas été exécutée : aucun ordinateur Windows n'est connecté ici. Le script PowerShell est préparé mais non exécuté. Un succès Linux local ne prouve ni sa compatibilité effective avec votre installation ni une sauvegarde intersession. Le test bout en bout avec la véritable clé utilisateur et le fichier retéléchargé de GitHub reste un préalable à une sauvegarde déclarée opérationnelle.

## Étapes Windows — génération, sauvegarde, restauration

1. Installer Gpg4win/GnuPG depuis sa distribution officielle, sans option payante obligatoire : [Gpg4win](https://www.gpg4win.org/). Disposer de Git et Python 3 si les vérificateurs en ligne de commande sont utilisés ; aucune installation sur votre ordinateur n'a été réalisée ici.
2. Dans Kleopatra, créer une **paire de clés OpenPGP avec capacité de chiffrement**, par exemple RSA 3072 ou plus, et protéger la clé privée par une phrase secrète saisie uniquement sur Windows. Conserver une copie de récupération de la clé privée et son certificat de révocation sur un support distinct sécurisé, jamais dans GitHub. La perte de la clé privée rend l'archive irrécupérable ; la perte du mot de passe peut également empêcher sa lecture.
3. Exporter uniquement la clé **publique** en ASCII (`.asc`) et relever son empreinte complète. Exemple PowerShell, après remplacement de `EMPREINTE_COMPLETE` par l'empreinte affichée localement :

```powershell
gpg --fingerprint EMPREINTE_COMPLETE
gpg --armor --output "$env:USERPROFILE\PRISME-public.asc" --export EMPREINTE_COMPLETE
```

La sortie attendue contient `BEGIN PGP PUBLIC KEY BLOCK`, jamais `PRIVATE KEY`. Fournir ce fichier public ou son texte et son empreinte au cloud. Ne jamais transmettre la phrase secrète, un export `--export-secret-keys` ou un token d'authentification.

4. Après réception et confirmation de l'empreinte, préparation cloud manuelle (exemple, chemins de fichiers sans secret) :

```sh
python research/observatoire_v1/vault/vault.py encrypt --source research/observatoire_v1/private --public-key /CHEMIN/PRISME-public.asc --recipient EMPREINTE_COMPLETE --output /workspace/prisme-encrypted-staging/prisme-20261021.gpg
```

Cette commande **n'a pas été exécutée avec une clé utilisateur**, puisqu'elle n'existe pas encore. Elle ne transfère rien. L'empreinte SHA-256 du fichier `.gpg` sera publiée dans un rapport expurgé de `PRISME-Historique` pour permettre un contrôle indépendant du téléchargement. L'inventaire interne, les prix et participants restent chiffrés. Ne pas publier l'archive chiffrée dans ce dépôt public.

5. Vérifier que `PRISME-Archives` est effectivement privé et accessible, puis y versionner uniquement le `.gpg`, son fichier `.sha256` et un README sans secret. Pas de workflow, artifact, Git LFS, donnée brute, zip non chiffré, clé privée, passphrase, jeton ou fichier de configuration d'authentification. Contrôler les fichiers indexés avant le push et relire la visibilité privée après. Ces opérations attendent les deux prérequis ci-dessus ; elles ne sont pas exécutées ici.
6. Sur Windows, cloner/télécharger le dépôt privé avec votre authentification habituelle, **sur le disque de votre ordinateur**, hors dossier de travail cloud. Conserver également une copie datée du ciphertext et de son hash sur un support indépendant, si disponible. Un clone synchronisé qui suit automatiquement les suppressions ne suffit pas : garder les snapshots datés et tester la lecture hors ligne. Ne jamais partager publiquement le lien d'archive ni désactiver la visibilité privée.
7. Vérifier le SHA-256 du fichier `.gpg` avec la valeur ancrée dans le rapport public :

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\PRISME-Backup\prisme-20261021.gpg'
```

Puis, depuis un clone du dépôt de **code** `PRISME-Historique`, restaurer vers un nouveau dossier privé Windows avec [Restore-Prisme.ps1](Restore-Prisme.ps1) :

```powershell
.\research\observatoire_v1\vault\Restore-Prisme.ps1 -ArchivePath 'D:\PRISME-Backup\prisme-20261021.gpg' -ExpectedSha256 HASH_SHA256_PUBLIE -Destination 'D:\PRISME-Restauration\essai-20261021'
```

La phrase secrète est demandée par GnuPG localement, pas dans la commande. Le script vérifie le hash du ciphertext, exige le succès du déchiffrement puis valide les hashes internes, la chaîne et le manifeste épinglé. Il supprime uniquement son zip temporaire, pas l'archive ni les données restaurées. Le dossier temporaire est sous `%LOCALAPPDATA%\PRISME\restore-work` : vérifier que ses droits Windows sont limités à votre compte. La suppression d'un temporaire n'est pas un effacement sécurisé ; un disque Windows chiffré et des ACL adaptées restent nécessaires. Le ZIP et les observations déchiffrées ne doivent jamais être commités ou partagés.

## Conservation et limites de la solution retenue

Aucun coût d'abonnement activé ; GitHub Free permet les dépôts privés et le volume actuel est de quelques dizaines de kilo-octets. Aucun quota Actions, aucun LFS, aucune automatisation requis. Ce choix utilisateur remplace la recommandation précédente comme destination temporaire envisagée, sans effacer ses limites : Git n'est pas un outil de sauvegarde spécialisé ; le compte peut devenir inaccessible, un dépôt être supprimé ou son historique réécrit. Maintenir la seconde copie Windows et la clé de récupération séparément. Ne pas supprimer le workspace original avant restauration de la véritable archive utilisateur vérifiée.

Conserver snapshots et manifeste au moins jusqu'à l'audit scientifique ; la durée finale et le nettoyage ultérieur restent à fixer explicitement, aucune suppression programmée. Ne pas compter sur une restauration de dépôt supprimé comme garantie. Les conditions The Odds API examinées autorisent la conservation des observations pour recherche ; la confidentialité du dépôt et le chiffrement doivent empêcher leur redistribution comme flux brut autonome. Aucune promesse d'archive perpétuelle, de WORM ou de garantie contractuelle n'est formulée.

**Obstacles précis** : dépôt non créé (403 de l'intégration), clé publique utilisateur manquante, transfert chiffré non effectué, sauvegarde/restauration Windows non vérifiée. Après création privée et réception de la clé publique, il restera à réaliser une vraie archive chiffrée, son push privé et son test de restauration depuis Windows. Aucune nouvelle capture de cotes et aucune programmation n'est autorisée par cette préparation.
