param([Parameter(Mandatory=$true)][string]$ConfigPath,
      [Parameter(Mandatory=$true)][ValidateSet('T1','T2','T3','T4','T5','T6')][string]$TaskId)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
$Config = Read-PrismeConfig $ConfigPath
foreach ($Path in @($ConfigPath,$Config.PrivateRoot,$Config.ApiKeyFile)) { Assert-PrismePrivateAcl $Path }
Assert-PrismePrivateAcl (Split-Path -Parent $Config.PrivateRoot)
Set-PrismeToolPath $Config
$Secure = Import-Clixml -LiteralPath $Config.ApiKeyFile
if ($Secure -isnot [Security.SecureString]) { throw 'Secret DPAPI invalide.' }
$Pointer = [IntPtr]::Zero
$ExitStatus = 1
try {
    $Pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Secure)
    $env:THE_ODDS_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Pointer)
    # No transcript, token output or raw response log. Python emits safe status only.
    & $Config.PythonExe (Join-Path $Config.RepoRoot 'research\observatoire_v1\windows\run_slot.py') --config $ConfigPath --task $TaskId
    $ExitStatus = $LASTEXITCODE
} finally {
    Remove-Item Env:THE_ODDS_API_KEY -ErrorAction SilentlyContinue
    if ($Pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Pointer) }
}
exit $ExitStatus
