@echo off
setlocal

:: ============================================================================
:: Right-Click Converter Toolbox - Uninstallation Script
:: ============================================================================
:: This script removes the context menu entries and deletes the installed
:: portable tools and scripts.
:: ============================================================================

:: ----------------------------------------------------------------------------
:: Configuration
:: ----------------------------------------------------------------------------
echo [INFO] Setting up configuration...

:: The main directory for the toolbox
set "TOOL_DIR=%LOCALAPPDATA%\Programs\RightClickConverter"

:: ----------------------------------------------------------------------------
:: Uninstallation Steps
:: ----------------------------------------------------------------------------

echo.
echo =================================================
echo  Starting Converter Toolbox Uninstallation
echo =================================================
echo.

:: 1. Remove Registry Keys
echo [STEP 1/2] Removing Windows context menu entries...

REG DELETE "HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations\.mp4\shell\ConvertMP4toPNG" /f
REG DELETE "HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations\.png\shell\ConvertPNGtoMP4" /f
REG DELETE "HKEY_CURRENT_USER\Software\Classes\SystemFileAssociations\.exr\shell\ConvertEXRtoMP4" /f

echo    Done.
echo.

:: 2. Remove Installed Files
echo [STEP 2/2] Deleting installation directory...
if exist "%TOOL_DIR%" (
    echo    Directory to be removed: %TOOL_DIR%
    rmdir /s /q "%TOOL_DIR%"
    echo    Done.
) else (
    echo    Installation directory not found. Nothing to remove.
)
echo.

:: ----------------------------------------------------------------------------
:: Finalization
:: ----------------------------------------------------------------------------
echo.
echo =================================================
echo  Uninstallation Complete
echo =================================================
echo.
echo The Right-Click Converter Toolbox has been removed.
echo.
echo [NOTE] The installer added the FFmpeg directory to your user PATH.
echo You may want to edit your environment variables to remove it manually.
echo.
pause
endlocal
