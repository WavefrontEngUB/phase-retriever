import tkinter as tk
import tkinter.ttk as ttk
from .mplplot import MPLPlot

class PlotsNotebook(ttk.Notebook):
    def __init__(self, master, bg, bind=None):
        self.master = master
        ttk.Notebook.__init__(self, master)
        self.plots = {}

        # Beam center selector
        self.plots["beam center"] = MPLPlot(self, bg, subplots=111, bind=bind)
        self.plots["beam center"].set_title(("Select region of interest", ))
        self.add(self.plots["beam center"], text="Beam center")

        # Autocorrelation selector
        self.plots["Autocorrelation"] = MPLPlot(self, bg, subplots=111, pick_type="circle", bind=bind)
        self.plots["Autocorrelation"].set_title(("Select autocorrelation radius", ))
        self.add(self.plots["Autocorrelation"], text="Autocorrelation")

        # Phase origin selector
        self.plots["phase"] = MPLPlot(self, bg, subplots=111, pick_type="point", bind=bind)
        self.plots["phase"].set_title(("Select phase origin", ))
        self.plots["phase"].n = 20 
        self.add(self.plots["phase"], text="Phase origin")

        # Mean Squared Error visualizer
        self.plots["MSE"] = MPLPlot(self, bg, subplots=121, pick_type=None, bind=bind)
        self.plots["MSE"].add_suplot(122)
        self.plots["MSE"].set_title(("X component", "Y Component"))
        self.add(self.plots["MSE"], text="MSE")

        # Focal explorer
        self.plots["explorer"] = MPLPlot(self, bg, subplots=111, pick_type=None)
        self.plots["explorer"].set_title(("Total irradiance",))
        self.add(self.plots["explorer"], text="Focal explorer")

    def get_data(self):
        rect = self.plots["beam center"].rect
        radius = self.plots["Autocorrelation"].r

        return_dict = {"rectangle":rect, "radius":radius}

        return return_dict

    def plot_image(self, image, n, subplot, plot):
        self.plots[plot].load_im(image, n, subplot)

    def bind_plot(self, plot, fun):
        self.plots[plot].bind_plot(self, fun)

    def swap_array(self, im, n, subplot, plot, vmin=None, vmax=None, cmap="gray"):
        self.plots[plot].swap_array(im, n, subplot, vmin=vmin, vmax=vmax,
                cmap=cmap)

