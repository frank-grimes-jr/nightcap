[CmdletBinding()]
param()
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$aa = Get-Content -Raw (Join-Path $repoRoot 'server-mods/code/zone/aa.cpp')
$plugin = Get-Content -Raw (Join-Path $repoRoot 'server-mods/plugins/multiclass.pl')
$process = Get-Content -Raw (Join-Path $repoRoot 'server-mods/code/zone/client_process.cpp')
$lua = Get-Content -Raw (Join-Path $repoRoot 'server-mods/code/zone/lua_client.cpp')
$release = $aa.Substring($aa.IndexOf('bool Client::ReleaseMulticlassSlot('))
$release = $release.Substring(0, $release.IndexOf('void Client::PurgeAfterClassRelease('))
if ($release -match '(?m)^\s*(LoadMulticlassMask|SetSkill|SaveAA|Save)\(') { throw 'Release must not perform independent writes or reload classes' }
if ($release.IndexOf('PersistEarnedAAState(') -gt $release.IndexOf('SendClearPlayerAA();')) { throw 'Publication must follow persistence' }
$revoke = $plugin.Substring($plugin.IndexOf('sub mc_revoke_slot'))
if ($revoke -match 'UPDATE|INSERT|DELETE|PurgeAfterClassRelease') { throw 'Quest must not bypass native release' }
if ($revoke -notmatch 'ReleaseMulticlassSlot') { throw 'Native release binding missing' }
if ([regex]::Matches($process,'if \(!m_multiclass_state_valid\) \{ OnDisconnect\(true\); return false; \}').Count -ne 2) { throw 'Invalid class state must terminate at entry and after packet handling' }
if ($lua -match 'SetMulticlassSlot\(static_cast<uint8>') { throw 'Lua must validate signed values before narrowing' }
'PASS: atomic class release architecture guards; native behavior is verified by the clone controls'
