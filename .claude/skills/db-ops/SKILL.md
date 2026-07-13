---
name: db-ops
description: MariaDB operations for the EQEmu peq database — backup, restore, and console access. Use when the user wants to back up, restore, or query the database.
disable-model-invocation: true
---

Database operations for the `peq` MariaDB database in akk-stack (host port 3307).

Ask the user which operation they want if not specified in $ARGUMENTS.

**Console** (from `akk-stack/`):
```powershell
make mc
```

**Backup** (from `akk-stack/`):
```powershell
make mysql-backup
```

**Direct connection** (from anywhere):
```powershell
mysql -h 127.0.0.1 -P 3307 -u eqemu -peqemu peq
```

**Restore from SQL dump** (from anywhere, replace `backup.sql` with actual path):
```powershell
Get-Content backup.sql | mysql -h 127.0.0.1 -P 3307 -u eqemu -peqemu peq
```

Or via docker exec:
```bash
docker exec -i akk-stack-eqemu-server-1 mysql -u root peq < backup.sql
```

MariaDB credentials: user `eqemu`, password `eqemu`, database `peq`, port 3307.
Root credentials are in `akk-stack/.env` (MARIADB_ROOT_PASSWORD).
