import sys
import os
import win32com.client # Required for pywin32 shell interaction
import hashlib
import tempfile
import time # For time.sleep

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
                except Exception as e:
                    pass
    except Exception as e:
        print(f"ERROR: Could not access Windows Shell Application: {e}")
        print("Please ensure pywin32 is correctly installed and you are running this from Explorer.")
    return selected_files

def main():
    """
    Entry point for resizing videos.
    Retrieves selected files directly from Windows Explorer using pywin32.
    Prompts user for new width.
    """
    video_paths = get_selected_files_from_explorer()

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
    lock_dir = os.path.join(tempfile.gettempdir(), "TS_Toolbox_VideoResize_Locks")
    os.makedirs(lock_dir, exist_ok=True)
    lock_file_path = os.path.join(lock_dir, f"{selected_files_hash}.lock")

    lock_acquired = False
    try:
        fd = os.open(lock_file_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
        os.close(fd)
        lock_acquired = True
        time.sleep(0.5) # Give a small buffer time
    except FileExistsError:
        print("Another instance of Video Resize is already processing this selection. Exiting redundant invocation.")
        return 
    except Exception as e:
        print(f"ERROR: Could not create lock file {lock_file_path}: {e}. Proceeding anyway, but may cause redundant operations.")
        pass

    try:
        new_width_str = ""
        while not (new_width_str.isdigit() and int(new_width_str) > 0):
            new_width_str = input("Enter new video width (pixels, e.g., 1920): ")
            if not (new_width_str.isdigit() and int(new_width_str) > 0):
                print("Invalid input. Please enter a positive integer for the width.")
        new_width = int(new_width_str)

        print(f"Resizing {len(valid_video_paths)} videos to {new_width}px width...")
        all_success = True
        for path in valid_video_paths:
            print(f"\nProcessing: {os.path.basename(path)}")
            if not converter.convert_vid_resize(path, new_width):
                all_success = False
                print(f"Failed to resize {os.path.basename(path)}.")
        
        if all_success:
            print("\nAll selected videos resized successfully!")
        else:
            print("\nSome videos failed to resize. Please check the logs above.")

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
