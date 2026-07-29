[CmdletBinding()]
param(
	[string]$Source
)

$ErrorActionPreference = "Stop"
if (-not $Source) {
	$Source = Join-Path $PSScriptRoot "..\..\server-mods\quests\global\global_player.lua"
}

$content = [System.IO.File]::ReadAllText([System.IO.Path]::GetFullPath($Source))
$eventConnect = [regex]::Match(
	$content,
	"function event_connect\(e\)(?<body>.*?)\r?\nend",
	[System.Text.RegularExpressions.RegexOptions]::Singleline
)

if (-not $eventConnect.Success) {
	throw "Could not locate event_connect in global_player.lua."
}

$body = $eventConnect.Groups["body"].Value
foreach ($fragment in @("e.self:GetClass2()", "e.self:GetClass3()")) {
	if (-not $body.Contains($fragment)) {
		throw "Login banner is missing canonical class accessor: $fragment"
	}
}

foreach ($legacyGlobal in @('qg["mc_class2"]', 'qg["mc_class3"]')) {
	if ($body.Contains($legacyGlobal)) {
		throw "Login banner still reads obsolete quest global: $legacyGlobal"
	}
}

Write-Host "Multiclass login banner uses the canonical loaded class slots."
