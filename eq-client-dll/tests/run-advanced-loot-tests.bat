@echo off
setlocal
call "C:\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0.."
if not exist build\tests mkdir build\tests
for %%F in (advanced-loot-state advanced-loot-policy advanced-loot-screen advanced-loot-controller) do (
 cl /nologo /W4 /WX /O2 /EHsc /MT /std:c++17 tests\%%F.cpp /Fo:build\tests\ /Fe:build\tests\%%F.exe
 if errorlevel 1 exit /b 1
 build\tests\%%F.exe
 if errorlevel 1 exit /b 1
)
exit /b %errorlevel%
