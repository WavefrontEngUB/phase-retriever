import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
from matplotlib.backends.backend_tkagg import (
        FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, Circle
from matplotlib.backend_bases import button_press_handler, key_press_handler

class MPLPlot(ttk.Frame):
    """Customized class to contain a matplotlib plot."""
    def __init__(self, master, bg, subplots=111, figsize=(6, 4), pick_type="rectangle", bind=None):
        ttk.Frame.__init__(self, master)
        self.bind=bind
        self.implot = None
        # MPL figure and axis
        self.fig = Figure(figsize=figsize)
        self.fig.patch.set_facecolor(bg)
        self.axes = []
        self.axes.append(self.fig.add_subplot(subplots, picker=True))
        # MPL canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        # Tkinter object
        self.tk_widget = self.canvas.get_tk_widget()
        self.tk_widget.pack(fill=tk.BOTH, expand=True)
        # Toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack()
        # Default values
        self.n = 1
        self.nx = 1
        self.ny = 1
        self.rect = None
        self.r = 1
        self.position = None
        self.pick_type = pick_type
        self.line_plot = []

        # Event connector
        self.canvas.mpl_connect("button_press_event", self.on_button_press)
        self.canvas.mpl_connect("key_press_event", self.on_key_press)
        if pick_type:
            self.canvas.mpl_connect("pick_event", self.onpick)

        # Dict to contain the possible patches inside the plots
        self.patches = {}

    def draw_circle(self, position, r):
        """Draw a circle in the prescribed coordinates"""
        # Create a cirlce object if not present already
        if "circle" not in self.patches:
            self.patches["circle"] = Circle((position), radius=r, fill=True,
                    color="green", alpha=.2)
            self.axes[0].add_patch(self.patches["circle"])
            self.canvas.draw()
            self.canvas.flush_events()
        else:
            self.patches["circle"].set_radius(self.r)
            self.patches["circle"].x = position[0]
            self.patches["circle"].y = position[1]
            self.fig.canvas.draw()
            self.fig.canvas.flush_events()
        self.r = r
        self.position = position

    def draw_rectangle(self, position, w, h):
        xc, yc = position
        # Coordinates of upper left corner
        y0 = yc-h//2
        y1 = yc+h//2
        x0 = xc-w//2
        x1 = xc+w//2
        # Fringe cases
        if y0 < 0:
            dy = abs(y0)
            y0 = 0
            y1 += dy-1
        if y1 >= self.ny:
            dy = y1-self.ny
            y1 = self.ny-1
            y0 = y0-dy
        if x0 < 0:
            dx = abs(x0)
            x0 = 0
            x1 += dx-1
        if x1 >= self.nx:
            dx = y1-self.nx
            x1 = self.nx-1
            x0 = x0-dx
        # Draw it
        if "rectangle" not in self.patches:
            self.patches["rectangle"] = Rectangle((x0, y0), w, h, color="green", alpha=.2)
            self.axes[0].add_patch(self.patches["rectangle"])
            self.canvas.draw()
            self.canvas.flush_events()
        else:
            self.patches["rectangle"].set_xy((x0, y0))
            self.patches["rectangle"].set_width(w)
            self.patches["rectangle"].set_height(h)
            self.canvas.draw()
            self.canvas.flush_events()

        self.rect = [x0, y0, x1, y1]
        self.position = position

    def on_button_press(self, event):
        button_press_handler(event, canvas=self.canvas, toolbar=self.toolbar)

    def on_key_press(self, event):
        key_press_handler(event, canvas=self.canvas, toolbar=self.toolbar)

    def onpick(self, event):
        xc = event.mouseevent.xdata
        yc = event.mouseevent.ydata

        # Case rectangle
        if self.pick_type == "rectangle":
            self.draw_rectangle((xc, yc), self.n*2, self.n*2)

        elif self.pick_type == "point":
            self.position = (xc, yc)
            self.draw_circle(self.position, self.n)

        # Case circle
        elif self.pick_type == "circle":
            dx = xc-self.nx//2
            dy = yc-self.ny//2

            r = np.sqrt(dx*dx+dy*dy)
            self.draw_circle((self.nx/2, self.ny/2), r)

        if self.bind:
            self.bind()

    def load_im(self, im, n, subplot, vmin=None, vmax=None, cmap="inferno"):
        self.im = im
        self.n = n
        self.ny, self.nx = self.im.shape
        self.implot = self.axes[subplot].imshow(im, cmap=cmap,
                                                vmin=vmin, vmax=vmax)
        self.canvas.draw()
        self.canvas.flush_events()

    def swap_array(self, im, n, subplot, vmin=None, vmax=None, cmap="gray"):
        if not self.implot:
            self.load_im(im, n, subplot, vmin=vmin, vmax=vmax, cmap=cmap)
        else:
            self.implot.set_data(im)
            self.canvas.draw()
            self.canvas.flush_events()

    def set_title(self, titles):
        for i, title in enumerate(titles):
            self.axes[i].set_title(title)

    def add_suplot(self, plot):
        self.axes.append(self.fig.add_subplot(plot, picker=True))

    def set_bind(self, seq, func):
        self.canvas.get_tk_widget().bind(seq, func)

    def plot(self, plot, data):
        xdata = range(len(data))
        if not self.line_plot:
            self.line_plot.append(self.axes[0].plot([], [], ".-")[0])
            self.line_plot.append(self.axes[1].plot([], [], ".-")[0])

        self.line_plot[plot].set_xdata(xdata)
        self.line_plot[plot].set_ydata(data)

        self.axes[0].relim()
        self.axes[0].autoscale_view()
        self.axes[1].relim()
        self.axes[1].autoscale_view()
        self.canvas.draw()
        self.canvas.flush_events()

    def bind_plot(self, fun):
        pass
