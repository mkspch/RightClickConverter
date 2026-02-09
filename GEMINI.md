# TS_Toolbox

## Project Overview

The "TS_Toolbox" is a Windows utility designed to streamline various image and video conversion tasks, particularly those encountered in professional media workflows involving EXR image sequences and color management. It provides a self-contained, portable Python environment, bundling essential tools like FFmpeg, OpenImageIO (OIIO), and PyOpenColorIO (OCIO).

The core conversion logic, residing in `src/converter.py`, handles:
*   MP4 to PNG sequence conversion.
*   MP4 to JPG sequence conversion.
*   Generic image sequence (e.g., PNG) to MP4 video conversion.
*   EXR image sequence (ACEScg) to sRGB MP4 video conversion, incorporating advanced color management via OCIO and efficient direct piping of processed pixel data to FFmpeg.
*   Image half-size scaling.
*   Image resizing to a specified width.
*   **Image contact sheet creation from multiple selected images (now fully functional).**
*   **Video contact sheet creation from multiple selected videos (now dynamically scales to the maximum height of selected videos, maintaining aspect ratios).**
*   Video resizing to a specified width.
*   **Splitting EXR files into individual AOV files (now robustly handles both multi-subimage and single-subimage EXRs with packed AOVs, including Cryptomatte channels).**

The toolbox integrates seamlessly with the Windows context menu. Users can initiate conversions by simply right-clicking on selected files, accessing a "TS_Toolbox" main menu with specific conversion options. The management of these context menu entries is handled by `src/registry_manager.py`, which is designed to support non-administrative installation for the current user. Utility functions in `src/utils.py` assist in the detection and handling of image sequences.

## Building and Running

The project's setup is designed to create a portable environment.

*   **Installation:**
    1.  Ensure the `install.bat` and `uninstall.bat` files, along with the `src/` directory, are present in your desired project root (e.g., `C:\Users\YourUser\Documents\RightClickConverter\`).
    2.  Run `install.bat` **as Administrator**. This script performs the following actions:
        *   Downloads and extracts a portable Python 3.11 environment.
        *   Downloads and extracts Portable Git for Windows.
        *   Downloads and extracts FFmpeg (gyan.dev essentials build).
        *   Clones the converter's Python scripts (including `converter.py`, `entry_*.py`, `registry_manager.py`, `utils.py`) from a GitHub repository.
        *   Installs necessary Python dependencies (`opencolorio`, `openimageio`) using `pip` within the portable Python environment.
        *   Registers the context menu entries using `src/registry_manager.py` for the current user.
        *   Cleans up downloaded temporary files.
*   **Uninstallation:**
    1.  Run `uninstall.bat` **as Administrator**. This script:
        *   Removes all registered context menu entries using `src/registry_manager.py`.
        *   Deletes the entire installed portable toolbox directory.
*   **Running Conversions:**
    1.  After a successful installation (and a potential restart of Windows Explorer or your machine), right-click on an image (MP4, PNG, EXR) or video file in Windows Explorer.
    2.  A "TS_Toolbox" submenu will appear in the context menu.
    3.  Select the desired conversion option (e.g., "VID > PNG", "VID > JPG", "IMG > MP4", "EXR > MP4 (ACEScg-sRGB)", "IMG > Half Size", "IMG > Resize", "IMG > Contact Sheet", "VID > Contact Sheet", "VID > Resize", "EXR > Split AOVs").
    4.  A terminal window will open, display progress, and report the results of the conversion.

## Development Conventions

*   **Portable Environment First:** The project prioritizes creating a self-contained portable environment, reducing system-wide dependencies.
*   **Batch Scripting:** `install.bat` and `uninstall.bat` are the primary tools for setup, dependency management, and invoking Python scripts.
*   **Python for Core Logic:** All core conversion logic, image/video processing, and advanced functionalities are implemented in Python.
*   **External Tool Integration:** Relies heavily on external command-line tools like `FFmpeg` and `Git` (via `curl` and `tar` for download/extraction), and specialized Python libraries (`PyOpenColorIO`, `OpenImageIO`, `numpy`).
*   **Windows Registry Management:** Uses Python's `winreg` module (via `src/registry_manager.py`) to programmatically manage Windows context menu entries, supporting non-administrative installation for the current user.
*   **Robust Error Handling:** Includes checks for missing executables, OCIO configuration files, and implements `try...except` blocks for graceful failure and informative error messages.
*   **Image Sequence Handling:** `src/utils.py` provides robust functions for detecting and interpreting image sequences with frame padding.
*   **Direct Piping:** The EXR conversion leverages direct piping of raw pixel data from `OpenImageIO` to `FFmpeg` to maximize efficiency and maintain quality.

## Project Structure

*   `install.bat`: Script for installing the toolbox.
*   `uninstall.bat`: Script for uninstalling the toolbox.
*   `src/`: Contains the main Python source code.
    *   `converter.py`: Core conversion logic, FFmpeg, OCIO, OIIO integration.
    *   `entry_exr_to_mp4.py`: Entry point for EXR to MP4 conversion.
    *   `entry_mp4_to_png.py`: Entry point for MP4 to PNG conversion.
    *   `entry_seq_to_mp4.py`: Entry point for image sequence to MP4 conversion.
    *   `registry_manager.py`: Python script for managing Windows context menu registry entries.
    *   `utils.py`: Utility functions, primarily for image sequence detection.
    *   `config/aces_1.2/`: Contains OpenColorIO configuration files (`config.ocio`, `luts/`).
*   `test/`: Contains test assets (e.g., `video.mp4`).
*   `dailies/`: A cloned repository (`generate-dailies`), used as a reference for best practices in media processing.