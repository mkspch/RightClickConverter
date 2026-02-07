@echo off
setlocal

:: ============================================================================
:: Right-Click Converter Toolbox - Installation Script
:: ============================================================================
:: This script downloads and sets up a portable environment for the converter
:: toolbox, and integrates it with the Windows context menu.
:: ============================================================================

:: ----------------------------------------------------------------------------
:: Configuration
:: ----------------------------------------------------------------------------
echo [INFO] Setting up configuration...

:: The root directory for the portable tools
set "INSTALL_BASE_DIR=%LOCALAPPDATA%\Programs"
:: The main directory for this specific toolbox
set "TOOL_DIR=%INSTALL_BASE_DIR%\TS_Toolbox"

:: --- Tool URLs (Update these to the latest versions as needed) ---
:: Make sure to use the 64-bit versions.

:: Python 3.11 Embeddable Package
set "PYTHON_URL=https://www.python.org/ftp/python/3.11.5/python-3.11.5-embed-amd64.zip"
set "PYTHON_ZIP=python.zip"
set "PYTHON_DIR=%TOOL_DIR%\python"

:: Portable Git for Windows
set "GIT_URL=https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/PortableGit-2.43.0-64-bit.7z.exe"
set "GIT_EXE=git_portable.exe"
set "GIT_DIR=%TOOL_DIR%\git"

:: FFmpeg (gyan.dev essentials build)
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "FFMPEG_ZIP=ffmpeg.zip"
set "FFMPEG_DIR=%TOOL_DIR%\ffmpeg"

:: --- Python Scripts Repository ---
:: This is the repository containing converter.py, utils.py, etc.
:: IMPORTANT: For minimal installation size, ensure your Git repository for this tool
::            contains ONLY the essential OCIO config files within src/config/aces_1.2/.
::            These minimal files are:
::            - config.ocio
::            - luts/Log2_48_nits_Shaper_to_linear.spi1d
::            - luts/InvRRT.sRGB.Log2_48_nits_Shaper.spi3d
::            - luts/Log2_48_nits_Shaper.RRT.sRGB.spi3d
set "SCRIPTS_REPO_URL=https://github.com/mkspch/TS_Toolbox.git"
set "SCRIPTS_DIR=%TOOL_DIR%\scripts"

:: --- Python Dependencies ---
set "PYTHON_DEPS=opencolorio openimageio"

:: ----------------------------------------------------------------------------
:: Installation Steps
:: ----------------------------------------------------------------------------

echo.
echo =================================================
echo  Starting Converter Toolbox Installation
echo =================================================
echo.
echo Installation Directory: %TOOL_DIR%
echo.

:: 1. Create directory structure
echo [STEP 1/6] Creating installation directories...
if not exist "%INSTALL_BASE_DIR%" mkdir "%INSTALL_BASE_DIR%"
if not exist "%TOOL_DIR%" mkdir "%TOOL_DIR%"
if not exist "%PYTHON_DIR%" mkdir "%PYTHON_DIR%"
if not exist "%GIT_DIR%" mkdir "%GIT_DIR%"
if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"
echo    Done.
echo.

:: 2. Download portable tools
echo [STEP 2/6] Downloading portable tools...
echo    Downloading Python...
curl -L "%PYTHON_URL%" -o "%TOOL_DIR%\%PYTHON_ZIP%"
echo    Downloading Git...
curl -L "%GIT_URL%" -o "%TOOL_DIR%\%GIT_EXE%"
echo    Downloading FFmpeg...
curl -L "%FFMPEG_URL%" -o "%TOOL_DIR%\%FFMPEG_ZIP%"
echo    Done.
echo.

:: 3. Extract portable tools
echo [STEP 3/6] Extracting tools...
echo    Extracting Python...
tar -xf "%TOOL_DIR%\%PYTHON_ZIP%" -C "%PYTHON_DIR%"
echo    Extracting Git...
:: The portable git is a self-extracting 7-zip. We can run it with -o to specify the output dir.
start /wait "" "%TOOL_DIR%\%GIT_EXE%" -o"%GIT_DIR%" -y
echo    Extracting FFmpeg...
tar -xf "%TOOL_DIR%\%FFMPEG_ZIP%" -C "%FFMPEG_DIR%" --strip-components=1
echo    Done.
echo.

:: 4. Get the Python scripts via Git
echo [STEP 4/6] Cloning converter scripts from repository...
echo    Repository: %SCRIPTS_REPO_URL%
"%GIT_DIR%\cmd\git.exe" clone "%SCRIPTS_REPO_URL%" "%SCRIPTS_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to clone the scripts repository. Please check the URL and your connection.
    goto:error
)
echo    Done.
echo.

:: 5. Set up Python environment
echo [STEP 5/6] Setting up Python environment...
echo    Enabling pip in embedded Python...
:: The embeddable package doesn't include pip. We need to get it.
curl -L "https://bootstrap.pypa.io/get-pip.py" -o "%TOOL_DIR%\get-pip.py"
"%PYTHON_DIR%\python.exe" "%TOOL_DIR%\get-pip.py"

:: Modify the pythonXX._pth file to enable site-packages
echo import site >> "%PYTHON_DIR%\python311._pth"

echo    Installing Python dependencies (%PYTHON_DEPS%)...
"%PYTHON_DIR%\Scripts\pip.exe" install %PYTHON_DEPS%
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install Python dependencies.
    goto:error
)
echo    Done.
echo.


:: 6. Add to Path and Registry Keys for Context Menu
echo [STEP 6/7] Adding FFmpeg to user PATH and creating context menu entries...

echo    Done.

echo    Calling Python script to create context menu entries...
"%PYTHON_DIR%\python.exe" "%SCRIPTS_DIR%\src\registry_manager.py" install
if %errorlevel% neq 0 (
    echo [ERROR] Failed to add registry entries. Please ensure you run install.bat as Administrator.
    goto:error
)

echo    Done.
echo.

:: ----------------------------------------------------------------------------
:: Finalization
:: ----------------------------------------------------------------------------
echo.
echo =================================================
echo  Installation Complete!
echo =================================================
echo.
echo The Right-Click Converter Toolbox should now be available.
echo.
goto:end

:error
echo.
echo [ERROR] Installation failed. Please see the messages above.
pause

:end
del "%TOOL_DIR%\%PYTHON_ZIP%"
del "%TOOL_DIR%\%GIT_EXE%"
del "%TOOL_DIR%\%FFMPEG_ZIP%"
del "%TOOL_DIR%\get-pip.py"
pause
endlocal
