@echo off
setlocal
call "C:\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0.."
if not exist build mkdir build
cl /nologo /W4 /O2 /EHsc /MT /std:c++17 tests\target-details.cpp /Fo:build\target-details.obj /Fe:build\target-details.exe || exit /b 1
build\target-details.exe
