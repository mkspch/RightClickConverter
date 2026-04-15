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
    Entry point for creating a video contact sheet.
    Retrieves selected files directly from Windows Explorer using pywin32.
    """
    clicked_path = sys.argv[1] if len(sys.argv) > 1 else None
    video_paths = utils.get_selected_files_from_explorer(clicked_path)

    # Define accepted video file extensions
    ACCEPTED_VIDEO_EXTENSIONS = ('.mp4', '.mov', '.avi', '.mkv', '.webm') # Add more as needed

    # Filter out non-existent files and non-video files
    temp_valid_video_paths = [p for p in video_paths if os.path.exists(p)]
    
    valid_video_paths = []
    for p in temp_valid_video_paths:
        if p.lower().endswith(ACCEPTED_VIDEO_EXTENSIONS):
            valid_video_paths.append(p)
        else:
            print(f"Skipping non-video file: {os.path.basename(p)}")

    if not valid_video_paths:
        print("Error: No valid video files found among the selections (or none selected in Explorer).")
        print("Please select one or more video files (MP4, MOV, AVI, etc.) in Windows Explorer and try again.")
        print("Press Enter to exit.")
        input()
        return

    # --- Implement Lock File Mechanism ---
    # Create a unique identifier for this set of selected files
    # Sort for consistent hash regardless of selection order
    selected_files_hash = hashlib.md5("".join(sorted(valid_video_paths)).encode()).hexdigest()
    lock_dir = os.path.join(tempfile.gettempdir(), "TS_Toolbox_VideoContactSheet_Locks")
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

        # Give a small buffer time for other instances to detect the lock
        time.sleep(0.5) # Wait for half a second

    except FileExistsError:
        print("Another instance of Video Contact Sheet is already processing this selection. Exiting redundant invocation.")
        return 
    except Exception as e:
        print(f"ERROR: Could not create lock file {lock_file_path}: {e}. Proceeding anyway, but may cause redundant operations.")
        pass # The lock_acquired will remain False if an error occurred

    try:
        print(f"Creating video contact sheet for {len(valid_video_paths)} videos...")
        for path in valid_video_paths:
            print(f"  - {os.path.basename(path)}")

        success = converter.create_video_contact_sheet(valid_video_paths)

        if success:
            print("\nVideo contact sheet created successfully!")
        else:
            print("\nFailed to create video contact sheet. Please check the errors above.")
    finally:
        if lock_acquired and os.path.exists(lock_file_path):
            try:
                os.remove(lock_file_path)
            except Exception as e:
                print(f"WARNING: Could not remove lock file {lock_file_path}: {e}")
        # Only pause the terminal for the instance that actually processed
        if lock_acquired: 
            print("Press Enter to exit.")
            input()


if __name__ == '__main__':
    main()
