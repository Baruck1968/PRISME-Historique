# Campagne 1 sur Windows — portage préparé, aucune activation

21 octobre 2026. Référence : `84d137e`. **La chaîne d'exécution ponctuelle est portée vers Windows et testée hors ligne sur Linux ; aucune tâche Windows n'est créée, activée ou exécutée dans cet audit.** Aucun nouvel appel API de cotes, aucun événement inscrit, aucun manifeste modifié. Il manque une validation native sur l'ordinateur utilisateur avant de prétendre la campagne opérationnelle.

## Échéances inchangées et état actuel

Le contrôle hors ligne à **2026-10-21T16:25:33.293631 UTC** trouve les six cibles encore futures ; **aucune n'est actuellement non récupérable**. Les onze J−1 déjà exclus avant l'inscription initiale restent absents dans l'historique, sans prix reconstruit. [expiry_report.json](expiry_report.json) publie uniquement les tâches, dates UTC et empreintes, pas les événements ou cotes.

| Tâche | UTC | Fenêtre UTC |
|---|---|---|
| T1 — C1 J−1 | 21 octobre 23:10 | 23:05 à 23:15 |
| T2 — C2 J−1 | 22 octobre 01:40 | 01:35 à 01:45 |
| T3 — C1 H−1 | 22 octobre 22:10 | 22:05 à 22:15 |
| T4 — C3 J−1 | 22 octobre 23:10 | 23:05 à 23:15 |
| T5 — C2 H−1 | 23 octobre 00:40 | 00:35 à 00:45 |
| T6 — C3 H−1 | 23 octobre 22:10 | 22:05 à 22:15 |

La génération des tâches recalcule les expirations à l'heure de son exécution : après cible +5 minutes, le créneau est marqué **`non_recoverable` dans un rapport séparé**, sans XML de capture pour ce créneau. À la limite exacte +5 minutes, la contrainte scientifique reste inclusive ; aucune requête/réponse ne doit dépasser la fenêtre. Un lancement reçu après cette limite enregistre l'absence sans appel de cotes. Aucune date n'est décalée pour compenser un PC indisponible. Les manifestes initiaux restent inchangés.

Empreintes vérifiées :

- Manifeste initial : `627d076a2a2f161942254d83f83751416e41ed18e54869d621f920838739031d`.
- État privé initial de campagne : `92aa4f3d46bfec27bfc1ece46497cb8c3add29d9f76b91f70b8067df38148d98`.

Les identifiants et deux issues restent dans le manifeste privé chiffré. Les alias C1–C3 ne redéfinissent aucun événement. FanDuel, `h2h`, les six dates et la cohorte restent celles publiées.

## Adaptations strictement techniques

Le collecteur utilise désormais [file_lock.py](../file_lock.py) : `fcntl.flock` sur Linux et verrou natif `msvcrt.locking` d'un octet sur Windows. Acquisition exclusive non bloquante avec attente bornée à 30 secondes, libération dans `finally` et par fermeture du handle lors d'une interruption. Le fichier verrou n'est jamais supprimé pour « débloquer » un processus. Le verrou global de campagne et le verrou du journal restent distincts ; une réservation persistée empêche le rejeu même après crash. Tous les processus doivent utiliser ce même portage, un même état et un disque local NTFS ; pas de copies parallèles d'état, de partage SMB non validé ou de synchronisation OneDrive comme mécanisme de verrouillage.

Aucune formule, fenêtre ou règle de sélection n'est changée. Le runner conserve : ±5 minutes pour **toute** la requête/réponse, fraîcheur marché 0–120 secondes, mêmes identifiants/source/sport/opérateur/marché/issues et début initial, absence de report d'heure, Decimal et ±20 % inclusif. Les paires incomplètes/invalides ne produisent pas de variation ; les non-franchissements sont conservés. Les règles et l'ouverture restent inconnues : les résultats éventuels demeurent indicatifs, sans alertes validées.

Le quota reste plafonné à 12 crédits, découverte incluse (dernier état connu : **1 crédit de campagne**, 498 restants sur le compte). Ce solde n'a pas été réinterrogé. Compteur absent, incohérent, reset ou dépassement : arrêt. Une seule tentative par tâche, pas d'appel de remplacement d'une observation invalide, pas de retry d'erreur API. Les contrôles du catalogue lors d'une **future exécution autorisée** sont gratuits ; aucun de ces contrôles réseau n'est exécuté par les tests hors ligne actuels.

