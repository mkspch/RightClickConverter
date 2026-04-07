import sys
import os
import argparse
import traceback

sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for the image resize conversion.
    """
    parser = argparse.ArgumentParser(description="Resize an image to a specified width.")
    parser.add_argument("image_path", help="Path to the input image file.")
    parser.add_argument("--width", type=int, help="Desired new width for the image.")

    args = parser.parse_args()

    try:
        image_path = args.image_path
        new_width = args.width

        if new_width is None:
            while True:
                try:
                    width_input = input("Enter new width for the image (e.g., 1920): ")
                    new_width = int(width_input)
                    if new_width <= 0:
                        print("Width must be a positive integer.")
                        continue
                    break
                except ValueError:
                    print("Invalid input. Please enter a number.")
            
        if not os.path.exists(image_path):
            print(f"Error: The file '{image_path}' does not exist.")
            print("Press Enter to exit.")
            input()
            return
            
        print(f"Image to resize: {image_path}")
        print(f"Desired width: {new_width}")
        success = converter.convert_img_resize(image_path, new_width)

        if success:
            print("\nConversion finished successfully!")
        else:
            print("\nConversion failed. Please check the errors above.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
        traceback.print_exc()
    finally:
        print("Press Enter to exit.")
        input()


if __name__ == '__main__':
    main()
