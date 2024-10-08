import sys
import os

import platform
import wx
import tkinter as tk
import tkinter.ttk as ttk

from .interface import PhaseRetrieverGUI
from .wx_gui import wxGUI
from .test import test_basics

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

    print(f"Description: {PROGRAM_NAME} is a GUI powered software to retrieve the phase of\n"
          f"a highly focused electromagnetic field. The program requires the six polarimetric\n"
          f"images recorded at two planes perpendical to the optical axis and separated some\n"
          f"distance nearby the focus. It also calculates the electric field longitudinal component.")
    print(f"")
    print(f"usage: {program_cmd} [path=<path>|get_test_data=<path>|demo|test] [-h|--help]")
    print(f"")
    print(f"Options:")
    print(f"  path:           Opens the program with the dataset in the specified path.")
    print(f"  get_test_data:  Copies the test dataset on the current directory \n"
          f"                  or in the specified optional <path>.")
    print(f"  demo=N:         Launches the program with a test dataset already loaded.\n"
          f"                  N: 1 or 'empty' -> Simulated data ; 2 -> Experimental data.\n"
          f"                  *It can be combined with get_test_data.*")
    print(f"  test:           Runs the unit test suite.")
    print(f"")
    print(f"  -h, --help:     Shows this help message.")
    print(f"")
    print(epilog)

    sys.exit(error_code)


if __name__ == "__main__":

    DEMO_FLAG = False
    DOWNLOAD_FLAG = False

    module_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(module_dir, 'test_dataset')

    data_dir = os.getcwd()

    verbose = False
    for arg in sys.argv[1:]:
        if arg in ["-h", "--help"]:
            print_help(0)
        elif arg == "-v":
            verbose = True
        elif arg == "test":
            err = test_basics()
            sys.exit(err)
        elif arg.startswith("demo"):
            DEMO_FLAG = True
            demo_num = arg.split("=")[1] if '=' in arg else 1
            try:
                demo_num = int(demo_num)
            except:
                print_help(-1, "Demo number must be an integer.")
            data_dir = os.path.join(test_data_dir, "experimental" if demo_num == 2
                                                   else "simulated")
        elif arg.startswith("get_test_data"):
            DOWNLOAD_FLAG = True
            download_path = arg.split("=")[1] if '=' in arg else '.'
        elif arg.startswith("path"):
            data_dir = arg.split("=")[1] if '=' in arg else ''
        else:
            print_help(1, "Unknown option")

    if DOWNLOAD_FLAG:
        import shutil
        from datetime import datetime

        if os.path.isdir(download_path):  # If exists, make a subdirectory
            download_path += datetime.now().strftime('_%y%m%d_%H%M')
        count = 1
        if os.path.isdir(download_path):
            while True:
                candidate = f"{download_path}_{count}"
                if not os.path.isdir(candidate):
                    download_path = candidate
                    break
                count += 1

        shutil.copytree(test_data_dir, download_path)
        if DEMO_FLAG:
            data_dir = download_path
        else:
            print(f"Data can be found in {os.path.abspath(download_path)}")
            sys.exit(0)

    wxMain(data_dir)
