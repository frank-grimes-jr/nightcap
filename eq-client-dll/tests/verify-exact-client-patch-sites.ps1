param(
	[string]$EqgamePath = (Join-Path $PSScriptRoot '..\..\Client_RoF2_Dev\everquest_rof2\eqgame.exe')
)

$ErrorActionPreference = 'Stop'
$expectedSize = 8774656
$expectedSha256 = '2A8702AD9F722704F01355C0750BE7D6F164A8B9C9128BA0CF286EA32B405B0E'
$imageBase = 0x00400000
$textRva = 0x00001000
$textFileOffset = 0x00000400

function Assert-Bytes {
	param(
		[byte[]]$Image,
		[uint32]$Rva,
		[byte[]]$Expected,
		[string]$Label
	)

	$fileOffset = $textFileOffset + ($Rva - $textRva)
	for ($i = 0; $i -lt $Expected.Length; $i++) {
		if ($Image[$fileOffset + $i] -ne $Expected[$i]) {
			throw ('{0} signature mismatch at RVA 0x{1:X8} byte {2}' -f $Label, $Rva, $i)
		}
	}
}

$resolvedPath = (Resolve-Path -LiteralPath $EqgamePath).Path
$file = Get-Item -LiteralPath $resolvedPath
if ($file.Length -ne $expectedSize) {
	throw "eqgame.exe size mismatch: expected $expectedSize, got $($file.Length)"
}

$sha256 = (Get-FileHash -LiteralPath $resolvedPath -Algorithm SHA256).Hash
if ($sha256 -ne $expectedSha256) {
	throw "eqgame.exe SHA-256 mismatch: expected $expectedSha256, got $sha256"
}

$image = [System.IO.File]::ReadAllBytes($resolvedPath)
Assert-Bytes $image 0x00043F90 ([byte[]](0,1,1,1,1,1,0,1,0,1,1,1,1,1,1,0)) 'caster table'
Assert-Bytes $image 0x00181E96 ([byte[]](0x33,0xC0,0x5E,0xC2,0x04,0x00)) 'Max_Mana return'
Assert-Bytes $image 0x00318E93 ([byte[]](0xE8,0xF8,0x6C,0xE8,0xFF)) 'CPlayerWnd mana predicate call'

$callFileOffset = $textFileOffset + (0x00318E93 - $textRva)
$relative = [BitConverter]::ToInt32($image, $callFileOffset + 1)
$callTarget = $imageBase + 0x00318E93 + 5 + $relative
if ($callTarget -ne 0x0059FB90) {
	throw ('CPlayerWnd mana predicate call target mismatch: expected 0x0059FB90, got 0x{0:X8}' -f $callTarget)
}

Write-Output 'PASS: exact RoF2 client and all guarded B2 patch sites verified.'
