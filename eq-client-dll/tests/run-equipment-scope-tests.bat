@echo off
setlocal
call "C:\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0.."
if not exist build\tests mkdir build\tests
cl /nologo /W4 /WX /O2 /EHsc /MT /std:c++17 tests\equipment-scope.cpp /Fo:build\tests\ /Fe:build\tests\equipment-scope.exe
if errorlevel 1 exit /b 1
build\tests\equipment-scope.exe
exit /b %errorlevel%
