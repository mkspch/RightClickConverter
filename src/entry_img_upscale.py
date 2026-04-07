import sys
import os
import glob
import traceback

# This allows the script to find the 'converter' module.
sys.path.append(os.path.dirname(__file__))

import converter

def main():
    """
    Entry point for the Image Upscale (Real-ESRGAN) conversion.
    Processes selected image files and allows user to choose an ESRGAN model.
    """
    try:
        if len(sys.argv) < 2:
            print("Error: No image file paths provided.")
            print("Press Enter to exit.")
            input()
            return

        image_paths = sys.argv[1:]
        existing_image_paths = [path for path in image_paths if os.path.exists(path)]

        if not existing_image_paths:
            print("Error: No valid image files found among the selected items.")
            print("Press Enter to exit.")
            input()
            return

        # --- Model Selection Logic ---
        REALESRGAN_DIR = os.path.join(os.environ.get('LOCALAPPDATA'), 'Programs', 'TS_Toolbox', 'realesrgan')
        MODEL_DIR = os.path.join(REALESRGAN_DIR, 'models')

        if not os.path.exists(MODEL_DIR):
            print(f"Error: Real-ESRGAN models directory not found at '{MODEL_DIR}'.")
            print("Please ensure Real-ESRGAN is correctly installed (run install.bat).")
            print("Press Enter to exit.")
            input()
            return

        available_models = {}
        model_files = glob.glob(os.path.join(MODEL_DIR, '*.bin'))
        
        if not model_files:
            print(f"Error: No Real-ESRGAN model files (.bin) found in '{MODEL_DIR}'.")
            print("Please ensure Real-ESRGAN is correctly installed and its models are present.")
            print("Press Enter to exit.")
            input()
            return

        print("\nAvailable Real-ESRGAN Models:")
        for i, model_path in enumerate(model_files):
            model_name = os.path.splitext(os.path.basename(model_path))[0]
            available_models[str(i + 1)] = model_name
            print(f"  {i + 1}: {model_name}")

        selected_model_name = None
        while selected_model_name is None:
            choice = input("Enter the number of the model to use (or 1 for default if available): ").strip()
            if choice in available_models:
                selected_model_name = available_models[choice]
            else:
                print("Invalid choice. Please enter a number from the list.")

        print(f"\nUsing model: {selected_model_name}")

        print(f"Starting Real-ESRGAN Upscale for {len(existing_image_paths)} image(s)...")
        
        success = converter.upscale_image_realesrgan(existing_image_paths, model_name=selected_model_name)

        if success:
            print("\nImage Upscale finished successfully!")
        else:
            print("\nImage Upscale failed. Please check the errors above.")
    except Exception as e:
        print(f"\nAn unhandled error occurred: {e}")
        traceback.print_exc()
    finally:
        print("Press Enter to exit.")
        input() # Waits for user input


if __name__ == '__main__':
    main()