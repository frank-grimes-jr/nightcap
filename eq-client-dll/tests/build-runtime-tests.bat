@echo off
setlocal
call "C:\BuildTools\VC\Auxiliary\Build\vcvars32.bat" >nul || exit /b 1
cd /d "%~dp0.."
if not exist build\tests mkdir build\tests
for %%F in (augment-item-window paladin-grip-native bazaar-panel bazaar-panel-native runtime-config runtime-host runtime-health verified-patch ui-state ui-hooks aa-recommendations aa-recommendations-native aa-allocation-native pet-state pet-management spell-access spell-inspection spell-menu model-policy model-hooks model-animation-native model-invisible-native trainer-native tradeskill-repeat equipment-native equipment-scope monk-reuse-native) do (
 cl /nologo /W4 /WX /O2 /EHsc /MT /std:c++17 tests\%%F.cpp /Fo:build\tests\ /Fe:build\tests\%%F.exe /link /MANIFEST:EMBED /MANIFESTUAC:"level='asInvoker' uiAccess='false'"
 if errorlevel 1 exit /b 1
)
exit /b 0
