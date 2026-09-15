# Static regression for the production multiclass adoption plugin.

[CmdletBinding()]
param(
    [string]$PluginPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if (-not $PluginPath) {
    $PluginPath = Join-Path $PSScriptRoot '..\server-mods\plugins\multiclass.pl'
}

$content = Get-Content -LiteralPath $PluginPath -Raw
$violations = [System.Collections.Generic.List[string]]::new()

if ($content -match '\bsub\s+mc_train_skills\b') {
    $violations.Add('legacy mc_train_skills helper is defined')
}
if ($content -match '->SetSkill\s*\(') {
    $violations.Add('production adoption directly writes a skill value')
}

if ($violations.Count -gt 0) {
    throw "Multiclass skill policy violation in ${PluginPath}: $($violations -join '; ')"
}

Write-Output "OK: $PluginPath does not maximize or directly seed skills."
