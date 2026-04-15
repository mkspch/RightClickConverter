@echo off
setlocal

:: ============================================================================
:: TS_Toolbox - Update Script
:: ============================================================================
:: This script pulls the latest changes from the Git repository for an
:: existing installation and refreshes the context menu entries.
:: ============================================================================

:: ----------------------------------------------------------------------------
:: Configuration
:: ----------------------------------------------------------------------------
set "TOOL_DIR=%LOCALAPPDATA%\Programs\TS_Toolbox"
set "GIT_EXE=%TOOL_DIR%\git\cmd\git.exe"
set "SCRIPTS_DIR=%TOOL_DIR%\scripts"
set "PYTHON_EXE=%TOOL_DIR%\python\python.exe"

echo.
echo =================================================
echo  Updating TS_Toolbox
echo =================================================
echo.

:: Check if installation exists
if not exist "%TOOL_DIR%" (
    echo [ERROR] TS_Toolbox installation not found at:
    echo         %TOOL_DIR%
    echo         Please run install.bat first.
    pause
    exit /b 1
)

:: 1. Pull latest changes from Git
echo [STEP 1/2] Pulling latest changes from repository...
if exist "%GIT_EXE%" (
    cd /d "%SCRIPTS_DIR%"
    "%GIT_EXE%" pull
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to pull changes from Git. Please check your internet connection.
        pause
        exit /b 1
    )
) else (
    echo [ERROR] Git executable not found at %GIT_EXE%.
    pause
    exit /b 1
)
echo    Done.
echo.

:: 2. Refresh registry entries
echo [STEP 2/2] Refreshing context menu entries...
if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" "%SCRIPTS_DIR%\src\registry_manager.py" install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to update registry entries.
        pause
        exit /b 1
    )
) else (
    echo [ERROR] Python executable not found at %PYTHON_EXE%.
    pause
    exit /b 1
)
echo    Done.
echo.

:: ----------------------------------------------------------------------------
:: Finalization
:: ----------------------------------------------------------------------------
echo.
echo =================================================
echo  Update Complete!
echo =================================================
echo.
echo The latest scripts have been downloaded and the menu entries updated.
echo.
pause
endlocal
