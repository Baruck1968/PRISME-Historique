# Manual operation only. Requires Python 3 and GnuPG; no API calls or scheduling.
param(
    [Parameter(Mandatory=$true)][string]$ArchivePath,
    [Parameter(Mandatory=$true)][ValidatePattern('^[a-fA-F0-9]{64}$')][string]$ExpectedSha256,
    [Parameter(Mandatory=$true)][string]$Destination
)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Destination) { throw 'Le dossier de restauration doit etre nouveau.' }
$Actual = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash
if ($Actual -ne $ExpectedSha256) { throw 'Empreinte de l archive chiffree incorrecte.' }
$Work = Join-Path $env:LOCALAPPDATA ('PRISME\restore-work\' + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $Work | Out-Null
$PlainZip = Join-Path $Work 'snapshot.zip'
try {
    & gpg --output $PlainZip --decrypt $ArchivePath
    if ($LASTEXITCODE -ne 0) { throw 'Echec du dechiffrement; aucune restauration acceptee.' }
    & py -3 (Join-Path $PSScriptRoot 'vault.py') restore $PlainZip $Destination
    if ($LASTEXITCODE -ne 0) { throw 'Echec des controles internes SHA-256 / manifeste / journal.' }
    Write-Output 'Archive restauree et empreintes internes verifiees.'
} finally {
    # Remove only temporary plaintext created by this script, never the original archive.
    if (Test-Path -LiteralPath $PlainZip) { Remove-Item -LiteralPath $PlainZip -Force }
    if (Test-Path -LiteralPath $Work) { Remove-Item -LiteralPath $Work }
}
