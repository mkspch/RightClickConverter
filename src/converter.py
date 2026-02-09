import os
import subprocess
import tempfile
import shutil
import numpy as np
import utils
from PIL import Image
import math # Added for math.ceil

try:
    import PyOpenColorIO as OCIO
    import OpenImageIO as OIIO
except ImportError:
    print("FATAL ERROR: PyOpenColorIO or OpenImageIO not found.")
    print("Please ensure these libraries are installed in the portable python environment.")
    OCIO = None
    OIIO = None

def _get_tool_path(tool_exe_name): # Renamed tool_name to tool_exe_name for clarity
    local_app_data = os.environ.get('LOCALAPPDATA')
    if not local_app_data:
        print("CRITICAL ERROR: LOCALAPPDATA environment variable not found.")
        return None

    # Both ffmpeg.exe and ffprobe.exe are located in the 'ffmpeg/bin' directory
    tool_dir = os.path.join(local_app_data, 'Programs', 'TS_Toolbox', 'ffmpeg', 'bin')
    tool_exe_path = os.path.join(tool_dir, f'{tool_exe_name}.exe')
    return tool_exe_path

FFMPEG_EXE = _get_tool_path('ffmpeg')
FFPROBE_EXE = _get_tool_path('ffprobe')

def convert_mp4_to_png_sequence(video_path):
    print(f"DEBUG: FFMPEG_EXE resolved to: {FFMPEG_EXE}")
    if not os.path.exists(FFMPEG_EXE):
        print(f"ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed and accessible at this path.")
        return False
    print(f"Using FFmpeg executable: {FFMPEG_EXE}")

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False

    video_dir = os.path.dirname(video_path)
    video_filename = os.path.basename(video_path)
    base_name, _ = os.path.splitext(video_filename)

    output_dir = os.path.join(video_dir, base_name)
    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, f"{base_name}_%04d.png")

    print(f"Starting conversion of {video_filename} to PNG sequence...")
    command = [
        FFMPEG_EXE,
        '-i', video_path,
        output_pattern
    ]

    print(f"FFMPEG Command: {' '.join(command)}")
    
    try:
        subprocess.run(command, executable=FFMPEG_EXE, check=True, capture_output=False, text=True) 
        print(f"Successfully converted video to PNG sequence in {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(command)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False


def convert_mp4_to_jpg_sequence(video_path, quality=90):
    print(f"DEBUG: FFMPEG_EXE resolved to: {FFMPEG_EXE}")
    if not os.path.exists(FFMPEG_EXE):
        print(f"ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed and accessible at this path.")
        return False
    print(f"Using FFmpeg executable: {FFMPEG_EXE}")

    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False

    video_dir = os.path.dirname(video_path)
    video_filename = os.path.basename(video_path)
    base_name, _ = os.path.splitext(video_filename)

    output_dir = os.path.join(video_dir, base_name)
    os.makedirs(output_dir, exist_ok=True)

    output_pattern = os.path.join(output_dir, f"{base_name}_%04d.jpg")

    print(f"Starting conversion of {video_filename} to JPG sequence...")
    ffmpeg_q_value = 2 + (100 - quality) * 29 // 99
    ffmpeg_q_value = max(2, min(31, ffmpeg_q_value))
    print(f"DEBUG: Using FFmpeg -q:v quality: {ffmpeg_q_value} (from input quality {quality})")

    command = [
        FFMPEG_EXE,
        '-i', video_path,
        '-q:v', str(ffmpeg_q_value),
        output_pattern
    ]

    print(f"FFMPEG Command: {' '.join(command)}")
    
    try:
        subprocess.run(command, executable=FFMPEG_EXE, check=True, capture_output=False, text=True) 
        print(f"Successfully converted video to JPG sequence in {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(command)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False


def convert_sequence_to_mp4(first_file_path, framerate=25, output_path=None):
    print(f"DEBUG: FFMPEG_EXE resolved to: {FFMPEG_EXE}")
    if not os.path.exists(FFMPEG_EXE):
        print(f"ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed and accessible at this path.")
        return False
    print(f"Using FFmpeg executable: {FFMPEG_EXE}")
    files, start_frame, sequence_pattern = utils.find_sequence_files(first_file_path)

    if not files:
        print("Error: Could not find sequence.")
        return False

    if not output_path:
        output_dir = os.path.dirname(first_file_path)
        base_name = os.path.basename(sequence_pattern).split('%')[0].rstrip('._-')
        if not base_name:
            base_name = "output"
        output_path = os.path.join(output_dir, f"{base_name}.mp4")

    print(f"Starting conversion of sequence {os.path.basename(sequence_pattern)} to MP4...")

    command = [
        FFMPEG_EXE,
        '-framerate', str(framerate),
        '-start_number', str(start_frame),
        '-i', sequence_pattern,
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p',
        '-y',
        output_path
    ]

    print(f"FFMPEG Command: {' '.join(command)}")
    try:
        subprocess.run(command, executable=FFMPEG_EXE, check=True, capture_output=True, text=True)
        print(f"Successfully created video: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(command)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False

def convert_exr_to_srgb_mp4(first_file_path, framerate=25):
    if not OCIO or not OIIO:
        return False

    exr_files, start_frame, sequence_pattern = utils.find_sequence_files(first_file_path)

    if not exr_files:
        print("Error: Could not find EXR sequence.")
        return False
        
    output_dir = os.path.dirname(first_file_path)
    base_name = os.path.basename(sequence_pattern).split('%')[0].rstrip('._-')
    final_output_path = os.path.join(output_dir, f"{base_name}_sRGB.mp4")

    ocio_config_path = os.path.join(os.path.dirname(__file__), 'config', 'aces_1.2', 'config.ocio')
    if not os.path.exists(ocio_config_path):
        print(f"CRITICAL ERROR: OCIO config not found at {ocio_config_path}")
        return False

    try:
        config = OCIO.Config.CreateFromFile(ocio_config_path)
        processor = config.getProcessor("ACEScg", "Output - sRGB")
    except Exception as e:
        print(f"OCIO Error: Could not set up color processor. {e}")
        return False

    first_img_buf = OIIO.ImageBuf(exr_files[0])
    output_width = first_img_buf.spec().width
    output_height = first_img_buf.spec().height

    ffmpeg_pixel_format = "rgb48le"

    ffmpeg_cmd = [
        FFMPEG_EXE,
        "-hide_banner", "-loglevel", "info", "-y",
        "-f", "rawvideo",
        "-pixel_format", ffmpeg_pixel_format,
        "-video_size", f"{output_width}x{output_height}",
        "-framerate", str(framerate),
        "-i", "pipe:0",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "23",
        final_output_path
    ]

    print(f"FFMPEG Command: {' '.join(ffmpeg_cmd)}")

    try:
        ffproc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, executable=FFMPEG_EXE)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed.")
        return False
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start FFmpeg subprocess: {e}")
        return False

    print("Starting color conversion and piping to FFmpeg...")
    try:
        for i, exr_path in enumerate(exr_files):
            print(f"  Processing frame {start_frame + i} ({i+1}/{len(exr_files)}): {os.path.basename(exr_path)}")
            
            img_buf = OIIO.ImageBuf(exr_path)

            OIIO.ImageBufAlgo.channels(img_buf, img_buf, (0,1,2))
            
            success_ocio = OIIO.ImageBufAlgo.colorconvert(img_buf, img_buf, "ACEScg", "Output - sRGB", colorconfig=ocio_config_path)
            if not success_ocio:
                print(f"OCIO Color Convert failed for frame {start_frame + i}. Check OCIO config and colorspace names.")
                return False

            if img_buf.spec().width != output_width or img_buf.spec().height != output_height:
                print(f"DEBUG: Resizing frame {start_frame + i} from {img_buf.spec().width}x{img_buf.spec().height} to {output_width}x{output_height}")
                img_buf = OIIO.ImageBufAlgo.resize(img_buf, "box", roi=OIIO.ROI(0, output_width, 0, output_height))

            pixels_raw = img_buf.get_pixels(OIIO.UINT16)

            print(f"DEBUG: Frame {start_frame + i} - Pixels raw shape: {pixels_raw.shape}, dtype: {pixels_raw.dtype}")
            expected_bytes = output_width * output_height * 3 * 2
            actual_bytes = len(pixels_raw.tobytes())
            print(f"DEBUG: Frame {start_frame + i} - Pixels raw byte length: {actual_bytes}, Expected: {expected_bytes}")
            if actual_bytes != expected_bytes:
                print("CRITICAL ERROR: Mismatch in pixel data byte length!")
                return False

            ffproc.stdin.write(pixels_raw.tobytes())

        print("Color conversion and piping complete. Waiting for FFmpeg to finish...")
        ffproc.stdin.close()
        stdout, stderr = ffproc.communicate()

        if ffproc.returncode != 0:
            print(f"ERROR: FFmpeg exited with error code {ffproc.returncode}")
            print("FFmpeg stdout:\n", stdout.decode())
            print("FFmpeg stderr:\n", stderr.stderr.decode())
            return False
        else:
            print("FFmpeg encoding finished successfully!")
            return True

    except Exception as e:
        print(f"An error occurred during the conversion process: {e}")
        import traceback
        traceback.print_exc()
        return False


def convert_exr_to_srgb_jpg_sequence(first_file_path, quality=90):
    """
    Converts an EXR image sequence (ACEScg) to an sRGB JPG image sequence,
    applying OCIO color management.

    Args:
        first_file_path (str): Path to the first file in the EXR sequence.
        quality (int): JPEG quality (0-100). Default is 90.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not OCIO or not OIIO:
        print("Error: PyOpenColorIO or OpenImageIO not available. Cannot perform EXR to JPG conversion.")
        return False

    exr_files, start_frame, sequence_pattern = utils.find_sequence_files(first_file_path)

    if not exr_files:
        print("Error: Could not find EXR sequence.")
        return False
        
    output_base_dir = os.path.dirname(first_file_path)
    base_name = os.path.basename(sequence_pattern).split('%')[0].rstrip('._-')
    output_sequence_dir = os.path.join(output_base_dir, f"{base_name}_sRGB_JPG")
    os.makedirs(output_sequence_dir, exist_ok=True)

    ocio_config_path = os.path.join(os.path.dirname(__file__), 'config', 'aces_1.2', 'config.ocio')
    if not os.path.exists(ocio_config_path):
        print(f"CRITICAL ERROR: OCIO config not found at {ocio_config_path}")
        return False

    try:
        config = OCIO.Config.CreateFromFile(ocio_config_path)
        processor = config.getProcessor("ACEScg", "Output - sRGB")
    except Exception as e:
        print(f"OCIO Error: Could not set up color processor. {e}")
        return False

    print(f"Starting color conversion of EXR sequence to sRGB JPG sequence in {output_sequence_dir}...")
    
    try:
        for i, exr_path in enumerate(exr_files):
            print(f"  Processing frame {start_frame + i} ({i+1}/{len(exr_files)}): {os.path.basename(exr_path)}")
            
            # Read EXR using OIIO
            img_buf = OIIO.ImageBuf(exr_path)

            # Ensure we're working with RGB channels (skip alpha if present for JPG)
            # OIIO.ImageBufAlgo.channels will ensure a 3-channel image if original is RGBA or more.
            # It handles cases where there are fewer than 3 channels gracefully.
            OIIO.ImageBufAlgo.channels(img_buf, img_buf, (0,1,2))
            
            # Apply OCIO color conversion
            success_ocio = OIIO.ImageBufAlgo.colorconvert(img_buf, img_buf, "ACEScg", "Output - sRGB", colorconfig=ocio_config_path)
            if not success_ocio:
                print(f"OCIO Color Convert failed for frame {start_frame + i}. Check OCIO config and colorspace names.")
                return False

            # Get pixel data as float (OIIO's default for color conversion output)
            pixels_float = img_buf.get_pixels() # Returns numpy array, typically float32
            
            # Convert float [0.0, 1.0] to uint8 [0, 255] for JPEG
            # Clamp values to [0, 1] before scaling to avoid issues with out-of-range floats
            pixels_uint8 = np.clip(pixels_float, 0.0, 1.0) * 255.0
            pixels_uint8 = pixels_uint8.astype(np.uint8)

            # Create PIL Image
            # Ensure it's RGB mode, not RGBA if an alpha channel somehow made it through
            if pixels_uint8.shape[-1] == 4: # If it's RGBA, convert to RGB
                pil_img = Image.fromarray(pixels_uint8[:,:,:3], 'RGB')
            else: # Assume RGB
                pil_img = Image.fromarray(pixels_uint8, 'RGB')


            # Construct output filename
            frame_num_str = str(start_frame + i).zfill(len(str(len(exr_files) + start_frame -1))) # Matches original padding
            output_jpg_path = os.path.join(output_sequence_dir, f"{base_name}_{frame_num_str}.jpg")
            
            # Save as JPEG
            pil_img.save(output_jpg_path, quality=quality)

        print(f"Successfully converted EXR sequence to sRGB JPG sequence in {output_sequence_dir}")
        return True

    except Exception as e:
        print(f"An error occurred during the EXR to JPG conversion process: {e}")
        import traceback
        traceback.print_exc()
        return False
def convert_img_half_size(image_path):
    """
    Scales down the selected image file to half its size, maintaining aspect ratio.

    Args:
        image_path (str): The full path to the input image file.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return False

    try:
        img = Image.open(image_path)
        original_width, original_height = img.size
        
        new_width = original_width // 2
        new_height = original_height // 2

        if new_width < 1: new_width = 1
        if new_height < 1: new_height = 1

        resized_img = img.resize((new_width, new_height), Image.LANCZOS)
        
        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_half{ext}"
        
        resized_img.save(output_path)
        print(f"Successfully scaled '{os.path.basename(image_path)}' to half size: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"Error converting image '{os.path.basename(image_path)}': {e}")
        return False

def convert_img_resize(image_path, new_width):
    """
    Resizes an image to a new width, maintaining aspect ratio.

    Args:
        image_path (str): The full path to the input image file.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at {image_path}")
        return False
    if new_width <= 0:
        print(f"Error: new_width must be a positive integer, got {new_width}")
        return False

    try:
        img = Image.open(image_path)
        original_width, original_height = img.size
        
        # Calculate new height maintaining aspect ratio
        aspect_ratio = original_width / original_height
        new_height = int(new_width / aspect_ratio)

        # Ensure minimum dimensions to avoid errors with very small images
        if new_height < 1: new_height = 1

        resized_img = img.resize((new_width, new_height), Image.LANCZOS) # LANCZOS is a high-quality downsampling filter

        base_name, ext = os.path.splitext(image_path)
        output_path = f"{base_name}_resized_{new_width}px{ext}"
        
        resized_img.save(output_path)
        print(f"Successfully resized '{os.path.basename(image_path)}' to {new_width}px width: {os.path.basename(output_path)}")
        return True
    except Exception as e:
        print(f"Error resizing image '{os.path.basename(image_path)}': {e}")
        return False

def create_contact_sheet(image_paths, output_filename="contact_sheet.jpg", columns=2, padding=10):
    """
    Creates a contact sheet from multiple images, arranged in columns.
    Images are scaled to match the height of the tallest image.
    Empty spaces are filled with black.

    Args:
        image_paths (list): A list of full paths to the input image files.
        output_filename (str): The desired filename for the output contact sheet.
        columns (int): The number of columns for the contact sheet grid.
        padding (int): Padding between images and around the border.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not image_paths:
        print("Error: No image paths provided for contact sheet.")
        return False

    images = []
    max_height = 0
    
    try:
        # Load images and find max height
        for path in image_paths:
            if not os.path.exists(path):
                print(f"Warning: Image not found and skipped: {path}")
                continue
            img = Image.open(path)
            images.append(img)
            if img.height > max_height:
                max_height = img.height

        if not images:
            print("Error: No valid images found to create contact sheet.")
            return False

        # Resize all images to the max_height, maintaining aspect ratio
        resized_images = []
        max_resized_width = 0
        for img in images:
            if img.height != max_height:
                aspect_ratio = img.width / img.height
                new_width = int(max_height * aspect_ratio)
                resized_img = img.resize((new_width, max_height), Image.LANCZOS)
            else:
                resized_img = img
            resized_images.append(resized_img)
            if resized_img.width > max_resized_width:
                max_resized_width = resized_img.width

        # Calculate the canvas size
        num_images = len(resized_images)
        rows = (num_images + columns - 1) // columns
        
        canvas_width = (max_resized_width * columns) + (padding * (columns + 1))
        canvas_height = (max_height * rows) + (padding * (rows + 1))

        contact_sheet = Image.new('RGB', (canvas_width, canvas_height), color = (0, 0, 0)) # Black background

        for i, img in enumerate(resized_images):
            # Calculate position for current image
            col = i % columns
            row = i // columns

            x_pos = (col * (max_resized_width + padding)) + padding
            y_pos = (row * (max_height + padding)) + padding
            paste_y = y_pos + (max_height - img.height) // 2 # Center vertically within its cell

            contact_sheet.paste(img, (x_pos, paste_y))
            
        output_path = os.path.join(os.path.dirname(image_paths[0]), output_filename)
        contact_sheet.save(output_path)
        print(f"Successfully created contact sheet: {output_path}")
        return True

    except Exception as e:
        print(f"Error creating contact sheet: {e}")
        return False

def create_video_contact_sheet(video_paths, output_filename="video_contact_sheet.mp4", columns=2, snippet_duration=5):
    """
    Creates an animated video contact sheet from multiple video files.
    It extracts a short segment from each video, scales them, arranges them in a grid,
    and then outputs a single MP4 video. All video snippets are scaled to the height
    of the tallest video in the selection, maintaining their aspect ratios.

    Args:
        video_paths (list): A list of full paths to the input video files.
        output_filename (str): The desired filename for the output video contact sheet.
        columns (int): The number of columns for the contact sheet grid.
        snippet_duration (int): The duration in seconds of the video snippet to extract from each video.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not video_paths:
        print("Error: No video paths provided for video contact sheet.")
        return False

    temp_dir = ""
    try:
        temp_dir = tempfile.mkdtemp()
        extracted_snippets = []
        input_args = [] # For FFmpeg input files

        # --- Phase 1: Extract video snippets and gathering video info ---
        print("Extracting video snippets and gathering video info...")
        shortest_duration = float('inf')
        max_height_across_videos = 0 # Initialize max height

        for i, video_path in enumerate(video_paths):
            if not os.path.exists(video_path):
                print(f"Warning: Video not found and skipped: {video_path}")
                continue

            probe_cmd_list = [
                FFPROBE_EXE, '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,duration', '-of', 'default=noprint_wrappers=1', video_path
            ]
            print(f"DEBUG: FFPROBE_EXE command: {' '.join(probe_cmd_list)}")
            probe_output = subprocess.check_output(probe_cmd_list, stderr=subprocess.STDOUT, text=True)
            print(f"DEBUG: FFPROBE_EXE output for {os.path.basename(video_path)}: '{probe_output.strip()}'")

            if not probe_output.strip():
                print(f"WARNING: FFPROBE_EXE returned empty output for {os.path.basename(video_path)}. Skipping video.")
                continue

            lines = probe_output.strip().split('\n')
            
            width = 0
            height = 0
            duration = 0.0

            for line in lines:
                if line.startswith("width="):
                    width = int(line.split('=')[1])
                elif line.startswith("height="):
                    height = int(line.split('=')[1])
                elif line.startswith("duration="):
                    duration = float(line.split('=')[1])
            
            if width == 0 or height == 0 or duration == 0.0:
                print(f"WARNING: Could not parse width, height, or duration from ffprobe output for {os.path.basename(video_path)}. Skipping video.")
                continue
            
            shortest_duration = min(shortest_duration, duration)
            max_height_across_videos = max(max_height_across_videos, height) # Update max height

            actual_snippet_duration = min(snippet_duration, duration)
            if actual_snippet_duration <= 0:
                print(f"Warning: Video {os.path.basename(video_path)} is too short to extract a snippet. Skipping.")
                continue

            input_args.extend(['-i', video_path])

            extracted_snippets.append({
                "path": video_path,
                "index": i,
                "original_width": width,
                "original_height": height,
                "duration": duration,
                # scaled_height and scaled_width will be determined after max_height_across_videos is final
            })
            print(f"  Processed video {os.path.basename(video_path)} (Duration: {duration:.1f}s, Original Size: {width}x{height})")

        if not extracted_snippets:
            print("Error: No valid video files found to create contact sheet after processing.")
            return False

        final_snippet_duration = min(snippet_duration, shortest_duration)
        if final_snippet_duration <= 0:
            print("Error: All selected videos are too short for snippet duration. Cannot create contact sheet.")
            return False
        
        # Now that max_height_across_videos is determined, calculate final scaled dimensions
        target_height_for_all_snippets = max_height_across_videos
        if target_height_for_all_snippets == 0:
            target_height_for_all_snippets = 360 # Fallback default if all videos were skipped or invalid

        max_scaled_width_for_grid = 0
        for snippet_info in extracted_snippets:
            scaled_width_for_target_height = int(snippet_info["original_width"] * (target_height_for_all_snippets / snippet_info["original_height"]))
            snippet_info["scaled_width_final"] = scaled_width_for_target_height
            snippet_info["scaled_height_final"] = target_height_for_all_snippets # Store for clarity
            if scaled_width_for_target_height > max_scaled_width_for_grid:
                max_scaled_width_for_grid = scaled_width_for_target_height
        
        if max_scaled_width_for_grid % 2 != 0:
            max_scaled_width_for_grid += 1


        # --- Phase 2: Construct FFmpeg filter_complex for grid arrangement ---
        filter_parts = []
        stream_labels = []
        for i, snippet_info in enumerate(extracted_snippets):
            filter_parts.append(
                f"[{i}:v]trim=start=0:duration={final_snippet_duration},setpts=PTS-STARTPTS,"
                f"scale={max_scaled_width_for_grid}:{target_height_for_all_snippets}:force_original_aspect_ratio=decrease,setsar=1,"
                f"pad={max_scaled_width_for_grid}:{target_height_for_all_snippets}:(ow-iw)/2:(oh-ih)/2[v{i}]"
            )
            stream_labels.append(f"[v{i}]")

        num_videos = len(extracted_snippets)
        rows = math.ceil(num_videos / columns)

        current_stream_idx = 0
        h_stacks_output_labels = []

        for r in range(rows):
            row_streams_to_stack = []
            for c in range(columns):
                if current_stream_idx < num_videos:
                    row_streams_to_stack.append(stream_labels[current_stream_idx])
                    current_stream_idx += 1
                else:
                    filler_width = max_scaled_width_for_grid
                    filler_height = target_height_for_all_snippets
                    filter_parts.append(f"color=black:s={filler_width}x{filler_height}:d={final_snippet_duration}[fill{r}{c}]")
                    row_streams_to_stack.append(f"[fill{r}{c}]")
            
            if not row_streams_to_stack:
                continue

            num_in_row = len(row_streams_to_stack)
            if num_in_row == 1:
                filter_parts.append(f"{row_streams_to_stack[0]}split=1[h{r}]")
            else:
                filter_parts.append(f"{''.join(row_streams_to_stack)}hstack=inputs={num_in_row}:shortest=1[h{r}]")
            h_stacks_output_labels.append(f"[h{r}]")
        
        if not h_stacks_output_labels:
            print("Error: Could not arrange video snippets into a grid.")
            return False
            
        if len(h_stacks_output_labels) == 1:
            filter_parts.append(f"{h_stacks_output_labels[0]}split=1[out]")
        else:
            filter_parts.append(f"{''.join(h_stacks_output_labels)}vstack=inputs={len(h_stacks_output_labels)}[out]")


        output_path = os.path.join(os.path.dirname(video_paths[0]), output_filename)

        final_ffmpeg_cmd = [
            FFMPEG_EXE,
            '-y',
            *input_args,
            '-filter_complex', ';'.join(filter_parts),
            '-map', '[out]',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-preset', 'medium',
            output_path
        ]

        print(f"Final FFmpeg Command: {' '.join(final_ffmpeg_cmd)}")
        subprocess.run(final_ffmpeg_cmd, check=True, capture_output=True, text=True, shell=True)
        
        print(f"Successfully created video contact sheet: {output_path}")
        return True

    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(e.cmd)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False
    except Exception as e:
        print(f"An error occurred during the video contact sheet creation: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")
        
def convert_vid_resize(video_path, new_width):
    """
    Resizes a video to a new width, maintaining aspect ratio.

    Args:
        video_path (str): The full path to the input video file.
        new_width (int): The desired new width for the video.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return False
    if new_width <= 0:
        print(f"Error: new_width must be a positive integer, got {new_width}")
        return False
    if not os.path.exists(FFMPEG_EXE):
        print(f"ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed and accessible at this path.")
        return False
    print(f"Using FFmpeg executable: {FFMPEG_EXE}")

    try:
        base_name, ext = os.path.splitext(video_path)
        output_path = f"{base_name}_resized_{new_width}px{ext}"

        # FFmpeg command to resize video, maintaining aspect ratio (-2 for height means auto-calculate even number)
        # and copy audio stream.
        ffmpeg_cmd_list = [
            FFMPEG_EXE, '-y',
            '-i', video_path,
            '-vf', f'scale={new_width}:-2',
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23',
            '-preset', 'medium',
            output_path
        ]
        print(f"Final FFmpeg Command: {' '.join(ffmpeg_cmd_list)}")

        subprocess.run(ffmpeg_cmd_list, check=True, capture_output=True, text=True)
        
        print(f"Successfully resized video '{os.path.basename(video_path)}' to {new_width}px width: {os.path.basename(output_path)}")
        return True

    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {ffmpeg_cmd}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False
    except Exception as e:
        print(f"An error occurred during video resizing: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_number_of_subimages(input_image_obj):
    """
    Counts the number of subimages in an OpenImageIO ImageInput object.
    """
    count = 0
    # Store the current subimage and miplevel to restore later
    original_subimage = input_image_obj.current_subimage()
    original_miplevel = input_image_obj.current_miplevel()

    while input_image_obj.seek_subimage(count, 0):
        count += 1
    
    # Restore the original subimage and miplevel state
    input_image_obj.seek_subimage(original_subimage, original_miplevel)
    return count

def split_exr_aovs(exr_path):
    """
    Splits an EXR file into individual AOV (Arbitrary Output Variable) files,
    each containing its native channels, and handles Cryptomatte channels separately.
    It supports both multi-part EXR files (where each part is an AOV) and
    single-part EXR files where multiple AOVs are packed as channels within one part.

    Args:
        exr_path (str): The path to the input EXR file.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not OIIO:
        print("Error: OpenImageIO is not available. Cannot split EXR AOVs.")
        return False

    if not os.path.exists(exr_path):
        print(f"Error: EXR file not found at {exr_path}")
        return False

    try:
        input_image = OIIO.ImageInput.open(exr_path)
        if not input_image:
            print(f"Error: Could not open EXR file {exr_path}")
            return False

        base_path = os.path.dirname(exr_path)
        base_filename_raw, ext = os.path.splitext(os.path.basename(exr_path))
        
        parts = base_filename_raw.split('.')
        base_filename = parts[0]
        frame_number = ""
        if len(parts) > 1 and parts[-1].isdigit():
            frame_number = parts[-1]
            base_filename = ".".join(parts[:-1])

        print(f"Splitting EXR: {os.path.basename(exr_path)}")

        crypto_channel_names = []
        crypto_channel_data = [] # To store numpy arrays of crypto data
        crypto_specs = [] # To store ImageSpec for crypto channels

        num_subimages = get_number_of_subimages(input_image)
        print(f"DEBUG: Detected {num_subimages} subimages in EXR.")

        if num_subimages > 1:
            # --- Scenario 1: Multi-subimage EXR (each subimage is typically an AOV) ---
            print("DEBUG: Handling multi-subimage EXR.")
            subimage = 0
            while True:
                if not input_image.seek_subimage(subimage, 0):
                    print(f"DEBUG: No more subimages after {subimage}. Breaking loop.")
                    break

                image_spec = input_image.spec()
                channel_names = image_spec.channelnames
                num_channels = image_spec.nchannels
                all_channel_pixels = input_image.read_image(image_spec.format)

                print(f"\nDEBUG: Processing subimage {subimage} (OIIO Subimage Name: '{image_spec.getattribute('oiio:subimagename', '')}')")
                print(f"DEBUG:   Image dimensions: {image_spec.width}x{image_spec.height}")
                print(f"DEBUG:   Total channels in subimage: {num_channels}")
                print(f"DEBUG:   Channel names: {channel_names}")

                current_aov_name = "subimage_" + str(subimage) # Fallback
                aov_spec_name = image_spec.getattribute("oiio:subimagename", "")
                if aov_spec_name:
                    current_aov_name = aov_spec_name
                elif len(channel_names) > 0:
                    first_channel_name_parts = channel_names[0].split('.')
                    if len(first_channel_name_parts) > 1:
                        current_aov_name = first_channel_name_parts[0]
                    elif all(c in channel_names for c in ['R', 'G', 'B', 'A']):
                        current_aov_name = "beauty"
                    elif num_channels == 1 and channel_names[0] not in ['R', 'G', 'B', 'A']:
                        current_aov_name = channel_names[0].replace(' ', '_').replace('.', '_')

                print(f"DEBUG:   Deduced AOV name for subimage: '{current_aov_name}'")

                is_subimage_crypto = False
                if "cryptomatte" in current_aov_name.lower() or any("cryptomatte" in c.lower() for c in channel_names):
                    is_subimage_crypto = True
                print(f"DEBUG:   Is subimage Crypto AOV candidate: {is_subimage_crypto}")

                if is_subimage_crypto:
                    print(f"DEBUG:   Subimage {subimage} identified as Crypto AOV. Collecting channels.")
                    for c_idx, c_name in enumerate(channel_names):
                        crypto_channel_names.append(c_name)
                        crypto_channel_data.append(all_channel_pixels[:, :, c_idx])
                        temp_spec = image_spec.copy()
                        temp_spec.nchannels = 1
                        temp_spec.channelnames = [c_name]
                        crypto_specs.append(temp_spec)
                else: # Not a crypto AOV subimage, save as individual AOV file
                    aov_output_dir = os.path.join(base_path, current_aov_name)
                    os.makedirs(aov_output_dir, exist_ok=True)
                    output_aov_filename = f"{aov_output_dir}/{base_filename}_{current_aov_name}{'.' + frame_number if frame_number else ''}{ext}"
                    
                    print(f"  Saving AOV: {current_aov_name} to {os.path.basename(output_aov_filename)}")
                    print(f"DEBUG:   Output AOV path: {output_aov_filename}")
                    print(f"DEBUG:   AOV will have {num_channels} channels: {channel_names}")

                    output_spec = image_spec.copy()
                    output_spec.nchannels = num_channels
                    output_spec.channelnames = channel_names
                    output_spec.set_format(image_spec.format)

                    out_file = OIIO.ImageOutput.create(output_aov_filename)
                    if not out_file:
                        print(f"Error: Could not create output file {output_aov_filename}")
                        subimage += 1
                        continue
                    out_file.open(output_aov_filename, spec=output_spec)
                    out_file.write_image(all_channel_pixels)
                    out_file.close()
                
                subimage += 1
        else:
            # --- Scenario 2: Single-subimage EXR with many packed AOVs as channels ---
            print("DEBUG: Handling single-subimage EXR with packed AOVs.")
            input_image.seek_subimage(0, 0) # Ensure we are at the first and only subimage
            image_spec = input_image.spec()
            channel_names = image_spec.channelnames
            all_channel_pixels = input_image.read_image(image_spec.format)

            grouped_aov_channels = {} # { "AOV_name": {"indices": [idx1, idx2], "names": ["R", "G"], "spec_base": ImageSpec_copy } }
            
            for c_idx, c_name in enumerate(channel_names):
                aov_prefix = "beauty" # Default for R, G, B, A
                is_crypto_channel = False

                # Determine AOV prefix and if it's a crypto channel
                if c_name in ["R", "G", "B", "A"]:
                    aov_prefix = "beauty"
                elif "cryptomatte" in c_name.lower():
                    # Crypto channels often named like CryptomatteMaterial.R, CryptomatteObject.G
                    if "." in c_name:
                        aov_prefix = c_name.split('.')[0]
                    else:
                        aov_prefix = "Cryptomatte" # Fallback if not dotted
                    is_crypto_channel = True
                elif "." in c_name:
                    aov_prefix = c_name.split('.')[0] # e.g., "DiffuseFilter" from "DiffuseFilter.R"
                else: # Single channel AOV like Z, P, N, or other custom single channels
                    aov_prefix = c_name

                print(f"DEBUG:   Channel '{c_name}' (index {c_idx}) -> Deduced AOV: '{aov_prefix}', Is Crypto: {is_crypto_channel}")

                if is_crypto_channel:
                    crypto_channel_names.append(c_name)
                    crypto_channel_data.append(all_channel_pixels[:, :, c_idx])
                    temp_spec = image_spec.copy()
                    temp_spec.nchannels = 1
                    temp_spec.channelnames = [c_name]
                    crypto_specs.append(temp_spec)
                else:
                    if aov_prefix not in grouped_aov_channels:
                        grouped_aov_channels[aov_prefix] = {"indices": [], "names": [], "spec_base": image_spec.copy()}
                    grouped_aov_channels[aov_prefix]["indices"].append(c_idx)
                    grouped_aov_channels[aov_prefix]["names"].append(c_name.split('.')[-1] if "." in c_name else c_name) # Use R from DiffuseFilter.R, or Z from Z

            # Now, save each grouped AOV
            for aov_name, data in grouped_aov_channels.items():
                if not data["indices"]:
                    continue # Skip empty groups

                aov_pixels_to_save = all_channel_pixels[:, :, data["indices"]]

                aov_output_dir = os.path.join(base_path, aov_name)
                os.makedirs(aov_output_dir, exist_ok=True)
                output_aov_filename = f"{aov_output_dir}/{base_filename}_{aov_name}{'.' + frame_number if frame_number else ''}{ext}"

                print(f"  Saving AOV: {aov_name} to {os.path.basename(output_aov_filename)}")
                print(f"DEBUG:   Output AOV path: {output_aov_filename}")
                print(f"DEBUG:   AOV will have {len(data['names'])} channels: {data['names']}")

                output_spec = data["spec_base"].copy()
                output_spec.nchannels = len(data["names"])
                output_spec.channelnames = data["names"]
                output_spec.set_format(image_spec.format)

                out_file = OIIO.ImageOutput.create(output_aov_filename)
                if not out_file:
                    print(f"Error: Could not create output file {output_aov_filename}")
                    continue
                out_file.open(output_aov_filename, spec=output_spec)
                out_file.write_image(aov_pixels_to_save)
                out_file.close()

        input_image.close() # Close the input EXR file

        # --- Process Collected Crypto Channels ---
        if crypto_channel_data:
            print("\nDEBUG: Processing collected Crypto channels.")
            
            # Use the spec from the first crypto channel for output spec creation
            # Fallback for empty crypto_specs if only data was collected (shouldn't happen with this logic)
            if not crypto_specs and channel_names: # Fallback if no specific crypto_specs but general channels exist
                first_crypto_spec = image_spec.copy() # Use the main image_spec as a base
                first_crypto_spec.nchannels = 1
                first_crypto_spec.channelnames = [channel_names[0]] # Just use first general channel name
                first_crypto_spec.set_format(OIIO.FLOAT) # Default to float if no format inferred
            elif crypto_specs:
                first_crypto_spec = crypto_specs[0]
            else: # Absolutely no spec info, create a default minimal spec
                first_crypto_spec = OIIO.ImageSpec(image_spec.width, image_spec.height, 1, OIIO.FLOAT)
                first_crypto_spec.channelnames = ["unknown_crypto"]

            crypto_output_dir = os.path.join(base_path, "Crypto")
            os.makedirs(crypto_output_dir, exist_ok=True)
            crypto_output_filename = f"{crypto_output_dir}/{base_filename}_Crypto{'.' + frame_number if frame_number else ''}{ext}"

            print(f"  Saving Crypto AOVs to {os.path.basename(crypto_output_filename)}")
            print(f"DEBUG:   Crypto output path: {crypto_output_filename}")
            print(f"DEBUG:   Crypto channel names: {crypto_channel_names}")

            if len(crypto_channel_data) > 0 and all(d.shape == crypto_channel_data[0].shape for d in crypto_channel_data):
                stacked_crypto_data = np.stack(crypto_channel_data, axis=2)
                print(f"DEBUG:   Stacked crypto data shape: {stacked_crypto_data.shape}")
            else:
                print("Error: Crypto channel data shapes mismatch. Cannot stack and save.")
                return False
            
            crypto_out_spec = first_crypto_spec.copy()
            crypto_out_spec.nchannels = len(crypto_channel_data)
            crypto_out_spec.channelnames = crypto_channel_names
            crypto_out_spec.set_format(first_crypto_spec.format)

            crypto_out_file = OIIO.ImageOutput.create(crypto_output_filename)
            if not crypto_out_file:
                print(f"Error: Could not create crypto output file {crypto_output_filename}")
                return False
            out_file.open(crypto_output_filename, spec=crypto_out_spec)
            out_file.write_image(stacked_crypto_data)
            out_file.close()

        print(f"Successfully split EXR AOVs for {os.path.basename(exr_path)}")
        return True

    except Exception as e:
        print(f"An error occurred while splitting EXR AOVs for {os.path.basename(exr_path)}: {e}")
        import traceback
        traceback.print_exc()
        return False