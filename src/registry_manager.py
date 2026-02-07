import sys
import os
import winreg

# Configuration for the context menu entries
# These paths are relative to the 'RightClickConverter' installation directory
PYTHON_EXECUTABLE_RELATIVE = "python/python.exe"
SCRIPTS_DIR_RELATIVE = "scripts/src"

MENU_NAME = "RightClickConverter"
MENU_TITLE = "Right Click Converter"
SUBMENU_KEY = "RightClickConverter.Menu"

# List of submenu items: (display_text, script_name)
SUBMENU_ITEMS = [
    ("Convert to PNG Sequence", "entry_mp4_to_png.py"),
    ("Convert Sequence to MP4", "entry_seq_to_mp4.py"),
    ("Convert ACEScg Sequence to sRGB MP4", "entry_exr_to_mp4.py"),
]

def get_install_root_path():
    """Determines the root installation path of RightClickConverter."""
    # Assumes this script is in %TOOL_DIR%\scripts\src
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up two levels: src -> scripts -> RightClickConverter
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
        # Create top-level menu entry (appears when right-clicking any file)
        key_path = r"*\shell\%s" % MENU_NAME
        with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_TITLE)
            winreg.SetValueEx(key, "ExtendedSubCommandsKey", 0, winreg.REG_SZ, SUBMENU_KEY)
        print(f"Added top-level menu: '{MENU_TITLE}'")

        # Define submenu items
        for display_text, script_name in SUBMENU_ITEMS:
            command_key_path = r"%s\shell\%s" % (SUBMENU_KEY, display_text.replace(" ", "")) # Use display text as key for simplicity
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_key_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, display_text)
                
                # Use %%V to pass the selected file/folder path
                command = f'"{python_exe}" "{os.path.join(scripts_path, script_name)}" "%%V"'
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
    full_key_path_from_hkey is the full path from hkey (e.g., r"*\shell\RightClickConverter").
    """
    try:
        # Extract parent path and key name from full_key_path_from_hkey
        path_parts = full_key_path_from_hkey.split('\\')
        key_to_delete_name = path_parts[-1]
        parent_path = '\\'.join(path_parts[:-1])

        with winreg.OpenKey(hkey, parent_path, 0, winreg.KEY_ALL_ACCESS) as parent_key_handle:
            try:
                # Enumerate and delete subkeys if any
                while True:
                    subkey_name_to_delete = winreg.EnumKey(winreg.OpenKey(parent_key_handle, key_to_delete_name, 0, winreg.KEY_ALL_ACCESS), 0)
                    recursive_delete_key(parent_key_handle, os.path.join(key_to_delete_name, subkey_name_to_delete))
            except OSError: # No more subkeys
                pass # All subkeys deleted or none existed
            except FileNotFoundError: # Key_to_delete_name doesn't exist
                pass
            
            # Delete the key itself
            winreg.DeleteKey(parent_key_handle, key_to_delete_name)
    except FileNotFoundError:
        pass # Key or its parent already doesn't exist, nothing to delete
    except Exception as e:
        print(f"Error in recursive_delete_key for {os.path.join(str(hkey), full_key_path_from_hkey)}: {e}")
        raise # Re-raise other unexpected errors

def remove_context_menu_entries():
    try:
        # Attempt to remove using winreg.DeleteTree (Python 3.8+ specific)
        print("Attempting to remove context menu entries using winreg.DeleteTree...")
        
        # Delete submenu definitions first (e.g., HKEY_CLASSES_ROOT\RightClickConverter.Menu)
        winreg.DeleteTree(winreg.HKEY_CLASSES_ROOT, SUBMENU_KEY)
        print(f"Removed submenu key: '{SUBMENU_KEY}'")

        # Delete top-level menu entry (e.g., HKEY_CLASSES_ROOT\*\shell\RightClickConverter)
        winreg.DeleteTree(winreg.HKEY_CLASSES_ROOT, r"*\shell\%s" % MENU_NAME)
        print(f"Removed top-level menu: '{MENU_TITLE}'")
        
        print("Context menu entries removed successfully using winreg.DeleteTree.")
        return True
    except AttributeError:
        # Fallback for Python versions < 3.8 or environments where DeleteTree is missing
        print("winreg.DeleteTree not available, falling back to recursive deletion.")
        try:
            # Delete submenu definitions first
            recursive_delete_key(winreg.HKEY_CLASSES_ROOT, SUBMENU_KEY)
            print(f"Removed submenu key: '{SUBMENU_KEY}' using recursive_delete_key.")

            # Delete top-level menu entry using recursive fallback
            recursive_delete_key(winreg.HKEY_CLASSES_ROOT, r"*\shell\%s" % MENU_NAME)
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
