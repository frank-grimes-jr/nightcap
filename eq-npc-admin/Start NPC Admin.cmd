@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Install Node.js 22.12 or newer, then run this launcher again.
  pause
  exit /b 1
)
if not exist node_modules\express\package.json (
  call npm ci --ignore-scripts --no-fund
  if errorlevel 1 goto failed
)
call npm run build
if errorlevel 1 goto failed
node api/server.mjs --open
if errorlevel 1 goto failed
exit /b 0
:failed
echo NPC Admin could not start. Read the error above. Port 3100 may already be in use.
pause
exit /b 1
