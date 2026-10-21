# Prepares/registers DISABLED one-time tasks only. It cannot activate them.
[CmdletBinding(SupportsShouldProcess=$true)]
param([Parameter(Mandatory=$true)][string]$ConfigPath,
      [Parameter(Mandatory=$true)][string]$OutputDirectory,
      [switch]$RegisterDisabled)
$ErrorActionPreference = 'Stop'
if ($WhatIfPreference) { Write-Output 'Simulation : aucun fichier ni tache cree.'; return }
. (Join-Path $PSScriptRoot 'Common.ps1')
$Config = Read-PrismeConfig $ConfigPath
Assert-PrismePrivateAcl $ConfigPath
Assert-PrismePrivateAcl $Config.PrivateRoot
$Sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$Manifest = Join-Path $Config.RepoRoot 'research\observatoire_v1\campaign1\manifest_redacted.json'
$Runner = Join-Path $PSScriptRoot 'Run-Slot.ps1'
& $Config.PythonExe (Join-Path $PSScriptRoot 'tasks.py') --manifest $Manifest --config $ConfigPath --runner $Runner --sid $Sid --output $OutputDirectory
if ($LASTEXITCODE -ne 0) { throw 'Echec de preparation XML; aucune activation.' }
$Rows = Get-Content -LiteralPath (Join-Path $OutputDirectory 'preparation.json') -Raw | ConvertFrom-Json
foreach ($Row in $Rows) {
    if ($Row.status -eq 'non_recoverable') { Write-Output ($Row.id + ': echeance non recuperable'); continue }
    if (-not $RegisterDisabled) { continue }
    $Name = 'PRISME-Campaign1-' + $Row.id
    if (Get-ScheduledTask -TaskName $Name -TaskPath '\' -ErrorAction SilentlyContinue) { throw 'Tache existante : aucun ecrasement autorise.' }
    if ($PSCmdlet.ShouldProcess($Name,'Enregistrer une tache DESACTIVEE')) {
        $Xml = Get-Content -LiteralPath (Join-Path $OutputDirectory ($Name + '.xml')) -Raw
        [xml]$Parsed = $Xml
        if ($Parsed.Task.Settings.Enabled -ne 'false') { throw 'XML non desactive refuse.' }
        Register-ScheduledTask -TaskName $Name -TaskPath '\' -Xml $Xml | Out-Null
        $Task = Get-ScheduledTask -TaskName $Name -TaskPath '\'
        if ($Task.Settings.Enabled) { Disable-ScheduledTask -TaskName $Name -TaskPath '\' | Out-Null; throw 'Etat inattendu : tache desactivee par securite.' }
    }
}
Write-Output 'Preparation terminee : aucune tache activee ni lancee.'
