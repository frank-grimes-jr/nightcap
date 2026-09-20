param(
    [Parameter(Mandatory=$true)][string]$Destination,
    [Parameter(Mandatory=$true)][string]$Profile,
    [string]$Wails = 'wails'
)
$ErrorActionPreference = 'Stop'
if (![IO.Path]::IsPathRooted($Destination)) { throw 'Destination must be absolute.' }
if (Test-Path -LiteralPath $Destination) { throw 'Use a new destination for each release.' }
Push-Location $PSScriptRoot
try {
    if (!(Test-Path -LiteralPath 'internal/launcher/policy_production_generated.go')) {
        throw 'Generate production trust and hosted files with nightcap-package first.'
    }
    $profileData = Get-Content -Raw -LiteralPath $Profile | ConvertFrom-Json
    # Confirm profile/compiled policy agreement instead of silently mislabeling a binary.
    $policy = Get-Content -Raw -LiteralPath 'internal/launcher/policy_production_generated.go'
    foreach ($value in @(($profileData.base_url + '/channel.json'), $profileData.relay_url, $profileData.guide_url, $profileData.version)) {
        if (!$policy.Contains('"' + $value + '"')) { throw 'Profile does not match the generated production policy.' }
    }
    Push-Location frontend
    try {
        & npm.cmd audit --audit-level=high
        if ($LASTEXITCODE -ne 0) { throw 'Dependency audit needs review before release.' }
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
    $configPath = Join-Path $PSScriptRoot 'wails.json'
    $original = [IO.File]::ReadAllBytes($configPath)
    try {
        $config = [Text.Encoding]::UTF8.GetString($original) | ConvertFrom-Json
        $config.info.productName = 'Nightcap Launcher'
        $config.info.productVersion = $profileData.version
        $config.info.comments = 'Private Nightcap launcher with signed updates and encrypted game transport.'
        [IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
        & $Wails build -platform windows/amd64 -tags production -o nightcap-launcher.exe -s -m -nosyncgomod
        if ($LASTEXITCODE -ne 0) { throw 'Production desktop build failed.' }
    } finally { [IO.File]::WriteAllBytes($configPath, $original) }
    New-Item -ItemType Directory -Path $Destination | Out-Null
    Copy-Item -LiteralPath 'build/bin/nightcap-launcher.exe' -Destination $Destination
    Copy-Item -LiteralPath '../deploy/production/FRIENDS.txt' -Destination $Destination
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Destination 'nightcap-launcher.exe')).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText((Join-Path $Destination 'SHA256SUMS.txt'), "$hash  nightcap-launcher.exe`n", [Text.UTF8Encoding]::new($false))
    [IO.File]::WriteAllText((Join-Path $Destination 'SERVER.txt'), "Guide: $($profileData.guide_url)`n", [Text.UTF8Encoding]::new($false))
    Compress-Archive -LiteralPath @((Join-Path $Destination 'nightcap-launcher.exe'),(Join-Path $Destination 'FRIENDS.txt'),(Join-Path $Destination 'SHA256SUMS.txt'),(Join-Path $Destination 'SERVER.txt')) -DestinationPath (Join-Path $Destination 'nightcap-friends.zip')
} finally { Pop-Location }
