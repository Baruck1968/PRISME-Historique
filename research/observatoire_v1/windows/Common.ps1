Set-StrictMode -Version Latest
function Read-PrismeConfig([string]$Path) {
    if ($env:OS -ne 'Windows_NT') { throw 'Windows natif requis.' }
    $Config = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    foreach ($Name in @('RepoRoot','PrivateRoot','PublicKey','PythonExe','GpgExe','GhExe','ApiKeyFile')) {
        if (-not [IO.Path]::IsPathRooted([string]$Config.$Name)) { throw "Chemin absolu requis: $Name" }
    }
    $Repo = [IO.Path]::GetFullPath($Config.RepoRoot).TrimEnd('\') + '\'
    foreach ($Value in @($Path,$Config.PrivateRoot,$Config.ApiKeyFile)) {
        $Full = [IO.Path]::GetFullPath($Value)
        if (($Full.TrimEnd('\') -eq $Repo.TrimEnd('\')) -or $Full.StartsWith($Repo,[StringComparison]::OrdinalIgnoreCase)) { throw 'Etat et secrets doivent rester hors du depot de code.' }
    }
    foreach ($Value in @($Config.PythonExe,$Config.GpgExe,$Config.GhExe,$Config.PublicKey,$Config.PrivateRoot)) {
        if (-not (Test-Path -LiteralPath $Value)) { throw 'Prerequis local manquant.' }
    }
    return $Config
}
function Assert-PrismePrivateAcl([string]$Path) {
    $Acl = Get-Acl -LiteralPath $Path
    $Broad = @('S-1-1-0','S-1-5-11','S-1-5-32-545') # Everyone, authenticated users, Users
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    foreach ($Rule in $Acl.Access) {
        if ($Rule.AccessControlType -eq 'Allow') {
            $Sid = $Rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
            if (($Broad -contains $Sid) -or (@($Identity,'S-1-5-18','S-1-5-32-544') -notcontains $Sid)) {
                throw 'ACL trop large : acces reserve au proprietaire, SYSTEM et administrateurs.'
            }
        }
    }
}
function Set-PrismeToolPath($Config) {
    $env:PATH = (Split-Path -Parent $Config.GpgExe) + ';' + (Split-Path -Parent $Config.GhExe) + ';' + $env:PATH
}
