---
name: start-stack
description: Start the full EQEmu dev environment — akk-stack Docker containers and eq-solo-gm dev servers. Use when the user wants to bring up the whole local stack.
disable-model-invocation: true
---

Start the EverQuest emulator dev environment. These require two separate terminal windows on Windows.

**Terminal 1 — Docker containers** (from `akk-stack/`):
```powershell
cd akk-stack
make up
```
Verify with `docker ps` — look for eqemu-server and mariadb containers.

**Terminal 2 — eq-solo-gm dev servers** (from `eq-solo-gm/`):
```powershell
cd eq-solo-gm
npm run dev
```
This starts the Express API on port 3001 and the Vite frontend on port 5173 concurrently.

**Verify everything is up:**
- http://localhost:5173 — GM tool frontend
- http://localhost:3001/api/ping — API health
- MariaDB accessible at localhost:3307 (`peq` database)

Tell the user both terminals need to stay open. If containers are already running, skip Terminal 1.
