import wx
import wx.lib.agw.aui as aui
import wx.lib.mixins.inspection as wit

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle
from matplotlib.backends.backend_wxagg import (
        FigureCanvasWxAgg as FigureCanvas,
        NavigationToolbar2WxAgg as NavigationToolbar)

# TODO: Reproduce the same functionality as in its Tk counterpart.
class Plot(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY, dpi=None, **kwargs):
        super().__init__(parent, id=id, **kwargs)
        self.figure = Figure(dpi=dpi, figsize=(2, 2), constrained_layout=True)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        sizer.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        self.SetSizer(sizer)

        # Dict to contain and access all the drawn patches in the current figure.
        self.patches = {}

    def draw_circle(self, position, r, color="green"):
        """Draw a circle with centre at the given coordinates with radius r."""
        ax = self.figure.axes[0]
        if "circle" not in self.patches:
            circle = self.patches["circle"] = Circle((position), radius=r, fill=True, color=color,
                    alpha=.2)
            ax.add_patch(circle)
        else:
            circle = self.patches["circle"]
            circle.set_radius(r)
            circle.set_center(position)
        self.canvas.draw()
        self.canvas.flush_events()

    def set_rectangle(self, position, w, h, color="green"):
        """Draw a rectangle at a given position with width w and height h."""
        if not "rectangle" in self.patches:
            rect = self.patches["rectangle"] = Rectangle((0, 0), 1, 1, color=color, fill=True,
                    alpha=0.2)
            self.figure.axes[0].add_patch(rect)
        else:
            rect = self.patches["rectangle"]
        # We transform the coordinates of the rectangle, as position is assumed to be its center,
        # while matplotlib requires its position from the lower left corner.
        x_llc, y_llc = position[1], position[0]
        # Set its new coordinates, width and height
        rect.set(width=w, height=h, x=x_llc, y=y_llc)
        self.canvas.draw()
        self.canvas.flush_events()

    def set_data(self, ax_num, data):
        ax = self.figure.axes[ax_num]
        line = ax.lines[0]
        # Set new data
        line.set_data(*data)
        ax.relim()
        self.canvas.draw()
        self.canvas.flush_events()

class PlotsNotebook(wx.Panel):
    def __init__(self, parent, id=wx.ID_ANY):
        super().__init__(parent, id=id)
        self.nb = aui.AuiNotebook(self, agwStyle=aui.AUI_NB_TOP | aui.AUI_NB_TAB_SPLIT | aui.AUI_NB_TAB_MOVE | aui.AUI_NB_SCROLL_BUTTONS)
        sizer = wx.BoxSizer()
        sizer.Add(self.nb, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.pages = {}
        self.colorbar = None
        
    def add(self, name):
        if name in self.pages:
            raise NameError(f"Page with name {name} already exists!")
        page = Plot(self.nb)
        self.nb.AddPage(page, name)
        self.pages[name] = len(self.pages)
        return page

    def get_page(self, name):
        return self.nb.GetPage(self.pages[name])

    def set_imshow(self, name, image, cmap="viridis", shape=(1, 1), num=1, vmin=0, vmax=1):
        if name not in self.pages:
            fig = self.add(name).figure
            ax = fig.add_subplot(*shape, num)
            ax.imshow(np.zeros((16, 16)), cmap=cmap, vmin=vmin, vmax=vmax)
        idx = self.pages[name]
        plot = self.nb.GetPage(idx)
        canvas = plot.canvas
        figure = plot.figure
        if num > len(figure.axes):
            ax = figure.add_subplot(*shape, num)
            ax.imshow(np.zeros((16, 16)), cmap=cmap, vmin=vmin, vmax=vmax)
        ax = figure.axes[num-1]

        ny, nx = image.shape

        ax_img = ax.get_images()[0]
        ax_img.set_extent([0, nx, ny, 0])
        ax_img.set_data(image)
        ax_img.set_clim(image.min(), image.max())
        canvas.flush_events()
        canvas.draw()

    def set_rectangle(self, name, position, w, h, color="green"):
        if name not in self.pages:
            raise NameError(f"Notebook page with name {name} does not exist")
        idx = self.pages[name]
        plot = self.nb.GetPage(idx)
        plot.set_rectangle(position, w, h, color=color)

    def set_circle(self, name, position, r, color="green"):
        if name not in self.pages:
            raise NameError(f"Notebook page with name {name} does not exist")
        idx = self.pages[name]
        plot = self.nb.GetPage(idx)
        plot.draw_circle(position, r, color=color)

    def set_colorbar(self, name, share=(0, 2)):
        idx = self.pages[name]
        plot = self.nb.GetPage(idx)
        figure = plot.figure
        axes = figure.axes

        im = axes[share[0]].get_images()[0]

        ax_shared = []
        for i in share:
            ax_shared.append(axes[i])

        if not self.colorbar:
            self.colorbar = figure.colorbar(im, ax=ax_shared)

        plot.canvas.draw()


class LabelPlotsNotebook(PlotsNotebook, wx.Panel):
    def __init__(self, parent, text):
        #super(wx.Panel, self).__init__(parent)
        #super(PlotsNotebook, self).__init__(self)
        wx.Panel.__init__(self, parent)
        PlotsNotebook.__init__(self, self)

        self.init(text)

    def init(self, text):
        tctrl = wx.StaticText(self, label=text)
        sizer = wx.BoxSizer(wx.VERTICAL)

        sizer.Add(tctrl, 1, wx.EXPAND | wx.LEFT)
        self.SetSizer(sizer)