La destination du staging chiffré est adaptée aux chemins Windows hors dépôt. La vérification des dates/validité de la clé principale est complétée avant utilisation ; les empreintes attendues ne changent pas. Le portage enlève l'import inconditionnel `fcntl` qui bloquait aussi le vérificateur de restauration sous Windows ; cela n'équivaut pas à un test natif réussi. L'ancien outil POSIX `phase2/archive.py`, avec son contrôle de permissions par mode Unix, n'est pas utilisé dans cette chaîne Windows : utiliser `vault.py` et les ACL décrites ci-dessous.

## Fichiers préparés

- [Common.ps1](Common.ps1) : validation de chemins absolus, état/secret hors dépôt, ACL limitées au compte courant/SYSTEM/administrateurs et chemins outils.
- [Test-Prerequisites.ps1](Test-Prerequisites.ps1) : contrôles locaux de Python, GnuPG, gh, ACL, DPAPI si configuré, état/manifeste/clé publique, fuseau et service Planificateur. **Aucun appel réseau.** Ne vérifie donc pas l'authentification réelle.
- [Set-LocalCredential.ps1](Set-LocalCredential.ps1) : saisie masquée manuelle, stockage `SecureString` protégé par DPAPI dans un fichier privé hors Git ; ne remplace pas un fichier existant.
- [tasks.py](tasks.py) : XML à date complète UTC, six tâches au maximum, dates passées non récupérables, toutes les tâches **désactivées**.
- [Install-Tasks.ps1](Install-Tasks.ps1) : génère seulement les XML par défaut ; `-RegisterDisabled` enregistre uniquement des tâches désactivées. Refuse d'écraser une tâche existante. `-WhatIf` n'écrit rien. Aucun `Enable-ScheduledTask` ni `Start-ScheduledTask`.
- [Run-Slot.ps1](Run-Slot.ps1) et [run_slot.py](run_slot.py) : adaptateur d'une seule tâche vers le runner existant. Secret seulement dans la mémoire et l'environnement du processus enfant, nettoyé en `finally`. Pas de transcript ni d'URL authentifiée dans les journaux. Les journaux locaux contiennent tâche, horodatage, statut, type d'erreur et reçu d'archive, jamais les messages d'exception ou prix.
- [Uninstall-Tasks.ps1](Uninstall-Tasks.ps1) : désactive puis retire exclusivement les six tâches nommées `PRISME-Campaign1-T1` à `T6`, sans supprimer de données, clés, manifestes ou archives. Supporte `-WhatIf`.

## Prérequis Windows et mise en place préparatoire

Windows 10/11 avec Windows PowerShell 5.1, service Planificateur actif, Python **3.12+**, GnuPG/Gpg4win et GitHub CLI. Les chemins de [config.example.json](config.example.json) sont des **exemples à adapter**, pas des logiciels détectés sur votre PC. Aucune installation logicielle ni modification de votre Windows n'a été effectuée ici.

