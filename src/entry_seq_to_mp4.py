import sys
import os

# This allows the script to find the 'converter' module.
sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for the image sequence to MP4 conversion.
    """
    if len(sys.argv) < 2:
        print("Error: No file path provided.")
        input("Press Enter to exit.")
        return

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Error: The file '{file_path}' does not exist.")
        input("Press Enter to exit.")
        return

    print(f"File provided for sequence: {file_path}")
    # We can add more logic here to ask for framerate if we want
    # For now, we'll use the default.
    success = converter.convert_sequence_to_mp4(file_path, framerate=24)

    if success:
        print("
Conversion finished successfully!")
    else:
        print("
Conversion failed. Please check the errors above.")
    
    input("Press Enter to exit.")


if __name__ == '__main__':
    main()
