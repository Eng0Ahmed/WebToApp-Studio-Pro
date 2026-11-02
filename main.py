import sys
import os

# Ensure current working directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    # Allow choosing classic UI via argument '--classic' if requested
    if "--classic" in sys.argv:
        from gui.app_window import AppWindow
        app = AppWindow()
        app.mainloop()
        return

    try:
        from gui.web_window import WebWindow
        WebWindow.run()
    except Exception as e:
        print(f"Warning: Failed to launch modern Web UI ({e}). Falling back to Classic UI...")
        from gui.app_window import AppWindow
        app = AppWindow()
        app.mainloop()

if __name__ == "__main__":
    main()
