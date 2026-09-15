@echo off
setlocal
call "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0.."
if not exist build mkdir build
cl /nologo /W4 /WX /O2 /EHsc /MT bootstrap\main.cpp /Fo:build\bootstrap.obj /Fe:build\nightcap-bootstrap.exe /link /MACHINE:X86 /DYNAMICBASE /NXCOMPAT /MANIFEST:EMBED /MANIFESTUAC:"level='asInvoker' uiAccess='false'"
exit /b %errorlevel%
