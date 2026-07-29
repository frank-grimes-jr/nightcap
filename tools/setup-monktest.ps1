# Creates or retires the authorized Epic #10 Monk combat QA character.
# Apply copies a complete source character through EQEmu's transactional
# character-copy path, then atomically installs the exact QA identity/classes
# and current-cap skills. Rollback uses EQEmu's recoverable soft-delete shape.

[CmdletBinding()]
param(
	[ValidateSet("Check", "Apply", "Rollback")]
	[string]$Mode = "Check",
	[string]$SourceCharacter = "Darth",
	[string]$DestinationCharacter = "Monktest",
	[string]$DestinationAccount = "admin",
	[string]$DatabaseContainer = "akk-stack-mariadb-1",
	[string]$ServerContainer = "akk-stack-eqemu-server-1",
	[string]$DatabaseName = "peq",
	[string]$DatabaseUser = "eqemu",
	[string]$DatabasePassword = "eqemu",
	[int]$ExpectedSourceId = 2,
	[int]$ExpectedAccountId = 12,
	[int]$ExpectedSkillCount = 60
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

foreach ($value in @(
	$SourceCharacter,
	$DestinationCharacter,
	$DestinationAccount,
	$DatabaseContainer,
	$ServerContainer,
	$DatabaseName,
	$DatabaseUser,
	$DatabasePassword
)) {
	if ($value -notmatch "^[A-Za-z0-9_.-]+$") {
		throw "Unsafe QA fixture argument: $value"
	}
}

if (
	$ExpectedSourceId -le 0 -or
	$ExpectedAccountId -le 0 -or
	$ExpectedSkillCount -le 0
) {
	throw "Expected source, account, and skill counts must be positive."
}

function Invoke-MySql([string]$Sql) {
	$output = @(
		& docker exec $DatabaseContainer mysql `
			"-u$DatabaseUser" "-p$DatabasePassword" $DatabaseName `
			--batch --raw --skip-column-names -e $Sql 2>&1
	)

	if ($LASTEXITCODE -ne 0) {
		throw "PEQ query failed: $($output -join [Environment]::NewLine)"
	}

	return $output
}

function Get-FixtureState {
	$rows = @(
		Invoke-MySql @"
SELECT
	c.id,
	c.account_id,
	c.class,
	c.race,
	c.level,
	c.zone_id,
	COALESCE(m.class2, 0),
	COALESCE(m.class3, 0),
	(SELECT COUNT(*) FROM character_skills cs WHERE cs.id = c.id),
	(
		SELECT COUNT(*)
		FROM character_skills cs
		LEFT JOIN (
			SELECT skill_id, MAX(cap) AS cap
			FROM skill_caps
			WHERE class_id IN (2, 5, 7) AND level = 50 AND cap > 0
			GROUP BY skill_id
		) expected ON expected.skill_id = cs.skill_id
		WHERE cs.id = c.id
		  AND (expected.skill_id IS NULL OR expected.cap <> cs.value)
	),
	(
		SELECT COUNT(*)
		FROM (
			SELECT skill_id
			FROM skill_caps
			WHERE class_id IN (2, 5, 7) AND level = 50 AND cap > 0
			GROUP BY skill_id
		) expected
	),
	(
		(SELECT COUNT(*) FROM character_alternate_abilities v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_auras v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_bandolier v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_buffs v WHERE v.character_id = c.id) +
		(SELECT COUNT(*) FROM character_disciplines v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_item_recast v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_material v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_memmed_spells v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_potionbelt v WHERE v.id = c.id) +
		(SELECT COUNT(*) FROM character_spells v WHERE v.id = c.id) +
		(
			SELECT IF(
				COUNT(*) = 1 AND
				MAX(v.slot_id = 23 AND v.item_id = 13006 AND v.charges = 1) = 1,
				0,
				1
			)
			FROM inventory v
			WHERE v.character_id = c.id
		) +
		(
			SELECT COUNT(*)
			FROM quest_globals v
			WHERE v.charid = c.id
			  AND v.name IN ('mc_class2', 'mc_class3')
		) +
		(SELECT COUNT(*) FROM timers v WHERE v.char_id = c.id)
	)
FROM character_data c
LEFT JOIN character_multiclass m ON m.character_id = c.id
WHERE c.name = '$DestinationCharacter' AND c.deleted_at IS NULL;
"@
	)

	if ($rows.Count -eq 0) {
		return $null
	}
	if ($rows.Count -ne 1) {
		throw "Expected one active $DestinationCharacter row, found $($rows.Count)."
	}

	$parts = $rows[0] -split "`t"
	if ($parts.Count -ne 12) {
		throw "Unexpected $DestinationCharacter state row: $($rows[0])"
	}

	return [pscustomobject]@{
		CharacterId = [int]$parts[0]
		AccountId = [int]$parts[1]
		BaseClass = [int]$parts[2]
		Race = [int]$parts[3]
		Level = [int]$parts[4]
		ZoneId = [int]$parts[5]
		Class2 = [int]$parts[6]
		Class3 = [int]$parts[7]
		SkillCount = [int]$parts[8]
		SkillMismatches = [int]$parts[9]
		ExpectedSkills = [int]$parts[10]
		InheritedCombatRows = [int]$parts[11]
	}
}

function Assert-Fixture([object]$State) {
	if (-not $State) {
		throw "$DestinationCharacter does not exist."
	}

	if (
		$State.AccountId -ne $ExpectedAccountId -or
		$State.BaseClass -ne 2 -or
		$State.Race -ne 1 -or
		$State.Level -ne 50 -or
		$State.ZoneId -ne 202 -or
		$State.Class2 -ne 5 -or
		$State.Class3 -ne 7 -or
		$State.SkillCount -ne $ExpectedSkillCount -or
		$State.ExpectedSkills -ne $ExpectedSkillCount -or
		$State.SkillMismatches -ne 0 -or
		$State.InheritedCombatRows -ne 0
	) {
		throw "Unexpected $DestinationCharacter state: $($State | ConvertTo-Json -Compress)"
	}
}

function Retire-Fixture([int]$CharacterId) {
	$deletedName = "$DestinationCharacter-deleted-$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
	$affectedRows = @(
		Invoke-MySql @"
UPDATE character_data
SET name = '$deletedName', deleted_at = NOW(), ingame = 0
WHERE id = $CharacterId
  AND name = '$DestinationCharacter'
  AND account_id = $ExpectedAccountId
  AND deleted_at IS NULL;
SELECT ROW_COUNT();
"@
	)

	if (
		$affectedRows.Count -ne 1 -or
		[int]$affectedRows[0] -ne 1 -or
		(Get-FixtureState)
	) {
		throw "Failed to retire $DestinationCharacter character $CharacterId."
	}

	Write-Host "Retired $DestinationCharacter as $deletedName (character id $CharacterId)."
}

$state = Get-FixtureState

if ($Mode -eq "Check") {
	Assert-Fixture $state
	Write-Host (
		"$DestinationCharacter is ready: id=$($state.CharacterId), " +
		"Human Cleric/Shadowknight/Monk level 50, " +
		"skills=$($state.SkillCount)."
	)
	exit 0
}

if ($Mode -eq "Rollback") {
	if (-not $state) {
		Write-Host "$DestinationCharacter is already absent."
		exit 0
	}

	Assert-Fixture $state
	Retire-Fixture $state.CharacterId
	exit 0
}

if ($state) {
	Assert-Fixture $state
	Write-Host "$DestinationCharacter is already configured; no changes made."
	exit 0
}

$sourceRows = @(
	Invoke-MySql @"
SELECT c.id, c.account_id, c.class, c.race, c.level, c.zone_id
FROM character_data c
WHERE c.name = '$SourceCharacter' AND c.deleted_at IS NULL;
"@
)
if ($sourceRows.Count -ne 1) {
	throw "Expected exactly one active source character named $SourceCharacter."
}

$sourceParts = $sourceRows[0] -split "`t"
if (
	$sourceParts.Count -ne 6 -or
	[int]$sourceParts[0] -ne $ExpectedSourceId -or
	[int]$sourceParts[1] -ne $ExpectedAccountId -or
	[int]$sourceParts[2] -ne 3 -or
	[int]$sourceParts[3] -ne 1 -or
	[int]$sourceParts[4] -ne 50 -or
	[int]$sourceParts[5] -ne 202
) {
	throw "Source template drifted: $($sourceRows[0])"
}

$accountRows = @(
	Invoke-MySql @"
SELECT id FROM account WHERE name = '$DestinationAccount';
"@
)
if ($accountRows.Count -ne 1 -or [int]$accountRows[0] -ne $ExpectedAccountId) {
	throw (
		"Destination account mismatch. Expected $DestinationAccount id " +
		"$ExpectedAccountId."
	)
}

$copyOutput = @(
	& docker exec --workdir /home/eqemu/server $ServerContainer `
		./bin/world character:copy-character `
		$SourceCharacter $DestinationCharacter $DestinationAccount 2>&1
)
if ($LASTEXITCODE -ne 0) {
	throw "EQEmu character copy failed: $($copyOutput -join [Environment]::NewLine)"
}

$copiedRows = @(
	Invoke-MySql @"
SELECT id, account_id
FROM character_data
WHERE name = '$DestinationCharacter' AND deleted_at IS NULL;
"@
)
if ($copiedRows.Count -ne 1) {
	throw "EQEmu copy did not create exactly one active $DestinationCharacter."
}

$copiedParts = $copiedRows[0] -split "`t"
$copiedId = [int]$copiedParts[0]
if ([int]$copiedParts[1] -ne $ExpectedAccountId) {
	throw "EQEmu copied $DestinationCharacter to an unexpected account."
}

$procedureName = "setup_epic10_monktest"
$applySql = @"
DROP PROCEDURE IF EXISTS $procedureName;
DELIMITER //
CREATE PROCEDURE $procedureName()
BEGIN
	DECLARE fixture_count INT DEFAULT 0;
	DECLARE fixture_id INT DEFAULT 0;
	DECLARE fixture_account INT DEFAULT 0;
	DECLARE seeded_skills INT DEFAULT 0;

	START TRANSACTION;

	SELECT COUNT(*), COALESCE(MAX(id), 0), COALESCE(MAX(account_id), 0)
	INTO fixture_count, fixture_id, fixture_account
	FROM character_data
	WHERE id = $copiedId
	  AND name = '$DestinationCharacter'
	  AND deleted_at IS NULL;

	IF fixture_count <> 1 OR fixture_account <> $ExpectedAccountId THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Monktest copy precondition failed';
	END IF;

	UPDATE character_data
	SET class = 2,
		race = 1,
		level = 50,
		level2 = 50,
		zone_id = 202,
		zone_instance = 0,
		aa_points_spent = 0,
		aa_exp = 0,
		aa_points = 0,
		aa_points_spent_old = 0,
		aa_points_old = 0,
		ingame = 0
	WHERE id = fixture_id;

	DELETE FROM character_alternate_abilities WHERE id = fixture_id;
	DELETE FROM character_auras WHERE id = fixture_id;
	DELETE FROM character_bandolier WHERE id = fixture_id;
	DELETE FROM character_buffs WHERE character_id = fixture_id;
	DELETE FROM character_disciplines WHERE id = fixture_id;
	DELETE FROM character_item_recast WHERE id = fixture_id;
	DELETE FROM character_material WHERE id = fixture_id;
	DELETE FROM character_memmed_spells WHERE id = fixture_id;
	DELETE FROM character_potionbelt WHERE id = fixture_id;
	DELETE FROM character_spells WHERE id = fixture_id;
	DELETE FROM inventory WHERE character_id = fixture_id;
	INSERT INTO inventory (character_id, slot_id, item_id, charges)
	VALUES (fixture_id, 23, 13006, 1);
	DELETE FROM quest_globals
	WHERE charid = fixture_id AND name IN ('mc_class2', 'mc_class3');
	DELETE FROM timers WHERE char_id = fixture_id;

	DELETE FROM character_multiclass WHERE character_id = fixture_id;
	INSERT INTO character_multiclass (character_id, class2, class3)
	VALUES (fixture_id, 5, 7);

	DELETE FROM character_skills WHERE id = fixture_id;
	INSERT INTO character_skills (id, skill_id, value)
	SELECT fixture_id, skill_id, MAX(cap)
	FROM skill_caps
	WHERE class_id IN (2, 5, 7)
	  AND level = 50
	  AND cap > 0
	GROUP BY skill_id;

	SET seeded_skills = ROW_COUNT();
	IF seeded_skills <> $ExpectedSkillCount THEN
		SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Unexpected Monktest skill count';
	END IF;

	COMMIT;
END//
DELIMITER ;
CALL $procedureName();
DROP PROCEDURE $procedureName;
"@

try {
	Invoke-MySql $applySql | Out-Null
} catch {
	Invoke-MySql "DROP PROCEDURE IF EXISTS $procedureName;" | Out-Null
	Retire-Fixture $copiedId
	throw
}

$state = Get-FixtureState
Assert-Fixture $state

Write-Host (
	"Created ${DestinationCharacter}: id=$($state.CharacterId), " +
	"Human Cleric/Shadowknight/Monk level 50 in Plane of Knowledge, " +
	"$($state.SkillCount) eligible skills granted to current caps."
)
