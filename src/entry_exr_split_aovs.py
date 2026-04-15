import sys
import os
import hashlib
import tempfile
import time # For time.sleep

# Ensure the converter module can be found
sys.path.append(os.path.dirname(__file__))
import converter
import utils

def main():
    """
    Entry point for splitting EXR AOVs.
    Retrieves selected files directly from Windows Explorer using pywin32.
    """
    clicked_path = sys.argv[1] if len(sys.argv) > 1 else None
    exr_paths = utils.get_selected_files_from_explorer(clicked_path)

    # Define accepted EXR file extension
    ACCEPTED_EXR_EXTENSION = '.exr'

    # Filter out non-existent files and non-EXR files
    temp_valid_exr_paths = [p for p in exr_paths if os.path.exists(p)]
    
    valid_exr_paths = []
    for p in temp_valid_exr_paths:
        if p.lower().endswith(ACCEPTED_EXR_EXTENSION):
            valid_exr_paths.append(p)
        else:
            print(f"Skipping non-EXR file: {os.path.basename(p)}")

    if not valid_exr_paths:
        print("Error: No valid EXR files found among the selections (or none selected in Explorer).")
        print("Please select one or more EXR files in Windows Explorer and try again.")
        print("Press Enter to exit.")
        input()
        return

    # --- Implement Lock File Mechanism ---
    # Create a unique identifier for this set of selected files
    # Sort for consistent hash regardless of selection order
    selected_files_hash = hashlib.md5("".join(sorted(valid_exr_paths)).encode()).hexdigest()
    lock_dir = os.path.join(tempfile.gettempdir(), "TS_Toolbox_EXRSplitAOVs_Locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_file_path = os.path.join(lock_dir, f"{selected_files_hash}.lock")

    lock_acquired = False
    try:
        fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.close(fd)
        lock_acquired = True
        time.sleep(0.5) # Give a small buffer time
    except FileExistsError:
        print("Another instance of EXR Split AOVs is already processing this selection. Exiting redundant invocation.")
        return 
    except Exception as e:
        print(f"ERROR: Could not create lock file {lock_file_path}: {e}. Proceeding anyway, but may cause redundant operations.")
        pass

    try:
        print(f"Splitting AOVs for {len(valid_exr_paths)} EXR files...")
        all_success = True
        for path in valid_exr_paths:
            print(f"\nProcessing: {os.path.basename(path)}")
            if not converter.split_exr_aovs(path):
                all_success = False
                print(f"Failed to split AOVs for {os.path.basename(path)}.")
        
        if all_success:
            print("\nAll selected EXR files processed successfully!")
        else:
            print("\nSome EXR files failed to process. Please check the logs above.")

    finally:
        if lock_acquired and os.path.exists(lock_file_path):
            try:
                os.remove(lock_file_path)
            except Exception as e:
                print(f"WARNING: Could not remove lock file {lock_file_path}: {e}")
        if lock_acquired: 
            print("Press Enter to exit.")
            input()


if __name__ == '__main__':
    main()
