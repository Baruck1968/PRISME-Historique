[CmdletBinding(SupportsShouldProcess=$true)]
param()
$ErrorActionPreference = 'Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Windows requis.' }
foreach ($Id in @('T1','T2','T3','T4','T5','T6')) {
    $Name = 'PRISME-Campaign1-' + $Id
    $Task = Get-ScheduledTask -TaskName $Name -TaskPath '\' -ErrorAction SilentlyContinue
    if ($Task -and $PSCmdlet.ShouldProcess($Name,'Supprimer uniquement ce declencheur de campagne')) {
        Disable-ScheduledTask -TaskName $Name -TaskPath '\' | Out-Null
        Unregister-ScheduledTask -TaskName $Name -TaskPath '\' -Confirm:$false
    }
}
Write-Output 'Donnees, manifestes, archives et journaux conserves.'
