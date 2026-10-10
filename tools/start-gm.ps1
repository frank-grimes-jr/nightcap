param([switch]$EnableProductionWrites, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path $PSScriptRoot -Parent
$gmRoot = Join-Path $repoRoot 'eq-solo-gm'
$logRoot = Join-Path $repoRoot 'artifacts\gm-runtime'
$url = 'http://127.0.0.1:3001/accounts?target=production'
$productionWritesActive = $false
Push-Location $gmRoot
try {
    $node = (Get-Command node -ErrorAction Stop).Source
    if ($EnableProductionWrites) {
        git -C $repoRoot merge-base --is-ancestor HEAD origin/main
        if ($LASTEXITCODE -ne 0) { throw 'Production changes require the reviewed GM release to be promoted to main first.' }
    }
    $listening = Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 3001 -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        $ownerProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($listening[0].OwningProcess)"
        $expected = Join-Path $gmRoot 'api\server.cjs'
        if (-not $ownerProcess.CommandLine.Contains($expected)) { throw 'Port 3001 is used by another application. Close it before opening Nightcap GM.' }
        $session = Invoke-RestMethod 'http://127.0.0.1:3001/api/session' -Headers @{ 'X-Nightcap-Owner' = '1' } -TimeoutSec 5
        # This is local process configuration; opening the UI must not depend on
        # OVH/SSH/DB availability, especially when the owner needs recovery tools.
        $productionWritesActive = $session.production_writes_enabled -eq $true
        if ($EnableProductionWrites -and -not $productionWritesActive) { throw 'A read-only GM preview is already running. Close that process before enabling production changes.' }
    } else {
        if (-not (Test-Path -LiteralPath (Join-Path $gmRoot 'node_modules'))) {
            npm ci --ignore-scripts
            if ($LASTEXITCODE -ne 0) { throw 'GM dependency installation failed.' }
        }
        npm run build
        if ($LASTEXITCODE -ne 0) { throw 'GM build failed.' }
        New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
        $env:NIGHTCAP_GM_PRODUCTION_WRITES = if ($EnableProductionWrites) { '1' } else { '0' }
        $productionWritesActive = $EnableProductionWrites.IsPresent
        $serverPath = Join-Path $gmRoot 'api\server.cjs'
        $process = Start-Process -FilePath $node -ArgumentList ('"' + $serverPath + '"') -WorkingDirectory $gmRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'stdout.log') -RedirectStandardError (Join-Path $logRoot 'stderr.log')
        $ready = $false
        for ($attempt = 0; $attempt -lt 30; $attempt++) {
            try {
                $session = Invoke-RestMethod 'http://127.0.0.1:3001/api/session' -Headers @{ 'X-Nightcap-Owner' = '1' } -TimeoutSec 2
                if ($session.environments.Count -eq 2) { $ready = $true; break }
            } catch { Start-Sleep -Milliseconds 500 }
            if ($process.HasExited) { break }
        }
        if (-not $ready) { throw "GM did not start. See $logRoot\stderr.log." }
        Set-Content -LiteralPath (Join-Path $logRoot 'process-id.txt') -Value $process.Id
    }
    if (-not $NoBrowser) { Start-Process $url }
    Write-Output "Nightcap GM ready: $url"
    if ($productionWritesActive) { Write-Output 'Approved production GM changes are enabled.' }
    else { Write-Output 'Production is read-only until the reviewed release is approved.' }
} finally { Pop-Location }
