# Read-only guard used before apply-era changes any rules, characters, or client settings.
function Assert-PokHubEra {
    param(
        [Parameter(Mandatory)]$Era,
        [Parameter(Mandatory)][scriptblock]$ReadSql,
        [string]$PolicyPath = (Join-Path $PSScriptRoot '..\docs\pok\catalog-policy.json')
    )
    $counts = @(& $ReadSql 'SELECT (SELECT COUNT(*) FROM npc_types WHERE id BETWEEN 997900 AND 997915 OR merchant_id BETWEEN 99300 AND 99315), (SELECT COUNT(*) FROM merchantlist WHERE merchantid BETWEEN 99300 AND 99315);')
    if ($counts.Count -ne 1 -or $counts[0] -notmatch '^\d+\s+\d+$') {
        throw 'Unable to verify PoK arrival-hub state before era apply.'
    }
    $parts = $counts[0] -split '\s+'
    if ([int]$parts[0] -eq 0 -and [int]$parts[1] -eq 0) { return }
    if ([int]$parts[0] -ne 16) { throw 'Incomplete or conflicting PoK arrival hub; era apply stopped before changes.' }
    $policy = Get-Content -LiteralPath $PolicyPath -Raw | ConvertFrom-Json
    if ($Era.expansion -ne $policy.expansion -or $Era.max_level -lt 1 -or $Era.max_level -gt $policy.max_level) {
        throw 'Review and extend the PoK class merchant catalog for this expansion before applying the era.'
    }
    $identities = @($policy.merchants | ForEach-Object {
        $merchantName = $_.name -replace "'", "''"
        "(id=$([int]$_.npc_id) AND merchant_id=$([int]$_.merchant_id) AND class=41 AND BINARY name=BINARY '$merchantName')"
    }) -join ' OR '
    $matching = @(& $ReadSql "SELECT COUNT(*) FROM npc_types WHERE $identities;")
    if ($matching.Count -ne 1 -or $matching[0] -ne '16') {
        throw 'PoK class merchant identities changed; era apply stopped before changes.'
    }
}