1. Mettre à jour le clone de code public. Créer un dossier privé **hors de ce clone**, par exemple `%LOCALAPPDATA%\PRISME`, et vérifier ses ACL NTFS ainsi que celles du disque de restauration. Autoriser seulement votre compte, SYSTEM et administrateurs ; retirer les accès larges hérités si nécessaire depuis les propriétés Sécurité de ce dossier. Ne pas modifier aveuglément les ACL d'un dossier existant contenant d'autres données. Les scripts refusent des droits trop larges mais ne font pas de réécriture générale des ACL.
2. Télécharger la dernière archive de campagne depuis le dépôt **privé** `PRISME-Archives`, conserver le ciphertext et restaurer sous ce dossier privé. Archive existante : `campaign1_20261021T161135891269Z_770079b2.gpg`, SHA-256 **`07228e86cbcf047c65bcc69a0b1cfb4c9c07b9110132ab837cf4786aceea4882`**, commit privé `33e70374cd46b1f8b07a7ead3d16d37daaee8ae8`. Ne pas démarrer d'une ancienne archive qui ignorerait une réservation/capture plus récente ; vérifier l'historique privé et le dernier reçu. Le runner refuse aussi un ancien état lorsque des snapshots plus récents sont présents localement.
3. Copier le modèle de configuration vers le dossier privé, adapter tous les chemins et protéger son ACL. Ni identifiant d'événement ni cote n'est à ajouter dans cette configuration. Conserver le fichier public `.asc` hors du dépôt de données ; aucune clé privée sur le cloud ou dans Git. L'empreinte principale attendue est `5A14F786E05DFC58C886F0A8D8CAB0E82DA81776`, sous-clé de chiffrement `558B3344B7FD5DCDDF70E7C30596A55A79FBA862`.
4. Préparer l'authentification GitHub **sur Windows**, pour le même compte Windows qui exécutera les tâches (`gh auth login`, navigateur/stockage sécurisé hors dépôt). Vérifier propriétaire `Baruck1968`, `private=true`, `visibility=private`, droit `push=true` avec `gh api repos/Baruck1968/PRISME-Archives --jq '{private,visibility,permissions}'`. Cette vérification est une opération future manuelle, pas réalisée sur votre PC par cet audit. Ne pas mettre de token dans la configuration, XML, commande de tâche ou dépôt.
5. Configurer manuellement la clé gratuite via `Set-LocalCredential.ps1 -ConfigPath ...` : DPAPI lie le fichier chiffré **à votre utilisateur et à cet ordinateur**. Ne pas recopier la variable proxy du cloud. Aucun secret n'est demandé dans le chat. Après changement d'utilisateur/machine, saisir de nouveau le secret localement ; le fichier DPAPI ne constitue pas une sauvegarde portable de la clé.
6. Exécuter le contrôle **hors ligne** :

```powershell
.\research\observatoire_v1\windows\Test-Prerequisites.ps1 -ConfigPath "$env:LOCALAPPDATA\PRISME\settings.json"
```

Les fichiers privés et la clé publique doivent déjà être restaurés. Une clé DPAPI absente est signalée comme un blocage d'exécution ; le test ne l'invente pas et ne contacte pas le fournisseur.

7. Préparer les XML dans un **nouveau dossier** de sortie, sans enregistrer de tâche :

```powershell
.\research\observatoire_v1\windows\Install-Tasks.ps1 -ConfigPath "$env:LOCALAPPDATA\PRISME\settings.json" -OutputDirectory "$env:LOCALAPPDATA\PRISME\tasks-prepares-1"
```

L'option `-RegisterDisabled` est disponible pour une installation manuelle ultérieure **toujours désactivée** ; les permissions locales de création de tâches doivent alors être vérifiées sur Windows. L'utilisateur exécutant la tâche reste votre SID, niveau `LeastPrivilege`. Ne pas passer à SYSTEM ou un autre utilisateur : la clé DPAPI et l'authentification gh ne leur seraient pas nécessairement accessibles. Les commandes d'activation ne sont volontairement pas incluses dans cette préparation. **Ne pas activer les tâches à cette étape.**

8. Désinstallation ciblée, si des tâches ont été enregistrées manuellement :

```powershell
.\research\observatoire_v1\windows\Uninstall-Tasks.ps1 -WhatIf
```

Retirer `-WhatIf` réalise seulement la désinstallation des six noms fixes ; les dossiers privés ne sont pas nettoyés.

## Horloge, session, alimentation et réseau

Les XML utilisent `StartBoundary` **avec suffixe `Z`**, indépendant du fuseau local et du changement d'heure. Le Planificateur peut afficher une heure locale différente ; contrôler la valeur UTC du XML, les six dates du tableau et `Get-TimeZone`. Ne pas convertir deux fois. Vérifier la synchronisation de l'horloge Windows (`w32tm /query /status`, Paramètres Date et heure) avant les cibles ; un fuseau correct ne garantit pas une horloge exacte. Python compare exclusivement des instants UTC.

Les tâches sont une fois seulement, `StartWhenAvailable=false`, `IgnoreNew`, sans répétition ni relance sur échec, avec fin de fenêtre et limite de durée de trois minutes. Un réveil ou redémarrage tardif n'autorise aucun rattrapage : le runner recontrôle l'heure avant le seul appel. Une interruption pendant l'appel peut laisser une réservation incertaine ; elle interdit le rejeu et doit être conservée pour audit, pas effacée.

