@echo off
title EQ Solo GM Tools
echo.
echo  Starting EQ Solo GM Tools...
echo  API  -^>  http://localhost:3001
echo  UI   -^>  http://localhost:5173
echo.
start "EQ GM API" cmd /k "cd /d %~dp0 && node api/server.cjs"
timeout /t 1 /nobreak >nul
start "EQ GM UI"  cmd /k "cd /d %~dp0 && npx vite"
timeout /t 3 /nobreak >nul
start http://localhost:5173
