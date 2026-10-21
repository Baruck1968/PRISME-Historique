# Manual secure input on Windows only. No credential is accepted in arguments.
param([Parameter(Mandatory=$true)][string]$ConfigPath)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$Config = Read-PrismeConfig $ConfigPath
$Folder = Split-Path -Parent $Config.ApiKeyFile
Assert-PrismePrivateAcl $Folder
if (Test-Path -LiteralPath $Config.ApiKeyFile) { throw 'Fichier existant : remplacement manuel explicite requis.' }
$Secret = Read-Host 'Cle gratuite The Odds API (saisie masquee)' -AsSecureString
if ($Secret.Length -eq 0) { throw 'Cle vide refusee.' }
# On Windows Export-Clixml protects SecureString using current-user DPAPI.
$Secret | Export-Clixml -LiteralPath $Config.ApiKeyFile
Assert-PrismePrivateAcl $Config.ApiKeyFile
Write-Output 'Secret DPAPI enregistre hors depot pour cet utilisateur et cet ordinateur.'
