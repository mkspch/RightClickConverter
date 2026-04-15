import sys
import os
import win32com.client # Required for pywin32 shell interaction
import hashlib
import tempfile
import time

# Ensure the converter module can be found
sys.path.append(os.path.dirname(__file__))
import converter

def get_selected_files_from_explorer():
    """
    Retrieves the full paths of files selected in the active Windows Explorer window.
    Requires pywin32.
    """
    selected_files = []
    try:
        shell_app = win32com.client.Dispatch("Shell.Application")
        for window in shell_app.Windows():
            if os.path.basename(window.FullName).lower() == "explorer.exe":
                try:
                    selection = window.document.SelectedItems()
                    if selection.Count > 0:
                        for item in selection:
                            selected_files.append(item.Path)
                        return selected_files
                except Exception:
                    pass
    except Exception as e:
        print(f"ERROR: Could not access Windows Shell Application: {e}")
    return selected_files

def main():
    """
    Entry point for generating an image comparison HTML.
    Retrieves selected files directly from Windows Explorer using pywin32.
    """
    image_paths = get_selected_files_from_explorer()

    # Define accepted image file extensions
    ACCEPTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.exr')

    # Filter out non-existent files and non-image files
    valid_image_paths = [p for p in image_paths if os.path.exists(p) and p.lower().endswith(ACCEPTED_IMAGE_EXTENSIONS)]

    if len(valid_image_paths) != 2:
        print(f"Error: Exactly 2 images must be selected for comparison (you selected {len(valid_image_paths)}).")
        print("Please select exactly two image files in Windows Explorer and try again.")
        print("Press Enter to exit.")
        input()
        return

    # Lock file mechanism
    selected_files_hash = hashlib.md5("".join(sorted(valid_image_paths)).encode()).hexdigest()
    lock_dir = os.path.join(tempfile.gettempdir(), "TS_Toolbox_Compare_Locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_file_path = os.path.join(lock_dir, f"{selected_files_hash}.lock")

    lock_acquired = False
    try:
        fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.close(fd)
        lock_acquired = True
        time.sleep(0.5)
    except FileExistsError:
        return
    except Exception as e:
        print(f"ERROR: Could not create lock file {lock_file_path}: {e}")
        pass

    try:
        success = converter.generate_image_comparison(valid_image_paths[0], valid_image_paths[1])
        if success:
            print("\nComparison HTML created successfully!")
        else:
            print("\nFailed to create comparison HTML.")
    finally:
        if lock_acquired and os.path.exists(lock_file_path):
            try:
                os.remove(lock_file_path)
            except Exception:
                pass
        if lock_acquired:
            print("Press Enter to exit.")
            input()

if __name__ == '__main__':
    main()
