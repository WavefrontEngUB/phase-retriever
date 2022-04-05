import tkinter as tk
import tkinter.ttk as ttk
from .myentry import myEntry

class BeamConfig(ttk.Frame):
    """Container with the characteristics of the beam."""
    def __init__(self, master, borderwidth=0, relief="flat"):
        self.master = master
        ttk.Frame.__init__(self, master, borderwidth=borderwidth, relief=relief)

        self.entries = {}
        self.buttons = {}
        # Current path
        self.entries["current path"] = myEntry(self, text="Dataset path", state="Disabled")

        # Beam center
        self.entries["beam center"] = myEntry(self, text="Beam center")

        # Autocorrelation radius
        self.entries["radius"] = myEntry(self, text="Autocorr. radius")

        # Location of phase origin
        self.entries["phase origin"] = myEntry(self, text="Loc. of phase origin")

        # Wavelength
        self.entries["wavelength"] = myEntry(self, text="Wavelength (mm)",
                def_entry="520e-6")

        # Pixel pitch
        self.entries["pitch"] = myEntry(self, text="Pixel pitch (mm)",
                def_entry="3.75e-3")

        # Magnification
        self.entries["magnification"] = myEntry(self, text="Magnification",
                def_entry="1")

        # Rectangle size
        self.entries["rectangle"] = myEntry(self, text="Region of interest size", 
                def_entry="256")

        # Number of iterations
        self.entries["niter"] = myEntry(self, text="Number of iterations", 
                def_entry="30")

        # Begin button
        self.buttons["begin"] = ttk.Button(self, text="Begin")

        # Pack everything up
        for entry in self.entries:
            self.entries[entry].pack(side=tk.TOP, anchor=tk.W)

        for entry in self.buttons:
            self.buttons[entry].pack(side=tk.TOP, anchor=tk.W)

    def update_element(self, element, new_entry):
        self.entries[element].change_text(new_entry)

    def get(self):
        return_dict = {}
        for key in self.entries:
            return_dict[key] = self.entries[key].get()
        return return_dict

    def set_callback(self, key, callback):
        button = self.buttons[key]
        button["command"] = callback
