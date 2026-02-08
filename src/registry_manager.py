import sys
import os
import winreg
import shutil # For simple bat file copy fallback

# Configuration for the context menu entries
PYTHON_EXECUTABLE_RELATIVE = "python/python.exe"
SCRIPTS_DIR_RELATIVE = "scripts/src"

MENU_NAME = "TS_Toolbox"
MENU_TITLE = "TS_Toolbox"
SUBMENU_KEY_NAME = "TS_Toolbox.Menu"
SUBMENU_KEY_FULL_PATH = r"Software\Classes\%s" % SUBMENU_KEY_NAME

# List of submenu items for regular right-click (including Contact Sheet)
SUBMENU_ITEMS = [
    ("VID > PNG", "entry_mp4_to_png.py"),
    ("VID > JPG", "entry_mp4_to_jpg.py"),
    ("IMG > MP4", "entry_seq_to_mp4.py"),
    ("EXR > MP4 (ACEScg-sRGB)", "entry_exr_to_mp4.py"),
    ("IMG > Half Size", "entry_img_half_size.py"),
    ("IMG > Resize", "entry_img_resize.py"),
    ("IMG > Contact Sheet", "entry_img_contactsheet.py"),
    ("VID > Contact Sheet", "entry_video_contact_sheet.py"),
    ("VID > Resize", "entry_vid_resize.py"), # New entry
]

def get_install_root_path():
    """Determines the root installation path of TS_Toolbox."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    install_root = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir))
    return install_root

def add_context_menu_entries():
    install_root = get_install_root_path()
    python_exe = os.path.join(install_root, PYTHON_EXECUTABLE_RELATIVE)
    scripts_path = os.path.join(install_root, SCRIPTS_DIR_RELATIVE)

    if not os.path.exists(python_exe):
        print(f"Error: Python executable not found at {python_exe}")
        return False
    if not os.path.exists(scripts_path):
        print(f"Error: Scripts directory not found at {scripts_path}")
        return False

    try:
        key_path = r"Software\Classes\*\shell\%s" % MENU_NAME
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_TITLE)
            winreg.SetValueEx(key, "ExtendedSubCommandsKey", 0, winreg.REG_SZ, SUBMENU_KEY_NAME)
        print(f"Added top-level menu: '{MENU_TITLE}'")

        for display_text, script_name in SUBMENU_ITEMS:
            command_key_path = r"%s\shell\%s" % (SUBMENU_KEY_FULL_PATH, display_text.replace(" ", ""))
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_key_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, display_text)
                
                # Wrap all commands in cmd.exe /K to keep the window open
                if display_text == "VID > JPG":
                    command_args = f'"{python_exe}" "{os.path.join(scripts_path, script_name)}" "%V" --quality 90'
                elif display_text == "IMG > Contact Sheet": # For contact sheet, pywin32 fetches files
                    command_args = f'"{python_exe}" "{os.path.join(scripts_path, script_name)}"' # No args needed, script gets selection
                elif display_text == "VID > Contact Sheet": # For video contact sheet, pywin32 fetches files
                    command_args = f'"{python_exe}" "{os.path.join(scripts_path, script_name)}"' # No args needed, script gets selection
                elif display_text == "VID > Resize": # For video resize, pywin32 fetches files
                    command_args = f'"{python_exe}" "{os.path.join(scripts_path, script_name)}"' # No args needed, script gets selection
                else:
                    command_args = f'"{python_exe}" "{os.path.join(scripts_path, script_name)}" "%V"'
                
                command = f'cmd.exe /c "{command_args}"' # Use cmd.exe /c here for production
                with winreg.CreateKey(key, "command") as cmd_key:
                    winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, command)
            print(f"  Added submenu item: '{display_text}'")
        
        print("Context menu entries added successfully. You may need to restart Explorer or reboot to see changes.")
        return True

    except Exception as e:
        print(f"Error adding registry entries: {e}")
        print("Please ensure you are running this script with Administrator privileges.")
        return False

def recursive_delete_key(hkey, full_key_path_from_hkey):
    """
    Recursively deletes a registry key and all its subkeys.
    hkey is a pre-defined key like HKEY_CLASSES_ROOT.
    full_key_path_from_hkey is the full path from hkey.
    """
    try:
        path_parts = full_key_path_from_hkey.split('\\')
        key_to_delete_name = path_parts[-1]
        parent_path = '\\'.join(path_parts[:-1])

        with winreg.OpenKey(hkey, parent_path, 0, winreg.KEY_ALL_ACCESS) as parent_key_handle:
            try:
                while True:
                    subkey_name_to_delete = winreg.EnumKey(winreg.OpenKey(parent_key_handle, key_to_delete_name, 0, winreg.KEY_ALL_ACCESS), 0)
                    recursive_delete_key(parent_key_handle, os.path.join(key_to_delete_name, subkey_name_to_delete))
            except OSError:
                pass
            except FileNotFoundError:
                pass
            
            winreg.DeleteKey(parent_key_handle, key_to_delete_name)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error in recursive_delete_key for {os.path.join(str(hkey), full_key_path_from_hkey)}: {e}")
        raise

def remove_context_menu_entries():
    try:
        print("Attempting to remove context menu entries using winreg.DeleteTree...")
        
        winreg.DeleteTree(winreg.HKEY_CURRENT_USER, SUBMENU_KEY_FULL_PATH)
        print(f"Removed submenu key: '{SUBMENU_KEY_FULL_PATH}'")

        winreg.DeleteTree(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\%s" % MENU_NAME)
        print(f"Removed top-level menu: '{MENU_TITLE}'")
        
        print("Context menu entries removed successfully using winreg.DeleteTree.")
        return True
    except AttributeError:
        print("winreg.DeleteTree not available, falling back to recursive deletion.")
        try:
            recursive_delete_key(winreg.HKEY_CURRENT_USER, SUBMENU_KEY_FULL_PATH)
            print(f"Removed submenu key: '{SUBMENU_KEY_FULL_PATH}' using recursive_delete_key.")

            recursive_delete_key(winreg.HKEY_CURRENT_USER, r"Software\Classes\*\shell\%s" % MENU_NAME)
            print(f"Removed top-level menu: '{MENU_TITLE}' using recursive_delete_key.")

            print("Context menu entries removed successfully using recursive deletion.")
            return True
        except Exception as e:
            print(f"Error during recursive deletion fallback: {e}")
            return False
    except FileNotFoundError:
        print("Registry entries not found, nothing to remove.")
        return True
    except Exception as e:
        print(f"Error removing registry entries: {e}")
        print("Please ensure you are running this script with Administrator privileges.")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python registry_manager.py [install|uninstall]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "install":
        if not add_context_menu_entries():
            sys.exit(1)
    elif command == "uninstall":
        if not remove_context_menu_entries():
            sys.exit(1)
    else:
        print(f"Invalid command: {command}. Use 'install' or 'uninstall'.")
        sys.exit(1)