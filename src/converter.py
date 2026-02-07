import os
import subprocess
import tempfile
import shutil
import numpy as np
# from . import utils # Removed relative import
import utils # Changed to absolute import

try:
    import PyOpenColorIO as OCIO
    import OpenImageIO as OIIO
except ImportError:
    print("FATAL ERROR: PyOpenColorIO or OpenImageIO not found.")
    print("Please ensure these libraries are installed in the portable python environment.")
    OCIO = None
    OIIO = None

# --- Constants ---
# In the final version, the installer will place the ffmpeg binary in a known location.
# For now, we assume it's in the system's PATH.
FFMPEG_EXE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ffmpeg', 'bin', 'ffmpeg.exe'))

def convert_mp4_to_png_sequence(video_path):
    """
    Converts an MP4 video file into a sequence of PNG images.

    Args:
        video_path (str): The full path to the input video file.

    Returns:
        bool: True if successful, False otherwise.
    """
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
        FFMPEG_EXE, # Use the full path to ffmpeg
        '-i', video_path,
        output_pattern
    ]

    print(f"FFmpeg Command: {' '.join(command)}") # Print the command
    
    try:
        # Run FFmpeg without capturing output, so it prints directly to console
        subprocess.run(command, check=True, capture_output=False, text=True) 
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
    """
    Converts an MP4 video file into a sequence of JPG images.

    Args:
        video_path (str): The full path to the input video file.
        quality (int): JPEG quality from 1 (worst) to 100 (best).

    Returns:
        bool: True if successful, False otherwise.
    """
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
    command = [
        FFMPEG_EXE, # Use the full path to ffmpeg
        '-i', video_path,
        '-q:v', str(quality), # Set JPEG quality
        output_pattern
    ]

    print(f"FFmpeg Command: {' '.join(command)}") # Print the command
    
    try:
        # Run FFmpeg without capturing output, so it prints directly to console
        subprocess.run(command, check=True, capture_output=False, text=True) 
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
    """
    Converts an image sequence (e.g., PNG, EXR) into an MP4 video.

    Args:
        first_file_path (str): The path to the first file in the sequence.
        framerate (int): The framerate of the output video.
        output_path (str, optional): The full path for the output video.
                                     If None, it's generated automatically.

    Returns:
        bool: True if successful, False otherwise.
    """
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
        # Try to create a sensible output filename
        base_name = os.path.basename(sequence_pattern).split('%')[0].rstrip('._-')
        if not base_name:
            base_name = "output" # fallback
        output_path = os.path.join(output_dir, f"{base_name}.mp4")

    print(f"Starting conversion of sequence {os.path.basename(sequence_pattern)} to MP4...")

    command = [
        FFMPEG_EXE,
        '-framerate', str(framerate),
        '-start_number', str(start_frame),
        '-i', sequence_pattern,
        '-c:v', 'libx264',      # H.264 codec
        '-pix_fmt', 'yuv420p',  # Standard pixel format for compatibility
        '-y',                  # Overwrite output file if it exists
        output_path
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
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
    """
    Converts an EXR sequence from ACEScg colorspace to an sRGB MP4 video.
    This function performs the color conversion in Python using OpenColorIO
    and OpenImageIO, creating a temporary PNG sequence which is then
    encoded with FFmpeg.

    Args:
        first_file_path (str): The path to the first file in the sequence.
        framerate (int): The framerate of the output video.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not OCIO or not OIIO:
        return False

    exr_files, start_frame, sequence_pattern = utils.find_sequence_files(first_file_path)

    if not exr_files:
        print("Error: Could not find EXR sequence.")
        return False
        
    output_dir = os.path.dirname(first_file_path)
    base_name = os.path.basename(sequence_pattern).split('%')[0].rstrip('._-')
    final_output_path = os.path.join(output_dir, f"{base_name}_sRGB.mp4")

    # --- Setup for OCIO ---
    ocio_config_path = os.path.join(os.path.dirname(__file__), 'config', 'aces_1.2', 'config.ocio')
    if not os.path.exists(ocio_config_path):
        print(f"CRITICAL ERROR: OCIO config not found at {ocio_config_path}")
        return False

    try:
        config = OCIO.Config.CreateFromFile(ocio_config_path)
        # NOTE: The names "ACES - ACEScg" and "Output - sRGB" are defined in the config.ocio file.
        processor = config.getProcessor("ACEScg", "Output - sRGB")
    except Exception as e:
        print(f"OCIO Error: Could not set up color processor. {e}")
        return False

    # --- Setup FFmpeg subprocess for direct piping ---

    # Get first frame's dimensions to set output_width and output_height
    # This assumes all frames in the sequence have the same dimensions
    first_img_buf = OIIO.ImageBuf(exr_files[0])
    output_width = first_img_buf.spec().width
    output_height = first_img_buf.spec().height

    # Define pixel format for FFmpeg input (rgb48le for 16-bit RGB)
    ffmpeg_pixel_format = "rgb48le"

    # Construct FFmpeg command
    ffmpeg_cmd = [
        FFMPEG_EXE,
        "-hide_banner", "-loglevel", "info", "-y",
        "-f", "rawvideo",
        "-pixel_format", ffmpeg_pixel_format,
        "-video_size", f"{output_width}x{output_height}",
        "-framerate", str(framerate),
        "-i", "pipe:0",  # Input from pipe
        "-c:v", "libx264",      # H.264 codec (can be made configurable)
        "-pix_fmt", "yuv420p",  # Standard pixel format for compatibility (can be made configurable)
        "-preset", "medium",    # Encoding preset (can be made configurable)
        "-crf", "23",           # Constant Rate Factor (quality setting) (can be made configurable)
        final_output_path
    ]

    print(f"DEBUG: FFmpeg command: {' '.join(ffmpeg_cmd)}")

    try:
        ffproc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print(f"CRITICAL ERROR: FFmpeg executable not found at '{FFMPEG_EXE}'.")
        print("Please ensure FFmpeg is correctly installed.")
        return False
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to start FFmpeg subprocess: {e}")
        return False

    # --- Process each EXR frame and pipe to FFmpeg ---
    print("Starting color conversion and piping to FFmpeg...")
    try:
        for i, exr_path in enumerate(exr_files):
            print(f"  Processing frame {start_frame + i} ({i+1}/{len(exr_files)}): {os.path.basename(exr_path)}")
            
            # Read EXR using OpenImageIO
            img_buf = OIIO.ImageBuf(exr_path)

            # Explicitly drop alpha channel if present, to ensure 3-channel RGB for FFmpeg
            OIIO.ImageBufAlgo.channels(img_buf, img_buf, (0,1,2))
            
            # Apply OCIO color transform directly to the ImageBuf
            # Note: "ACEScg" and "Output - sRGB" are hardcoded here, make configurable if needed
            success_ocio = OIIO.ImageBufAlgo.colorconvert(img_buf, img_buf, "ACEScg", "Output - sRGB", colorconfig=ocio_config_path)
            if not success_ocio:
                print(f"OCIO Color Convert failed for frame {start_frame + i}. Check OCIO config and colorspace names.")
                return False # Critical failure for this frame

            # Resize to the consistent output dimensions before extracting pixels
            if img_buf.spec().width != output_width or img_buf.spec().height != output_height:
                print(f"DEBUG: Resizing frame {start_frame + i} from {img_buf.spec().width}x{img_buf.spec().height} to {output_width}x{output_height}")
                img_buf = OIIO.ImageBufAlgo.resize(img_buf, "box", roi=OIIO.ROI(0, output_width, 0, output_height))

            # Get pixels from the transformed ImageBuf directly in UINT16 format
            # OIIO handles the float-to-UINT16 conversion internally here, with proper scaling/clamping
            pixels_raw = img_buf.get_pixels(OIIO.UINT16)

            # Debugging raw pixel data
            print(f"DEBUG: Frame {start_frame + i} - Pixels raw shape: {pixels_raw.shape}, dtype: {pixels_raw.dtype}")
            expected_bytes = output_width * output_height * 3 * 2 # 3 channels, 2 bytes per uint16
            actual_bytes = len(pixels_raw.tobytes())
            print(f"DEBUG: Frame {start_frame + i} - Pixels raw byte length: {actual_bytes}, Expected: {expected_bytes}")
            if actual_bytes != expected_bytes:
                print("CRITICAL ERROR: Mismatch in pixel data byte length!")
                return False

            # Write the raw pixel data to FFmpeg's stdin
            ffproc.stdin.write(pixels_raw.tobytes())

        print("Color conversion and piping complete. Waiting for FFmpeg to finish...")
        ffproc.stdin.close() # Close stdin to signal EOF to FFmpeg
        stdout, stderr = ffproc.communicate()

        if ffproc.returncode != 0:
            print(f"ERROR: FFmpeg exited with error code {ffproc.returncode}")
            print("FFmpeg stdout:\n", stdout.decode())
            print("FFmpeg stderr:\n", stderr.decode())
            return False
        else:
            print("FFmpeg encoding finished successfully!")
            return True

    except Exception as e:
        print(f"An error occurred during the conversion process: {e}")
        import traceback
        traceback.print_exc()
        return False