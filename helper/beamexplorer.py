import tkinter as tk
import tkinter.ttk as ttk
from .myentry import myEntry

class ExplorerProps(ttk.LabelFrame):
    def __init__(self, parent, borderwidth, relief="flat", text=None):
        ttk.LabelFrame.__init__(self, parent, borderwidth=borderwidth, relief=relief,
                text=text)

        self.entries = {}
        self.other_widgets = {}
        self.min_z = tk.StringVar()
        self.min_z.set("0")
        self.max_z = tk.StringVar()
        self.max_z.set("2")

        # Minimum distance
        self.entries["min_z"] = myEntry(self, text="z min (wavelength)",
                def_entry="", textvariable=self.min_z)
        self.entries["min_z"].set_callback(self.set_limits)

        # Maximum distance
        self.entries["max_z"] = myEntry(self, text="z max (wavelength)",
                def_entry="", textvariable=self.max_z)
        self.entries["max_z"].set_callback(self.set_limits)

    def pack_widgets(self):
        for entry in self.entries:
            self.entries[entry].pack(side=tk.TOP, anchor=tk.W)

        for entry in self.other_widgets:
            self.other_widgets[entry].pack(side=tk.TOP, anchor=tk.W, fill="y")

    def set_limits(self, *args):
        try:
            from_ = str(self.entries["min_z"].get())
            to = str(self.entries["max_z"].get())
            print(from_, to)
            self.other_widgets["slider"].config(from_=from_)
            self.other_widgets["slider"].config(to=to)
        except:
            print("Could not config!")

    def set_callback(self):
        pass

    def set_state(self, state):
        """Activa o desactiva tots els widgets depenents d'aquest requadre!"""
        for child in self.winfo_children():
            try:
                child.configure(state=state)
            except:
                pass

    def _set_z_label(self, *args):
        value = self.other_widgets["slider"].get()
        self.zval.set(value)
        # Si hi ha un callback extra, crida'l
        if self.binded_fun:
            self.binded_fun(float(value))

    def bind_update(self, function):
        self.binded_fun = function

class BeamPropWin(ExplorerProps):
    def __init__(self, parent, borderwidth=0, relief="flat", text=None):
        ExplorerProps.__init__(self, parent, borderwidth=borderwidth, relief=relief,
                text=text)

        self.n_ims = tk.StringVar()
        self.n_ims.set("100")
        self.entries["n_ims"] = myEntry(self, text="Number of images",
                def_entry="", textvariable=self.n_ims)

        self.v_var = tk.IntVar()
        self.v_var.set(0)
        self.entries["video"] = ttk.Checkbutton(self, text="Make video", variable=self.v_var)
        self.entries["fps"] = myEntry(self, text="FPS", def_entry="8")

    def get_values(self):
        n_ims = int(self.n_ims.get())
        min_z = float(self.min_z.get())
        max_z = float(self.max_z.get())
        delta_z = max_z-min_z
        video = self.v_var.get()
        fps = self.entries["fps"].get()
        return {"n_ims":n_ims, "delta_z":delta_z, "video":video, "fps":fps}

class BeamExplorer(ExplorerProps):
    
    def __init__(self, parent, borderwidth=0, relief="flat"):
        ExplorerProps.__init__(self, parent, borderwidth=borderwidth, relief=relief)
        
        # Slider to select the z plane
        self.other_widgets["slider_text"] = ttk.Label(self, text="z location")
        self.other_widgets["slider"] = ttk.Scale(self, from_="0", to="2",
                orient=tk.HORIZONTAL, command=self._set_z_label)

        # Etiqueta del slider
        self.zval = tk.StringVar()
        self.zval.set("0")
        self.other_widgets["slider_pos"] = ttk.Label(self, textvariable=self.zval)

        # Empaqueta els widgets
        self.pack_widgets()

        # Callbacks per a les variables de texte...
        self.min_z.trace_add("write", self.set_limits)
        self.max_z.trace_add("write", self.set_limits)
