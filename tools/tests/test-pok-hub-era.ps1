$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot '..\pok-hub-era.ps1')
$policy = Join-Path $PSScriptRoot '..\..\docs\pok\catalog-policy.json'
$script:counts = "16`t1747"
$script:identities = '16'
$read = { param($query) if ($query.StartsWith('SELECT (SELECT')) { $script:counts } else { $script:identities } }
Assert-PokHubEra -Era @{expansion=0;max_level=50} -ReadSql $read -PolicyPath $policy
Assert-PokHubEra -Era @{expansion=0;max_level=10} -ReadSql $read -PolicyPath $policy
$rejected = 0
foreach ($era in @(@{expansion=1;max_level=50},@{expansion=0;max_level=60})) {
    try { Assert-PokHubEra -Era $era -ReadSql $read -PolicyPath $policy } catch { $rejected++ }
}
foreach ($counts in @("1`t0", "0`t1", 'invalid')) {
    $script:counts = $counts
    try { Assert-PokHubEra -Era @{expansion=0;max_level=50} -ReadSql $read -PolicyPath $policy } catch { $rejected++ }
}
$script:counts = "16`t1747"
$script:identities = '15'
try { Assert-PokHubEra -Era @{expansion=0;max_level=50} -ReadSql $read -PolicyPath $policy } catch { $rejected++ }
if ($rejected -ne 6) { throw "Expected six rejected era preflights, got $rejected" }
$script:counts = "0`t0"
Assert-PokHubEra -Era @{expansion=1;max_level=60} -ReadSql $read -PolicyPath $policy
$source = Get-Content (Join-Path $PSScriptRoot '..\apply-era.ps1') -Raw
$guardPosition = $source.IndexOf('Assert-PokHubEra -Era')
$writePosition = $source.IndexOf('Sql "UPDATE rule_values')
if ($guardPosition -lt 0 -or $writePosition -lt 0 -or $guardPosition -gt $writePosition) { throw 'Preflight must exist and precede era writes.' }
Write-Output 'PASS: valid hub and legacy paths; six invalid preflights rejected before era changes.'

# Execute the real script with only its root redirected to a disposable fixture.
# A Continue caller must not let missing files fall through to external commands.
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('nightcap-era-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path (Join-Path $fixture 'eq-solo-gm\scripts') -Force | Out-Null
Set-Content -LiteralPath (Join-Path $fixture 'era.json') -Value '{"name":"QA","expansion":0,"max_level":50,"aa_open":true,"luclin_models":false}'
$redirected = $source.Replace("'E:\EQ_Local_Dev'", "'" + $fixture.Replace("'","''") + "'")
$testScript = Join-Path $fixture 'apply-era.ps1'
Set-Content -LiteralPath $testScript -Value $redirected
$script:externalCalls = 0
function docker { $script:externalCalls++; throw 'Unexpected external command from a missing-file test.' }
$errors = 0
$ErrorActionPreference = 'Continue'
try { & $testScript } catch { $errors++ }
Set-Content -LiteralPath (Join-Path $fixture 'eq-solo-gm\scripts\vendor_restock.sql') -Value 'SELECT 1;'
try { & $testScript } catch { $errors++ }
$ErrorActionPreference = 'Stop'
if ($errors -ne 2 -or $script:externalCalls -ne 0) { throw 'Missing era inputs or guard did not stop before external commands.' }
Write-Output 'PASS: missing restock and missing guard stop before any external command, even with a Continue caller.'
