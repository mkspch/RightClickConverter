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

FFMPEG_EXE = r"C:\Users\nhb\AppData\Local\Programs\TS_Toolbox\ffmpeg\bin\ffmpeg.exe"
FFPROBE_EXE = r"C:\Users\nhb\AppData\Local\Programs\TS_Toolbox\ffmpeg\bin\ffprobe.exe"

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
    total_width_per_row = 0
    
    try:
        # Load images and find max height, and sum up widths for scaling reference
        for path in image_paths:
            if not os.path.exists(path):
                print(f"Warning: Image not found and skipped: {path}")
                continue
            img = Image.open(path)
            images.append(img)
            if img.height > max_height:
                max_height = img.height
            total_width_per_row += img.width

        if not images:
            print("Error: No valid images found to create contact sheet.")
            return False

        # Calculate average aspect ratio if needed, or target width per column
        # For simplicity, we'll make each column's images max_height tall.
        # Max width needed for a column will be max(img.width for img in images resized to max_height)
        
        resized_images = []
        max_resized_width = 0
        for img in images:
            if img.height != max_height:
                # Resize image maintaining aspect ratio
                aspect_ratio = img.width / img.height
                new_width = int(max_height * aspect_ratio)
                resized_img = img.resize((new_width, max_height), Image.LANCZOS)
            else:
                resized_img = img
            resized_images.append(resized_img)
            if resized_img.width > max_resized_width:
                max_resized_width = resized_img.width

        # Now, calculate the canvas size
        num_images = len(resized_images)
        rows = (num_images + columns - 1) // columns
        
        canvas_width = (max_resized_width * columns) + (padding * (columns + 1))
        canvas_height = (max_height * rows) + (padding * (rows + 1))

        contact_sheet = Image.new('RGB', (canvas_width, canvas_height), color = (0, 0, 0)) # Black background

        x_offset = padding
        y_offset = padding
        
        for i, img in enumerate(resized_images):
            # Calculate position for current image
            col = i % columns
            row = i // columns

            x_pos = (col * (max_resized_width + padding)) + padding
            y_pos = (row * (max_height + padding)) + padding
            paste_y = y_pos + (max_height - img.height) // 2

            contact_sheet.paste(img, (x_pos, paste_y))
            
        output_path = os.path.join(os.path.dirname(image_paths[0]), output_filename)
        contact_sheet.save(output_path)
        print(f"Successfully created contact sheet: {output_path}")
        return True

    except Exception as e:
        print(f"Error creating contact sheet: {e}")
        return False

