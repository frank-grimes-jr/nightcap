@echo off
setlocal
call "C:\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0..\..\..\eq-client-dll"
if not exist build\tests mkdir build\tests
cl /nologo /W4 /WX /O2 /EHsc /MT /std:c++17 tests\aa-allocation-native.cpp /Fo:build\tests\ /Fe:build\tests\aa-allocation-native.exe /link /MANIFEST:EMBED /MANIFESTUAC:"level='asInvoker' uiAccess='false'"
if errorlevel 1 exit /b 1
build\tests\aa-allocation-native.exe "E:\EQ_Local_Dev\Client_RoF2_Dev\everquest_rof2\eqgame.exe"
exit /b %errorlevel%
