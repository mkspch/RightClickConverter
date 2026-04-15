import os
import re
import time
import win32gui
import win32com.client

def get_selected_files_from_explorer(clicked_path=None):
    """
    Retrieves the full paths of files selected in the active Windows Explorer window.
    If clicked_path is provided, it helps identify the correct window.
    """
    # Small delay to ensure Explorer selection state is updated after right-click
    time.sleep(0.1)
    
    selected_files = []
    try:
        shell_app = win32com.client.Dispatch("Shell.Application")
        foreground_hwnd = win32gui.GetForegroundWindow()
        
        # 1. First pass: try to find the window that matches the foreground HWND
        # and contains the clicked_path (if provided).
        for window in shell_app.Windows():
            try:
                # Basic check for Explorer window
                if os.path.basename(window.FullName).lower() != "explorer.exe":
                    continue
                
                selection = window.document.SelectedItems()
                paths = [item.Path for item in selection]
                
                # If we have a clicked_path, and it's in this window's selection, 
                # this is definitely our window.
                if clicked_path and clicked_path in paths:
                    return paths
                
                # If no clicked_path, check if this is the foreground window
                if not clicked_path and window.HWND == foreground_hwnd:
                    if paths:
                        return paths
            except Exception:
                continue

        # 2. Second pass: fallback to any window that has a selection
        for window in shell_app.Windows():
            try:
                if os.path.basename(window.FullName).lower() != "explorer.exe":
                    continue
                selection = window.document.SelectedItems()
                if selection.Count > 0:
                    return [item.Path for item in selection]
            except Exception:
                continue
                
    except Exception as e:
        print(f"ERROR: Could not access Windows Shell Application: {e}")
        
    # 3. Third pass: if all else fails and we have a clicked_path, return just that
    if clicked_path:
        return [clicked_path]
        
    return selected_files

def find_sequence_files(file_path):
    """
    Finds all files in a directory that belong to an image sequence.

    Args:
        file_path (str): The path to one file in the sequence.

    Returns:
        tuple: A tuple containing (list_of_files, first_frame, sequence_pattern)
               or (None, None, None) if no sequence is found.
    """
    if not os.path.exists(file_path):
        return None, None, None

    directory = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    # Regex to find frame numbers (e.g., frame.1001.exr, frame_v01_1001.exr, frame-1001.exr)
    match = re.search(r'(\d+)\.(?!.*\d)', filename)
    if not match:
        return None, None, None

    frame_number_str = match.group(1)
    frame_padding = len(frame_number_str)
    
    start_index = match.start(1)
    end_index = match.end(1)

    # Create a pattern to search for other files
    # Example: "frame." + "%04d" + ".exr" -> "frame.%04d.exr"
    sequence_prefix = filename[:start_index]
    sequence_suffix = filename[end_index:]
    
    # Create a regex pattern to find matching files
    regex_pattern = re.compile(
        re.escape(sequence_prefix) + r'(\d{' + str(frame_padding) + r'})' + re.escape(sequence_suffix)
    )

    sequence_files = []
    for f in os.listdir(directory):
        if regex_pattern.match(f):
            full_path = os.path.join(directory, f)
            sequence_files.append(full_path)

    if not sequence_files:
        return None, None, None
        
    sequence_files.sort()
    
    # Determine the first frame number from the sorted list
    first_file_basename = os.path.basename(sequence_files[0])
    first_frame_match = regex_pattern.match(first_file_basename)
    first_frame = int(first_frame_match.group(1))

    # Create an ffmpeg-compatible sequence pattern (e.g., frame.%04d.exr)
    ffmpeg_pattern = os.path.join(directory, f"{sequence_prefix}%0{frame_padding}d{sequence_suffix}")

    return sequence_files, first_frame, ffmpeg_pattern

if __name__ == '__main__':
    # Example Usage
    # Create some dummy files for testing
    if not os.path.exists('test_sequence'):
        os.makedirs('test_sequence')
    for i in range(10, 21):
        with open(f"test_sequence/my_render.part1_{i:04d}.exr", "w") as f:
            f.write("dummy")
    
    test_file = "test_sequence/my_render.part1_0015.exr"
    # Correct the test file path to match the created files
    test_file_corrected = "test_sequence/my_render.part1_0015.exr".replace("0015", "0010")


    files, start, pattern = find_sequence_files(test_file)

    if files:
        print(f"Detected {len(files)} files in sequence.")
        print(f"First file: {files[0]}")
        print(f"Last file: {files[-1]}")
        print(f"Start frame: {start}")
        print(f"FFmpeg pattern: {pattern}")
    else:
        print("No sequence found.")

    # Clean up dummy files
    for i in range(10, 21):
        os.remove(f"test_sequence/my_render.part1_{i:04d}.exr")
    os.rmdir('test_sequence')