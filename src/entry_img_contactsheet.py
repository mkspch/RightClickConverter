import sys
import os
import win32com.client # Required for pywin32 shell interaction
import hashlib
import tempfile

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
        # Get all open Explorer windows
        # Iterate to find the active Explorer window that has a selection
        for window in shell_app.Windows():
            # Check if the window is an Explorer window showing files
            if os.path.basename(window.FullName).lower() == "explorer.exe":
                try:
                    selection = window.document.SelectedItems()
                    if selection.Count > 0: # Only consider windows with active selections
                        for item in selection:
                            selected_files.append(item.Path)
                        return selected_files # Return as soon as a selection from an Explorer window is found
                except Exception as e:
                    # print(f"DEBUG: Error accessing selection in window: {e}")
                    pass
    except Exception as e:
        print(f"ERROR: Could not access Windows Shell Application: {e}")
        print("Please ensure pywin32 is correctly installed and you are running this from Explorer.")
    return selected_files

def main():
    """
    Entry point for creating an image contact sheet.
    Retrieves selected files directly from Windows Explorer using pywin32.
    """
    image_paths = get_selected_files_from_explorer()

    # Define accepted image file extensions
    ACCEPTED_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.exr') # Add more as needed

    # Filter out non-existent files and non-image files
    temp_valid_image_paths = [p for p in image_paths if os.path.exists(p)]
    
    valid_image_paths = []
    for p in temp_valid_image_paths:
        if p.lower().endswith(ACCEPTED_IMAGE_EXTENSIONS):
            valid_image_paths.append(p)
        # else: Removed debug print for skipping non-image file

    if not valid_image_paths:
        print("Error: No valid image files found among the selections (or none selected in Explorer).")
        print("Please select one or more image files in Windows Explorer and try again.")
        print("Press Enter to exit.")
        input()
        return

    # --- Implement Lock File Mechanism ---
    # Create a unique identifier for this set of selected files
    # Sort for consistent hash regardless of selection order
    selected_files_hash = hashlib.md5("".join(sorted(valid_image_paths)).encode()).hexdigest()
    lock_dir = os.path.join(tempfile.gettempdir(), "TS_Toolbox_ContactSheet_Locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_file_path = os.path.join(lock_dir, f"{selected_files_hash}.lock")

    lock_acquired = False
    fd = None # File descriptor for the lock file
    try:
        # Try to create the lock file. If it already exists, another instance is running.
        # Using os.open with os.O_CREAT | os.O_EXCL ensures atomicity.
        fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.close(fd) # Close the file descriptor immediately
        lock_acquired = True
        # Removed debug print for acquired lock

    except FileExistsError:
        # Removed debug print for redundant invocation
        return # Exit immediately without pausing for redundant invocations
    except Exception as e:
        print(f"ERROR: Could not create lock file {lock_file_path}: {e}. Proceeding anyway, but may cause redundant operations.")
        pass # The lock_acquired will remain False if an error occurred

    try:
        print(f"Creating contact sheet for {len(valid_image_paths)} images...")
        for path in valid_image_paths:
            print(f"  - {os.path.basename(path)}")

        # The create_contact_sheet function will determine output path based on the first image's directory
        success = converter.create_contact_sheet(valid_image_paths)

        if success:
            print("\nContact sheet created successfully!")
        else:
            print("\nFailed to create contact sheet. Please check the errors above.")
    finally:
        if lock_acquired and os.path.exists(lock_file_path):
            try:
                os.remove(lock_file_path)
                # Removed debug print for released lock
            except Exception as e:
                print(f"WARNING: Could not remove lock file {lock_file_path}: {e}")
        # Only pause the terminal for the instance that actually processed
        if lock_acquired: 
            print("Press Enter to exit.")
            input()


if __name__ == '__main__':
    main()