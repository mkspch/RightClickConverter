import os
import subprocess
import tempfile
import shutil
from . import utils

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
FFMPEG_EXE = "ffmpeg" 

# --- Conversion Functions ---

def convert_mp4_to_png_sequence(video_path):
    """
    Converts an MP4 video file into a sequence of PNG images.

    Args:
        video_path (str): The full path to the input video file.

    Returns:
        bool: True if successful, False otherwise.
    """
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

    try:
        # Use Popen to have more control over output, but for now, run is fine
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully converted video to PNG sequence in {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print("Error during FFmpeg execution:")
        print(f"Command: {' '.join(command)}")
        print(f"Return Code: {e.returncode}")
        print(f"Output: {e.stdout}")
        print(f"Error Output: {e.stderr}")
        return False


def convert_sequence_to_mp4(first_file_path, framerate=24, output_path=None):
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

def convert_exr_to_srgb_mp4(first_file_path, framerate=24):
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

    # --- Create a temporary directory for intermediate PNGs ---
    temp_dir = tempfile.mkdtemp(prefix="exr_to_png_")
    print(f"Created temporary directory for PNG conversion: {temp_dir}")

    try:
        # --- Convert each EXR to a 16-bit PNG in the temp directory ---
        print("Starting color conversion from EXR to temporary PNG sequence...")
        first_png_file = ""
        for i, exr_path in enumerate(exr_files):
            current_frame_num = start_frame + i
            print(f"  Processing frame {current_frame_num} ({i+1}/{len(exr_files)}): {os.path.basename(exr_path)}")
            
            # Read EXR using OpenImageIO
            img_buf = OIIO.ImageBuf(exr_path)
            
            # Process pixels with OCIO
            # OIIO buffer protocol allows direct pixel access
            pixels = img_buf.get_pixels(OIIO.FLOAT)
            processor.apply(pixels)
            
            # Create a new buffer for the transformed pixels
            out_buf = OIIO.ImageBuf(img_buf.spec())
            out_buf.set_pixels(pixels)
            
            # Write to a 16-bit PNG
            temp_png_path = os.path.join(temp_dir, f"frame_{current_frame_num:04d}.png")
            out_buf.write(temp_png_path, "uint16")
            
            if i == 0:
                first_png_file = temp_png_path

        print("Color conversion complete.")

        # --- Encode the temporary PNG sequence to MP4 ---
        success = convert_sequence_to_mp4(
            first_file_path=first_png_file,
            framerate=framerate,
            output_path=final_output_path
        )
        return success

    except Exception as e:
        print(f"An error occurred during the conversion process: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # --- Clean up the temporary directory ---
        if os.path.exists(temp_dir):
            print(f"Cleaning up temporary directory: {temp_dir}")
            shutil.rmtree(temp_dir)
