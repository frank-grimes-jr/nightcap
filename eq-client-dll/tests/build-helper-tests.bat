@echo off
setlocal
call "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0.."
if not exist build\tests\helper-fixture mkdir build\tests\helper-fixture
cl /nologo /W4 /WX /O2 /EHsc /MT /LD tests\helper-fixture.cpp /Fo:build\tests\helper-fixture\ /Fe:build\tests\helper-fixture\dinput8.dll /link /DEF:tests\helper-fixture.def
if errorlevel 1 exit /b 1
cl /nologo /W4 /WX /O2 /EHsc /MT tests\helper-host.cpp build\tests\helper-fixture\dinput8.lib /Fo:build\tests\helper-fixture\ /Fe:build\tests\helper-fixture\eqgame.exe /link /DYNAMICBASE /MANIFEST:EMBED /MANIFESTUAC:"level='asInvoker' uiAccess='false'"
exit /b %errorlevel%
