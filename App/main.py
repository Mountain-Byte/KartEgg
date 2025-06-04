import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Für Windows 8.1 und neuer
except:
    try:
        ctypes.windll.user32.SetProcessDPIAware()  # Für Windows 7
    except:
        pass

from ui.group_selection import select_group
from ui.main_ui import start_main_app

def main():
    group = select_group()
    if group:
        start_main_app(group)

if __name__ == "__main__":
    main()