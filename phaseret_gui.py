from phase_retriever import PhaseRetrieverGUI, wxGUI
import platform
import wx
import tkinter as tk
import tkinter.ttk as ttk

def wxMain():
    app = wx.App()
    gui = wxGUI(None, "Phase retriever")
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
if __name__ == "__main__":
    wxMain()
