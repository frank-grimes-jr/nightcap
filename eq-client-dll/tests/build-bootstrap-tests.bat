@echo off
setlocal
call "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0.."
if not exist build\tests mkdir build\tests
cl /nologo /W4 /WX /O2 /EHsc /MT /LD tests\bootstrap-fixture.cpp /Fo:build\tests\ /Fe:build\tests\bootstrap-fixture.dll /link /DEF:tests\bootstrap-fixture.def
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /O2 /EHsc /MT tests\bootstrap-probe.cpp build\tests\bootstrap-fixture.lib /Fo:build\tests\ /Fe:build\tests\bootstrap-probe.exe /link /DYNAMICBASE /MANIFEST:EMBED /MANIFESTUAC:"level='asInvoker' uiAccess='false'"
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /O2 /EHsc /MT tests\bootstrap-host.cpp build\dinput8.lib /Fo:build\tests\ /Fe:build\tests\bootstrap-host.exe /link /DYNAMICBASE /MANIFEST:EMBED /MANIFESTUAC:"level='asInvoker' uiAccess='false'"
exit /b %errorlevel%
