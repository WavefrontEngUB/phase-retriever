import sys
import os

import platform
import wx
import tkinter as tk
import tkinter.ttk as ttk

from .interface import PhaseRetrieverGUI
from .wx_gui import wxGUI

PROGRAM_NAME = "Phase retriever"


def wxMain(data_dir=""):
    app = wx.App()
    gui = wxGUI(None, PROGRAM_NAME, search_dir=data_dir)
    gui.Show()
    app.MainLoop()

def TkMain():
    root = tk.Tk()
    style = ttk.Style()
    if platform.system() == "Linux":
        style.theme_use("clam")
    bg = style.lookup("TFrame", "background")
    b = None
    root["background"] = bg
    gui = PhaseRetrieverGUI(root, bg)
    root.mainloop()

def print_help(error_code=0, epilog=''):

    program_cmd = f"python -m {sys.modules[__name__].__package__}"

    print(f"Description: {PROGRAM_NAME} is a GUI powered software to retrieve the fase of a "
          f"highly focused electromagnetic field,\nby taking as input two recording "
          f"planes separated some distance nearby the focus.\n"
          f"It also reconstruct the longitudinal component.\nTo do so, it is necessary "
          f"to provide polarimetric images of both z-planes.")
    print(f"")
    print(f"usage: {program_cmd} [demo|download_data=<path>] [-h|-help]")
    print(f"")
    print(f"Options:")
    print(f"  demo:           Launches the program with a test dataset already loaded.")
    print(f"  download_data:  Downloads the test dataset on the current directory "
          f"or in the specified in <path>.")
    print(f"")
    print(f"  -h, -help:      Show this help message.")
    print(f"")
    print(epilog)

    sys.exit(error_code)


if __name__ == "__main__":

    DEMO_FLAG = False
    DOWNLOAD_FLAG = False

    for arg in sys.argv[1:]:
        if arg in ["-h", "-help"]:
            print_help(0)
        elif arg == "demo":
            DEMO_FLAG = True
        elif arg.startswith("download_data"):
            DOWNLOAD_FLAG = True
            download_path = arg.split("=")[1] if '=' in arg else '.'
        else:
            print_help(1, "Unknown option")


    module_dir = os.path.dirname(__file__)
    test_data = os.path.join(os.path.dirname(module_dir), 'test_dataset')

    data_dir = test_data if DEMO_FLAG else ""

    if DOWNLOAD_FLAG:
        from distutils.dir_util import copy_tree
        if os.path.isdir(download_path):  # If exists, make a subdirectory
            download_path = os.path.join(download_path, 'phase_retriever_dataset')
        copy_tree(test_data, download_path)
        if DEMO_FLAG:
            data_dir = download_path
        else:
            print(f"Data can be found in {os.path.abspath(download_path)}")
            sys.exit(0)

    wxMain(data_dir)
