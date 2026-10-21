param([Parameter(Mandatory=$true)][string]$ConfigPath)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$Config = Read-PrismeConfig $ConfigPath
Assert-PrismePrivateAcl $ConfigPath
Assert-PrismePrivateAcl $Config.PrivateRoot
Assert-PrismePrivateAcl (Join-Path $Config.PrivateRoot 'journal.jsonl')
Assert-PrismePrivateAcl (Split-Path -Parent $Config.PrivateRoot)
Set-PrismeToolPath $Config
& $Config.PythonExe -c 'import sys; assert sys.version_info >= (3,12); import msvcrt'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ et verrou Windows requis.' }
& $Config.GpgExe --version | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw 'GnuPG indisponible.' }
& $Config.GhExe --version | Select-Object -First 1
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI indisponible.' }
& $Config.PythonExe (Join-Path $Config.RepoRoot 'research\observatoire_v1\windows\offline_check.py') --private-root $Config.PrivateRoot --public-key $Config.PublicKey
if ($LASTEXITCODE -ne 0) { throw 'Verification privee hors ligne en echec.' }
Get-TimeZone | Select-Object Id
$Scheduler = Get-Service -Name Schedule
if ($Scheduler.Status -ne 'Running') { throw 'Service Planificateur de taches arrete.' }
$Scheduler | Select-Object Name,Status
if (Test-Path -LiteralPath $Config.ApiKeyFile) {
    Assert-PrismePrivateAcl $Config.ApiKeyFile
    $Secure = Import-Clixml -LiteralPath $Config.ApiKeyFile
    if ($Secure -isnot [Security.SecureString]) { throw 'Secret DPAPI incorrect.' }
} else { Write-Warning 'Cle locale absente : execution impossible, preparation seulement.' }
Write-Output 'Hors ligne uniquement : acces GitHub, API, reveil et restauration Windows non prouves.'
