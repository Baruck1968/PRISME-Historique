# Archive initiale chiffrée — transfert privé vérifié

21 octobre 2026. Exécution de la procédure préparée au commit `2a07c07`, après fourniture de la clé publique utilisateur. **Archive de production chiffrée et transférée ; intégrité du transfert vérifiée.** Aucun nouveau relevé de cotes, aucune programmation, aucun achat ou opération financière.

## Vérifications préalables

Le fichier fourni `PRISME-public.asc` a été inspecté dans un trousseau GnuPG temporaire. Il contient une clé publique principale et une sous-clé de chiffrement. Aucune instruction contenue dans le document n'a été exécutée ; seul son contenu cryptographique a été traité.

- Empreinte principale constatée et conforme à la valeur attendue : **`5A14F786E05DFC58C886F0A8D8CAB0E82DA81776`**.
- Sous-clé de chiffrement : **`558B3344B7FD5DCDDF70E7C30596A55A79FBA862`**, capacité `e`, algorithme OpenPGP 18 (ECDH). Clé principale algorithme 22 (EdDSA).
- Dates de création antérieures à l'opération et expiration postérieure ; pas d'indicateur de révocation/expiration/désactivation dans la clé fournie. Cette vérification porte sur le fichier reçu, sans consultation d'un serveur de révocations.
- L'API confirme propriétaire `Baruck1968`, dépôt `PRISME-Archives`, `private=true`, `visibility=private` et permission `push=true`, avant chiffrement/transfert puis à nouveau juste avant transfert.
- Le manifeste prospectif original est présent et son SHA-256 correspond à l'empreinte épinglée dans `vault.py`.

## Chiffrement et contenu protégé

`vault.py` existant a été utilisé sans modification, avec la clé publique reçue et l'empreinte principale complète comme destinataire. Il a vérifié les noms des fichiers, la chaîne du journal, les empreintes des captures et celle du manifeste avant de former le paquet en mémoire et de le chiffrer. Aucun mot de passe, clé privée ou jeton n'a été nécessaire dans l'archive ou un dépôt.

Le contenu chiffré conserve les quatre fichiers utiles de l'état privé : les deux enveloppes de tentative/capture (échec initial et capture réussie), le journal et le manifeste initial, plus l'inventaire interne SHA-256. La capture réussie contient les identifiants, cotes et horodatages réels déjà conservés. Le `.lock` de fonctionnement n'est pas archivé. Les observations brutes restent exclusivement dans le paquet chiffré et dans les copies privées locales ; elles ne sont pas ajoutées au dépôt de code public.

Le manifeste reste celui du 21 octobre à `15:17:28.264762 UTC`, avec ses échéances initiales :

`627d076a2a2f161942254d83f83751416e41ed18e54869d621f920838739031d`

Aucun remplacement de J−1 manquant par la découverte, aucune nouvelle inscription ni changement de cible. L'archivage ne crée aucune nouvelle observation.

## Transfert et contrôle de retour

| Élément | Résultat |
|---|---|
| Dépôt destinataire | `Baruck1968/PRISME-Archives`, privé |
| Unique fichier transféré | `prisme-20261021-initial.gpg` |
| Taille du ciphertext | 35 317 octets |
| Commit dans le dépôt privé | `de09b355711a9a7e8d7547f5b54a2220db52a2ea` |
| SHA-256 | `033c900f87f524bfe63421ef5d687f935f781ffa8cb33ce8c548cdd13e91011e` |
| Contrôle distant | Fichier retéléchargé depuis ce commit, identique octet pour octet au ciphertext local |
| Visibilité après transfert | `private=true`, `visibility=private` |
| Liste des modifications du commit | Uniquement le fichier `.gpg` |

Conformément à la dernière instruction, **aucun fichier `.sha256` n'a été transféré dans PRISME-Archives** : son empreinte est ancrée dans ce rapport expurgé et dans [production_verification_2026-10-21.json](production_verification_2026-10-21.json). Le petit fichier de hash produit localement par l'outil reste hors des dépôts. La clé publique elle-même n'a pas été transférée dans les dépôts. Ni archive ZIP en clair, ni clé API, ni trousseau, ni phrase secrète, ni token d'authentification n'a été envoyé.

La copie vérifiée retéléchargée est conservée dans `/workspace/prisme-encrypted-staging/download-verified/`, en plus du ciphertext original hors dépôt et des fichiers privés préservés. Ces copies locales ne remplacent pas la seconde copie Windows.

## Restauration Windows à effectuer

Le contrôle du transfert porte sur le ciphertext. Le cloud ne détient pas votre clé privée et n'a donc pas déchiffré **cette archive de production**. Le test local précédent de chiffrement/restauration utilisait une clé de test distincte. La restauration complète avec votre vraie clé et la sauvegarde sur votre ordinateur restent **non exécutées** tant que vous ne les avez pas réalisées sur Windows.

1. Depuis votre session GitHub authentifiée, télécharger le fichier `.gpg` du dépôt privé au commit ci-dessus vers un dossier privé sur votre ordinateur, par exemple `D:\PRISME-Backup\`. Ne pas utiliser un artifact temporaire. Conserver une seconde copie datée sur un support indépendant si disponible, et conserver la clé privée de récupération séparément.
2. Vérifier le fichier téléchargé :

```powershell
Get-FileHash -Algorithm SHA256 -LiteralPath 'D:\PRISME-Backup\prisme-20261021-initial.gpg'
```

La valeur attendue est **`033c900f87f524bfe63421ef5d687f935f781ffa8cb33ce8c548cdd13e91011e`**.

3. Avec GnuPG/Gpg4win, Python 3 et le code `PRISME-Historique` à jour, lancer depuis la racine de ce dépôt :

```powershell
.\research\observatoire_v1\vault\Restore-Prisme.ps1 -ArchivePath 'D:\PRISME-Backup\prisme-20261021-initial.gpg' -ExpectedSha256 '033c900f87f524bfe63421ef5d687f935f781ffa8cb33ce8c548cdd13e91011e' -Destination 'D:\PRISME-Restauration\initial-20261021'
```

Le dossier destination doit être nouveau et privé. GnuPG demandera votre phrase secrète localement si nécessaire : ne jamais la mettre dans la commande, un dépôt ou une conversation. Le script vérifie le hash du ciphertext, le succès du déchiffrement, l'inventaire interne, les deux entrées de capture du journal et le manifeste épinglé. La sortie attendue du vérificateur indique `restored_files=4`, `verified_captures=2` et le SHA-256 du manifeste initial. Un succès sera la preuve d'une restauration effective sur Windows ; ne pas l'annoncer avant ce test.

4. Conserver l'archive chiffrée et le hash dans votre sauvegarde Windows datée. Ne pas commiter les observations déchiffrées. La clé privée reste dans votre trousseau Windows et sa copie de récupération protégée ; ne pas la conserver dans PRISME-Archives. Ne pas supprimer les originaux cloud avant restauration Windows confirmée.

Le dépôt privé est une conservation temporaire versionnée, pas une garantie de sauvegarde inviolable. Sa confidentialité future dépend du maintien de sa visibilité et de ses droits. Aucun changement de collecte ni de surveillance n'est inclus dans cette opération.
