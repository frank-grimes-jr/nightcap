# Syncs ALL spell-access gates to the server's spells_new (the multiclass source
# of truth). Run after any discipline embrace/release at the Chronicler, with the
# EQ CLIENT CLOSED. Idempotent.
#
# The three gates (all must agree for buy -> right-click scribe -> memorize):
#   1. spells_new class levels  - patched live by plugin::mc_apply_class (source)
#   2. scroll items.classes     - synced here from spells_new, then shared_memory
#                                 regen + zone restart (items are shared-mem cached)
#   3. client spells_us.txt     - class-level fields 105-120 rewritten from spells_new
#                                 (RoF2 refuses to memorize what its local file forbids)

$Root      = 'E:\EQ_Local_Dev'
$SpellFile = Join-Path $Root 'Client_RoF2_Dev\everquest_rof2\spells_us.txt'

if (Get-Process eqgame -ErrorAction SilentlyContinue) {
    Write-Output 'EQ client is running - close it first (it holds/caches spells_us.txt).'
    exit 1
}

# -- Gate 2: scroll item class bits <- spells_new ------------------------------
$mask = (1..16 | ForEach-Object { "(CASE WHEN s.classes$_ BETWEEN 1 AND 254 THEN $([math]::Pow(2, $_ - 1)) ELSE 0 END)" }) -join ' + '
docker exec akk-stack-mariadb-1 mysql -ueqemu -peqemu peq -e "UPDATE items i JOIN spells_new s ON s.id = i.scrolleffect SET i.classes = $mask WHERE i.itemtype = 20 AND i.scrolleffect > 0;"
if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL: items sync'; exit 1 }
Write-Output 'scroll items.classes synced from spells_new'

# -- Gate 2b: rebuild shared memory + restart zones ----------------------------
docker exec akk-stack-eqemu-server-1 bash -c 'cd /home/eqemu/server && ./bin/shared_memory > /dev/null 2>&1'
if ($LASTEXITCODE -ne 0) { Write-Output 'FAIL: shared_memory regen'; exit 1 }
docker exec akk-stack-eqemu-server-1 bash -c 'pgrep -x zone | xargs -r kill'
Write-Output 'shared memory rebuilt, all zones restarted'

# -- Gate 3: client spells_us.txt class levels <- spells_new -------------------
$dump = docker exec akk-stack-mariadb-1 mysql -ueqemu -peqemu peq -N -e "SELECT id, CONCAT_WS('^', classes1,classes2,classes3,classes4,classes5,classes6,classes7,classes8,classes9,classes10,classes11,classes12,classes13,classes14,classes15,classes16) FROM spells_new;"
$levels = @{}
foreach ($line in $dump) { $p = $line -split "`t"; if ($p.Count -eq 2) { $levels[$p[0]] = ($p[1] -split '\^') } }
Write-Output "loaded class levels for $($levels.Count) spells from spells_new"

Copy-Item $SpellFile "$SpellFile.bak" -Force
$sw = [System.IO.StreamWriter]::new("$SpellFile.tmp", $false, [System.Text.Encoding]::ASCII)
$patched = 0
foreach ($line in [System.IO.File]::ReadLines($SpellFile)) {
    $f = $line.Split('^')
    # 0-indexed: fields 104..119 are classes 1..16
    if ($f.Count -gt 120 -and $levels.ContainsKey($f[0])) {
        $new = $levels[$f[0]]
        for ($i = 0; $i -lt 16; $i++) {
            if ($f[104 + $i] -ne $new[$i]) { $f[104 + $i] = $new[$i]; $patched++ }
        }
        $sw.WriteLine(($f -join '^'))
    } else {
        $sw.WriteLine($line)
    }
}
$sw.Close()
Move-Item "$SpellFile.tmp" $SpellFile -Force
Write-Output "client spells_us.txt: $patched class-level fields updated (backup: spells_us.txt.bak)"
Write-Output 'DONE - log in and test buy -> scribe -> memorize.'
