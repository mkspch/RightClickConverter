import sys
import os

# This allows the script to find the 'converter' module.
sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for the EXR (ACEScg) sequence to sRGB JPG sequence conversion.
    """
    try:
        if len(sys.argv) < 2:
            print("Error: No file path provided.")
            print("Press Enter to exit.")
            input()
            return

        file_path = sys.argv[1]

        if not os.path.exists(file_path):
            print(f"Error: The file '{file_path}' does not exist.")
            print("Press Enter to exit.")
            input()
            return

        print(f"File provided for EXR sequence: {file_path}")
        
        success = converter.convert_exr_to_srgb_jpg_sequence(file_path)

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