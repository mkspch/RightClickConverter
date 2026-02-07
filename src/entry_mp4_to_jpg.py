import sys
import os

# This allows the script to find the 'converter' module
# when called from an external process.
sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for the MP4 to JPG sequence conversion.
    """
    # The first argument (sys.argv[0]) is the script name.
    # The second argument (sys.argv[1]) is the file path from the context menu.
    if len(sys.argv) < 2:
        print("Error: No file path provided.")
        print("Press Enter to exit.") # Keeps the window open to see the error
        input()
        return

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: The file '{video_path}' does not exist.")
        print("Press Enter to exit.")
        input()
        return
        
    print(f"File to convert: {video_path}")
    success = converter.convert_mp4_to_jpg_sequence(video_path)

    if success:
        print("
Conversion finished successfully!")
    else:
        print("
Conversion failed. Please check the errors above.")
    print("Press Enter to exit.")
    input() # Waits for user input


if __name__ == '__main__':
    main()
