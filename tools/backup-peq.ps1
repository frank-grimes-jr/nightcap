# Nightcap peq database backup — run manually or via scheduled task "NightcapPeqBackup".
# Dumps inside the container (binary-safe), copies out, prunes backups older than 14 days.
# Requires Docker Desktop running; failures are logged, not thrown.

$BackupDir = 'E:\EQ_Local_Dev\backups'
$Container = 'akk-stack-mariadb-1'
$LogFile   = Join-Path $BackupDir 'backup.log'
$Stamp     = Get-Date -Format 'yyyyMMdd_HHmmss'
$OutFile   = Join-Path $BackupDir "peq_$Stamp.sql.gz"

function Log($msg) { "$(Get-Date -Format s) $msg" | Out-File -FilePath $LogFile -Append -Encoding utf8 }

if (-not (Test-Path $BackupDir)) { New-Item -ItemType Directory -Force $BackupDir | Out-Null }

# Dump + gzip inside the container, then docker cp (PowerShell corrupts piped binary stdout)
docker exec $Container sh -c 'mysqldump -ueqemu -peqemu --single-transaction --routines --triggers peq | gzip > /tmp/peq_backup.sql.gz'
if ($LASTEXITCODE -ne 0) { Log "FAIL dump (docker exec exit $LASTEXITCODE)"; exit 1 }

docker cp "${Container}:/tmp/peq_backup.sql.gz" $OutFile
docker exec $Container rm -f /tmp/peq_backup.sql.gz
if (-not (Test-Path $OutFile) -or (Get-Item $OutFile).Length -lt 1MB) { Log "FAIL copy or suspiciously small: $OutFile"; exit 1 }

Log "OK $OutFile ($([math]::Round((Get-Item $OutFile).Length/1MB,1)) MB)"

# Retention: keep 14 days
Get-ChildItem $BackupDir -Filter 'peq_*.sql.gz' | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-14) } |
    ForEach-Object { Log "prune $($_.Name)"; Remove-Item $_.FullName -Force -Confirm:$false }