def create_video_contact_sheet(video_paths, output_filename="video_contact_sheet.mp4", columns=2, target_height_per_video=360, snippet_duration=5):
    """
    Creates an animated video contact sheet from multiple video files.
    It extracts a short segment from each video, scales them, arranges them in a grid,
    and then outputs a single MP4 video.

    Args:
        video_paths (list): A list of full paths to the input video files.
        output_filename (str): The desired filename for the output video contact sheet.
        columns (int): The number of columns for the contact sheet grid.
        target_height_per_video (int): The desired height for each video snippet in the grid.
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

        # --- Phase 1: Extract video snippets and gathering video infoの流れ ---
        print("Extracting video snippets and gathering video info...")
        shortest_duration = float('inf')
        for i, video_path in enumerate(video_paths):
            if not os.path.exists(video_path):
                print(f"Warning: Video not found and skipped: {video_path}")
                continue

            # Probe video for duration, width, height
            probe_cmd_list = [
                f'"{FFPROBE_EXE}"', '-v', 'error', '-select_streams', 'v:0',
                '-show_entries', 'stream=width,height,duration', '-of', 'default=noprint_wrappers=1', f'"{video_path}"'
            ]
            probe_cmd = " ".join(probe_cmd_list)
            print(f"DEBUG: FFPROBE_EXE command: {probe_cmd}")
            probe_output = subprocess.check_output(probe_cmd, stderr=subprocess.STDOUT, text=True, shell=True)
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

            # Determine actual snippet duration (don't exceed video length)
            actual_snippet_duration = min(snippet_duration, duration)
            if actual_snippet_duration <= 0:
                print(f"Warning: Video {os.path.basename(video_path)} is too short to extract a snippet. Skipping.")
                continue

            # Input video path for FFmpeg
            input_args.extend(['-i', video_path])

            extracted_snippets.append({
                "path": video_path, # Keep original path for direct FFmpeg input
                "index": i, # Store original input index
                "original_width": width,
                "original_height": height,
                "duration": duration,
                "scaled_height": target_height_per_video,
                "scaled_width": int(width * (target_height_per_video / height)) # Initial scale guess
            })
            print(f"  Processed video {os.path.basename(video_path)} (Duration: {duration:.1f}s)")

        if not extracted_snippets:
            print("Error: No valid video files found to create contact sheet after processing.")
            return False

        # Ensure snippet duration does not exceed the shortest video
        final_snippet_duration = min(snippet_duration, shortest_duration)
        if final_snippet_duration <= 0:
            print("Error: All selected videos are too short for snippet duration. Cannot create contact sheet.")
            return False
        
        # Determine max scaled width to align columns based on snippets' original dimensions
        max_scaled_width = 0
        for snippet_info in extracted_snippets:
            # Re-calculate scaled width based on target_height_per_video and original aspect ratio
            scaled_width_for_target_height = int(snippet_info["original_width"] * (target_height_per_video / snippet_info["original_height"]))
            snippet_info["scaled_width_final"] = scaled_width_for_target_height
            if scaled_width_for_target_height > max_scaled_width:
                max_scaled_width = scaled_width_for_target_height
        
        # Ensure max_scaled_width is even for x264 compatibility
        if max_scaled_width % 2 != 0:
            max_scaled_width += 1


        # --- Phase 2: Construct FFmpeg filter_complex for grid arrangement ---
        filter_parts = []
        
        # Prepare inputs and scale/pad each video stream to a uniform size
        # We need to explicitly handle each video input
        stream_labels = []
        for i, snippet_info in enumerate(extracted_snippets):
            # [i:v] selects the video stream from the i-th input file
            # trim=start=0:duration sets the snippet duration
            # setpts=PTS-STARTPTS normalizes timestamps
            # scale ensures aspect ratio and targets height, then pad adds black bars for uniform width
            filter_parts.append(
                f"[{i}:v]trim=start=0:duration={final_snippet_duration},setpts=PTS-STARTPTS,"
                f"scale={max_scaled_width}:{target_height_per_video}:force_original_aspect_ratio=decrease,setsar=1,"
                f"pad={max_scaled_width}:{target_height_per_video}:(ow-iw)/2:(oh-ih)/2[v{i}]"
            )
            stream_labels.append(f"[v{i}]")

        # Arrange snippets into a grid using hstack and vstack
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
                    # Add a black filler if there are not enough videos for a full row
                    filler_width = max_scaled_width
                    filler_height = target_height_per_video
                    filter_parts.append(f"color=black:s={filler_width}x{filler_height}:d={final_snippet_duration}[fill{r}{c}]")
                    row_streams_to_stack.append(f"[fill{r}{c}]")
            
            if not row_streams_to_stack:
                continue

            num_in_row = len(row_streams_to_stack)
            if num_in_row == 1:
                # If only one video in a row, still need to label it for vstack
                filter_parts.append(f"{row_streams_to_stack[0]}split=1[h{r}]")
            else:
                filter_parts.append(f"{''.join(row_streams_to_stack)}hstack=inputs={num_in_row}:shortest=1[h{r}]")
            h_stacks_output_labels.append(f"[h{r}]")
        
        # Vertical stack all horizontal stacks
        if not h_stacks_output_labels:
            print("Error: Could not arrange video snippets into a grid.")
            return False
            
        if len(h_stacks_output_labels) == 1:
            filter_parts.append(f"{h_stacks_output_labels[0]}split=1[out]") # Split to add label
        else:
            filter_parts.append(f"{''.join(h_stacks_output_labels)}vstack=inputs={len(h_stacks_output_labels)}[out]")


        output_path = os.path.join(os.path.dirname(video_paths[0]), output_filename)

        final_ffmpeg_cmd = [
            FFMPEG_EXE,
            '-y', # Overwrite output
            *input_args, # All video inputs
            '-filter_complex', ';'.join(filter_parts),
            '-map', '[out]', # Map the final output stream
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-crf', '23', # Quality setting
            '-preset', 'medium', # Balanced speed/quality
            output_path
        ]

        print(f"Final FFmpeg Command: {' '.join(final_ffmpeg_cmd)}")
        subprocess.run(final_ffmpeg_cmd, check=True, capture_output=True, text=True, shell=True) # Use shell=True here
        
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
            f'"{FFMPEG_EXE}"', '-y', # Overwrite output file without asking
            '-i', f'"{video_path}"',
            '-vf', f'"scale={new_width}:-2"', # Resize filter
            '-c:a', 'copy', # Copy audio stream
            '-c:v', 'libx264', # Encode video with libx264
            '-pix_fmt', 'yuv420p', # Pixel format for wider compatibility
            '-crf', '23', # Quality setting, 23 is a good default
            '-preset', 'medium', # Encoding preset
            f'"{output_path}"'
        ]
        ffmpeg_cmd = " ".join(ffmpeg_cmd_list)
        print(f"Final FFmpeg Command: {ffmpeg_cmd}")

        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, shell=True)
        
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