param(
    [Parameter(Mandatory=$true)][string]$Destination,
    [string]$Wails = 'wails'
)
$ErrorActionPreference = 'Stop'
if (![IO.Path]::IsPathRooted($Destination)) { throw 'Destination must be absolute.' }
Push-Location $PSScriptRoot
try {
    if (!(Test-Path -LiteralPath 'internal/launcher/policy_qa_generated.go')) {
        throw 'Generate the signed QA bundle with cmd/nightcap-package first.'
    }
    Push-Location (Join-Path $PSScriptRoot 'frontend')
    try {
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'QA frontend build failed.' }
    } finally { Pop-Location }
    # Wails reads metadata from wails.json. Restore its exact bytes even on failure.
    # Run one build at a time in this checkout.
    $configPath = Join-Path $PSScriptRoot 'wails.json'
    $original = [IO.File]::ReadAllBytes($configPath)
    try {
        $config = [Text.Encoding]::UTF8.GetString($original) | ConvertFrom-Json
        $config.info.productName = 'Nightcap Launcher - Local QA Candidate'
        $config.info.comments = 'Signed offline QA bundle. Not a production release or gameplay acceptance.'
        [IO.File]::WriteAllText($configPath, ($config | ConvertTo-Json -Depth 10), [Text.UTF8Encoding]::new($false))
        & $Wails build -platform windows/amd64 -tags qacandidate -o nightcap-launcher-qa.exe -s -m -nosyncgomod
        if ($LASTEXITCODE -ne 0) { throw 'QA desktop build failed.' }
    } finally {
        [IO.File]::WriteAllBytes($configPath, $original)
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    Copy-Item -LiteralPath 'build/bin/nightcap-launcher-qa.exe' -Destination $Destination
    $builtHash = (Get-FileHash -Algorithm SHA256 -LiteralPath 'build/bin/nightcap-launcher-qa.exe').Hash
    $copiedHash = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Destination 'nightcap-launcher-qa.exe')).Hash
    if ($builtHash -ne $copiedHash) { throw 'Copied QA launcher hash mismatch.' }
    foreach ($name in @('manifest.json','signature.json','audit.json')) {
        Copy-Item -LiteralPath "internal/launcher/qabundle/$name" -Destination $Destination
    }
    Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $Destination 'nightcap-launcher-qa.exe') |
        Select-Object Algorithm,Hash | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $Destination 'launcher-sha256.json')
} finally {
    Pop-Location
}
