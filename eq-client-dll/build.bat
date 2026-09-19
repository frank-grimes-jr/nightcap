@echo off
rem Build the Nightcap dinput8 proxy - x86 ONLY (RoF2 is a 32-bit client).
rem Toolchain: VS Build Tools 2022 at C:\BuildTools (vcvars32 = x86 host/target).
setlocal
call "C:\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0"
if not exist build mkdir build
cl /nologo /W4 /O2 /EHsc /MT /std:c++17 /LD src\dllmain.cpp /Fo:build\ /Fe:build\dinput8.dll ^
   /link /DEF:src\dinput8.def /MACHINE:X86
if errorlevel 1 exit /b 1
echo.
echo Built: %~dp0build\dinput8.dll
dumpbin /nologo /exports build\dinput8.dll | findstr /C:"DirectInput8Create" /C:"GetdfDIJoystick"
endlocal
