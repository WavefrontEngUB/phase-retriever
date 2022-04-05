import tkinter as tk
import tkinter.ttk as ttk
from .beamexplorer import BeamExplorer
from .beamconfig import BeamConfig

class BeamNotebook(ttk.Notebook):
    def __init__(self, parent, borderwidth=None, relief=None):
        ttk.Notebook.__init__(self, parent)

        self.pages = {}

        self.pages["config"] = BeamConfig(self, borderwidth=borderwidth, relief=relief)
        self.pages["explorer"] = BeamExplorer(self, borderwidth=borderwidth, relief=relief)

        self.add(self.pages["config"], text="Configuration")
        self.add(self.pages["explorer"], text="Exploration")

    def update_element(self, page, element, new_entry):
        self.pages[page].update_element(element, new_entry)

    def get(self, page):
        return_dict = self.pages[page].get()
        return return_dict

    def set_callback(self, page, key, callback):
        self.pages[page].set_callback(key, callback)

    def set_state(self, page, state):
        self.pages[page].set_state(state)

    def bind_update(self, page, function):
        self.pages[page].bind_update(function)

    def bind_update(self, page, function):
        self.pages[page].bind_update(function)
