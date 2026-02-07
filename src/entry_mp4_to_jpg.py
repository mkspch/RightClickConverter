import sys
import os
import argparse # Import argparse for command-line arguments

# This allows the script to find the 'converter' module
# when called from an external process.
sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for the MP4 to JPG sequence conversion.
    """
    parser = argparse.ArgumentParser(description="Convert MP4 video to JPG sequence.")
    parser.add_argument("video_path", help="Path to the input MP4 video file.")
    parser.add_argument("--quality", type=int, default=90, 
                        help="JPEG quality (1-100). Default is 90.")

    args = parser.parse_args()

    try:
        video_path = args.video_path
        quality = args.quality

        if not os.path.exists(video_path):
            print(f"Error: The file '{video_path}' does not exist.")
            print("Press Enter to exit.") # Keeps the window open to see the error
            input()
            return
            
        print(f"File to convert: {video_path}")
        print(f"Using JPEG quality: {quality}")
        success = converter.convert_mp4_to_jpg_sequence(video_path, quality=quality)

        if success:
            print("\nConversion finished successfully!")
        else:
            print("\nConversion failed. Please check the errors above.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Press Enter to exit.")
        input() # Waits for user input


if __name__ == '__main__':
    main()
