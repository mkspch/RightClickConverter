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

:: The root directory for the portable tools
set "INSTALL_BASE_DIR=%LOCALAPPDATA%\Programs"
:: The main directory for this specific toolbox
set "TOOL_DIR=%INSTALL_BASE_DIR%\TS_Toolbox"
set "PYTHON_DIR=%TOOL_DIR%\python"
set "SCRIPTS_DIR=%TOOL_DIR%\scripts"

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

echo    Calling Python script to remove context menu entries...
"%PYTHON_DIR%\python.exe" "%SCRIPTS_DIR%\src\registry_manager.py" uninstall
if %errorlevel% neq 0 (
    echo [ERROR] Failed to remove registry entries. Please ensure you run uninstall.bat as Administrator.
)

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

pause
endlocal