`WakeToRun=true` n'est **pas une garantie** : arrêt complet, batterie vide, veille profonde, politique interdisant les minuteurs de sortie de veille, Wi-Fi non reconnecté ou horloge incorrecte peuvent rendre le créneau absent. Maintenir le PC alimenté, en fonctionnement et connecté pendant les fenêtres ; vérifier les politiques de réveil (`powercfg /a`, `powercfg /waketimers`) et faire un essai **local sans API** après autorisation distincte. Aucune modification d'alimentation n'est exécutée ici. Pas de réveil de machine éteinte garanti.

`InteractiveToken` exige une session de votre utilisateur ouverte. L'écran peut être verrouillé, mais une déconnexion ferme cette condition ; une tâche désactivée ou une session fermée peut ne jamais démarrer. Cette limitation évite de stocker un mot de passe Windows dans la tâche. Une exécution sans session nécessiterait une autre configuration de principal/authentification, à valider séparément : elle n'est pas supposée fonctionnelle.

## Chiffrement, stockage et restauration

Après chaque relevé ou absence consignée, le runner réutilise OpenPGP, crée un nouvel état immuable, chiffre le paquet privé et transfère **uniquement le `.gpg`** vers `PRISME-Archives`. Les étapes de contrôle privé/push avant et après, SHA-256, téléchargement de retour et non-écrasement des anciennes archives sont inchangées. Une panne d'upload arrête la campagne et conserve l'état local. Aucun fichier de clé API, DPAPI, configuration gh, clé privée ou journal PowerShell n'entre dans le paquet : le chiffreur sélectionne uniquement les noms de captures/manifestes et le journal attendus.

La clé privée reste dans votre trousseau Windows et sa sauvegarde indépendante ; elle sert à restaurer, pas à chiffrer les futures captures. Utiliser le script de restauration préparé `vault/Restore-Prisme.ps1` avec le **nouveau code portable**, un dossier destination nouveau sous un parent privé et le hash ci-dessus. Il contrôle ciphertext, déchiffrement, hashes internes, journal et manifeste épinglé. Aucune restauration effective avec votre clé privée n'a été réalisée ici ; seule la restauration locale avec une clé de test temporaire a été rejouée hors ligne sur Linux. Conserver le ciphertext daté sur Windows et une copie indépendante si disponible ; ne pas supprimer les originaux avant ce test.

Le mode Unix `chmod` n'assure pas la confidentialité sous Windows : ce sont les ACL NTFS vérifiées par les scripts qui doivent protéger les parents de données, logs et staging. Les sauvegardes brutes locales déchiffrées ne doivent pas être partagées ou commitées. Les journaux de reçus sous le dossier privé parent restent à conserver pour l'audit, sans secrets.

## Résultats de tests et limites de preuve

[41 tests hors ligne réussis](validation.log), dont 10 nouveaux : XML sans activation/récurrence/rattrapage, bornes UTC et échéances expirées non récupérables, SID/arguments, six dates figées, branche `msvcrt` simulée, contention bornée, nettoyage du secret et **vrai verrou interprocessus sur Linux**, libéré après terminaison du processus. La suite conserve les tests de fenêtre, fraîcheur, seuil, quotas, rejeu, erreurs et restauration chiffrée sur les vraies données privées sans nouvelle capture.

**Non exécutés** : PowerShell natif (pas de `pwsh` ici), validation du schéma XML par le service Windows, vrai verrou interprocessus Windows, ACL/DPAPI sur votre PC, authentification Windows vers GitHub, réveil, déchiffrement avec votre clé utilisateur et relevé à une cible. Les tests Python de la branche Windows utilisent un simulacre d'API `msvcrt`, pas une certification de ces opérations natives. Le paquet PowerShell est préparé et relu, pas déclaré opérationnel. Exécuter les dix tests dédiés avec `py -3 -m unittest discover -s tests -p test_observatoire_windows.py -v` sur Windows ; les anciennes utilités POSIX non utilisées par cette chaîne ne sont pas un test d'ACL Windows.

**Conclusion de faisabilité** : un ordinateur Windows peut héberger les six exécutions ponctuelles avec ces adaptations, sous réserve de stockage NTFS privé, session ouverte, horloge/réseau/alimentation et vérification native. Rien ne garantit les six observations ; une panne restera une absence. Aucune activation n'a été effectuée et les dates ne seront pas déplacées si les prérequis sont satisfaits trop tard.
