import os.path

import wx
from wx.lib.agw.floatspin import EVT_FLOATSPIN
from wx.propgrid import EVT_PG_CHANGED
import numpy as np
import json
import multiprocessing as mp

from .gui.wxplot import PlotsNotebook, LabelPlotsNotebook
from .gui.wxentries import wxEntryPanel
# from .gui.wxexplore import DataExplorer
from .retriever import PhaseRetriever
from .misc.focalprop import FocalPropagator

delta_t = 30  # ms

class GUIRetriever(PhaseRetriever):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.finished = False

    def monitor_process(self, *args):
        self.finished = False
        for p in self.processes:
            if p is None:
                continue
            p.start()
            #p.join(timeout=0)
        wx.CallLater(delta_t, self.check_status, *args)

    def check_status(self, plot):
        for i, p in enumerate(self.processes):
            full = True
            while full:
                try:
                    data = self.queues[i].get_nowait()
                    self.mse[i].append(data)
                except:
                    full = False
            status = any([p.is_alive() for p in self.processes if p is not None])
        self.update_function(plot)
        # Check the processes again if they are still alive
        if status:
            # FIXME: Recursion!!!!
            wx.CallLater(delta_t, self.check_status, plot)
        else:
            for p in self.processes:
                if p is None:
                    continue
                p.join(timeout=0)
            self.finished = True

    def update_function(self, plot):
        # TODO: Update manually so not to lock the whole interface...
        axes = plot.figure.axes
        for i, ax in enumerate(axes):
            line = ax.lines[0]
            line.set_data(range(len(self.mse[i])), self.mse[i])
            ax.relim()
            ax.autoscale_view()
        plot.canvas.draw()

class wxGUI(wx.Frame):
    def __init__(self, parent, title, search_dir=''):
        super().__init__(parent, title=title, size=(800, 600))

        # Initializing a dict containing the names of the plots that we will have on our
        # GUI with their pointers
        self.plots = {
                "irradiance": None,
                "mse"       : None,
                "phi"       : None,
                "bandwidth" : None,
                }

        self.init()
        self.Centre()

        self.propagator = FocalPropagator()

        if search_dir:
            self._load_data(search_dir)

    def init(self):
        # Initializing the plotter
        self.plotter = plotter = PlotsNotebook(self)

        # FIXME: Notebook
        notebook = wx.Notebook(self)

        # Separators for each of the panels we'll have
        sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.entries = entries = wxEntryPanel(notebook)
        self.entries.GetPgrid().Bind(EVT_PG_CHANGED, self.OnSpecChange)
        self.entries.GetButton("search").Bind(wx.EVT_BUTTON, self.OnLoadClick)
        self.entries.GetButton("autoadjust").Bind(wx.EVT_BUTTON, self.OnAutoadjust)
        self.entries.GetButton("begin").Bind(wx.EVT_BUTTON, self.OnRetrieve)

        # Explorer tab
        # self.explorer = explorer = DataExplorer(notebook)
        # explorer.GetSpin().Bind(EVT_FLOATSPIN, self.OnExplore)

        # FIXME: Notebook
        notebook.AddPage(entries, "Config")
        # notebook.AddPage(explorer, "Exploration")

        # Adding it, from left to right, to the sizer
        sizer.Add(notebook, 1, wx.LEFT | wx.EXPAND)
        sizer.Add(plotter, 2, wx.RIGHT | wx.EXPAND)
        self.SetSizer(sizer)

        # Creating a menu
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()

        fileSave = fileMenu.Append(wx.ID_SAVE, "Save config.\tCtrl+S", "Save configuration")
        fileLoad = fileMenu.Append(wx.ID_OPEN, "Load config.\tCtrl+O", "Load configuration")
        fileExport = fileMenu.Append(wx.ID_ANY, "Export results\tCtrl+E", "Export results")

        my_id = wx.NewId()
        saveAccel = wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('s'), my_id)
        fileSave.SetAccel(saveAccel)
        loadAccel = wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('o'), my_id)
        fileLoad.SetAccel(loadAccel)
        exportAccel = wx.AcceleratorEntry(wx.ACCEL_CTRL, ord('e'), my_id)
        fileExport.SetAccel(exportAccel)

        fileQuit = fileMenu.Append(wx.ID_EXIT, "Quit", "Quit application")
        menubar.Append(fileMenu, "&File")
        self.SetMenuBar(menubar)

        self.Bind(wx.EVT_MENU, self.OnLoad, fileLoad)
        self.Bind(wx.EVT_MENU, self.OnDump, fileSave)
        self.Bind(wx.EVT_MENU, self.OnExport, fileExport)
        self.Bind(wx.EVT_MENU, self.OnQuit, fileQuit)

        # TODO: Initialize the phase retriever
        self.retriever = GUIRetriever()


    # --- MAIN-PANEL OnEvent methods ---
    def OnSpecChange(self, event):
        """Change properties of the retriever as they are modified in the pgrid entry
        panel."""
        values = self.entries.GetValues()
        # FIXME: Change wxentries so that its keys are the same as those of the retriever
        for key in values:
            if key == "lamb":
                self.retriever["lamb"] = values[key]

            elif key == "n_iter":
                self.retriever["n_max"] = values[key]

            elif key == "bandwidth":
                self.retriever[key] = bw = values[key]
                width = values["window_size"]
                self.plotter.set_circle("Spectrum", (width // 2, width // 2), 2 * bw,
                                        color="red")
            elif key == "window_size":
                width = values[key]
                if width != self.retriever["dim"]:
                    self.retriever["dim"] = width
                    rect_center = values["window_center"]
                    top = [int(i) - width // 2 for i in rect_center]
                    bottom = [int(i) + width // 2 for i in rect_center]
                    self.plotter.set_rectangle("Irradiance", top, width, width)

            elif key == "window_center":
                rect_center = values[key]
                top = [int(i) - width // 2 for i in rect_center]
                bottom = [int(i) + width // 2 for i in rect_center]
                self.retriever["rect"] = [top, bottom]
                # The retriever will tell us if the rect coordinates are the correct ones
                top, bottom = self.retriever["rect"]
                width = self.retriever["dim"]
                center = [str(int(i) + width // 2) for i in top]
                # Set the correct values in the entry widget
                self.entries.SetValue(window_center=center)
                # Finally, set the rectangle visible on screen
                self.plotter.set_rectangle("Irradiance", top, width, width)
                self._plot_irradiance()
                self._plot_stokes()

    def OnLoadClick(self, event):
        dialog = wx.DirDialog(self,
                              "Choose input directory  (files might not be shown)",
                              os.getcwd(), wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        # Run the window and check if it successfully finishes
        res = dialog.ShowModal()
        if res == wx.ID_OK:
            # Retain a reference of the user selected path
            dirname = dialog.GetPath()
        elif res == wx.ID_CANCEL:
            dialog.Destroy()
            return
        dialog.Destroy()
        self._load_data(dirname)

    def OnAutoadjust(self, event):
        # TODO
        # We center the window with the size given by the entries.
        configs = self.entries.GetValues()
        window_size = configs["window_size"]
        self.retriever.config(dim=window_size)
        top, bottom = self.retriever.center_window()
        rect_center = top[0]+window_size//2, top[1]+window_size//2
        # Adjust the phase origin
        self.retriever.select_phase_origin()
        phase_origin = self.retriever.options["origin"]
        self.retriever.compute_bandwidth()
        bw = self.retriever.options["bandwidth"]

        # Set the autoadjusted values to the entry panel
        self.entries.SetValue(bandwidth=bw, 
                window_center=[str(x) for x in rect_center],
                phase_origin=[str(x) for x in phase_origin])

        # Replot everything
        self._reconfig()
        self.plotter.set_colorbar("Cropped Stokes", share=(0,1,2,3))
        self.plotter.select_page("Spectrum")

    # def OnStartProcessing(self, event):
    #     # Check if pixel_size is properly set, needed to do any assignment
    #     p_size = self.retriever.options["pixel_size"]
    #     if ((not p_size) or (p_size <= 0)):
    #         error_dialog = wx.MessageDialog(self,
    #                         "Pixel size must be selected before proceeding!",
    #                         style=wx.ICON_ERROR | wx.OK)
    #         error_dialog.ShowModal()

    def OnRetrieve(self, event):
        # Prepare the plotting page if it didn't exist
        try:
            plot = self.plotter.get_page("MSE")
            axes = plot.figure.axes
        except:
            plot = self.plotter.add("MSE")
            # Set titles
            fig = plot.figure
            ax1 = fig.add_subplot(1, 2, 1)
            ax2 = fig.add_subplot(1, 2, 2)
            axes = [ax1, ax2]
            axes[0].set_title("MSE X component (loading...)")
            axes[1].set_title("MSE Y component (loading...)")

        # First, we need to clear all possible lines
        for ax in axes:
            ax.clear()
            ax.plot([], [])
        # Then, we call the retriever to commence the process
        self.retriever.config(mode=self.entries.GetValue("mode"))
        self.retriever.config(pixel_size=self.entries.GetValue("pixel_size"))
        self.retriever.retrieve(args=(plot,), monitor=False)
        wx.CallLater(delta_t, self.retriever.monitor_process, plot)
        wx.CallLater(delta_t, self.OnCheckCompletion)
        self.plotter.select_page("MSE")

    def OnCheckCompletion(self, event=None):
        if self.retriever.finished:
            self.OnFinished()
        else:
            wx.CallLater(delta_t, self.OnCheckCompletion)

    def OnFinished(self):
        """Plot results once the phase retriever is finished"""
        Ex, Ey = self.retriever.get_trans_fields()
        Ez = np.zeros_like(Ex)
        self.update_results(Ex, Ey, Ez)

        self.plotter.set_colorbar("Results", share=(3, 5, 1))
        self.plotter.select_page("Results")

        # TODO: Prepare the propagator to explore the phase retrieval results...
        configs = self.entries.GetValues()
        pixel_size = configs["pixel_size"]/configs["lamb"]
        self.propagator["Ex"] = Ex
        self.propagator["Ey"] = Ey
        self.propagator["pixel_size"] = pixel_size
        self.propagator.create_spectra()
        self.propagator.create_gamma()
        self.update_results(*self.propagator.propagate_field_to(0))

    def OnExplore(self, event):
        """ Not used, but it is a method to explore the phase retrieval results
            over the z coordinate.
        """
        if not self.retriever.finished :
            dialog =  wx.MessageDialog(self, "Phase retrieval not yet finished!",
                                       style=wx.ICON_ERROR | wx.OK)
            dialog.ShowModal()
            dialog.Destroy()
            return
        # Get the selected z propagation value (wavelength units)
        z = self.explorer.GetZ()
        self.update_results(*self.propagator.propagate_field_to(z))

    # --- FILE-MENU OnEvent methods ---
    def OnDump(self, event):
        """Dump current configuration on a json file, to be loaded later."""
        configs = self.entries.GetValues()
        # Open a dialog to ask where to save it
        with wx.FileDialog(self, "Save configuration", wildcard="*.json",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
            try:
                with open(path, "w") as f:
                    json.dump(configs, f, indent=4, sort_keys=True)
            except IOError:
                wx.LogError(f"Can't save data in file {path}")

    def OnLoad(self, event):
        """Load a configuration file."""
        with wx.FileDialog(self, "Load configuration", wildcard="*.json",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as dialog:
            if dialog.ShowModal() == wx.ID_CANCEL:
                return
            path = dialog.GetPath()
            try:
                with open(path, "r") as f:
                    configs = json.load(f)
            except IOError:
                wx.LogError(f"Can't load configuration from file {path}")
        self.entries.SetValue(**configs)
        self._load_data(configs["path"])
        self._reconfig()

    def OnExport(self, event):
        try:

            Ex, Ey, Ez = self.propagator.propagate_field_to(0)
            data = {"Ex":Ex, "Ey":Ey, "Ez": Ez}
            basename = self.beam_name + "_retrieved.npz"

            with wx.FileDialog(self, "Save recovered data",
                               os.getcwd(), basename,
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                               wildcard="*.npz") as save_dialog:
                if save_dialog.ShowModal() == wx.ID_CANCEL:
                    return
                path = save_dialog.GetPath()
                if not path.endswith(".npz"):
                    path += ".npz"
                np.savez(path, **data)
        except:
            dialog = wx.MessageDialog(self, "Could not export any recovered data",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR)
            dialog.ShowModal()

    def OnQuit(self, event):
        self.Close()

    # --- Utils ---
    def _reconfig(self):
        # First, we need to get all the configurations from the entries
        values = self.entries.GetValues()
        bw = values["bandwidth"]*2
        rect_center = values["window_center"]
        width = values["window_size"]
        top = [int(i)-width//2 for i in rect_center]
        bottom = [int(i)+width//2 for i in rect_center]
        # Change configurations on the retriever
        self.retriever.config(path=values["path"], lamb=values["lamb"],
                rect=(top, bottom), bandwidth=bw/2, dim=width, pixel_size=values["pixel_size"], n_max=values["n_iter"])
        self.retriever._compute_spectrum()

        # Plot the relevant information...
        self._plot_irradiance()
        self._plot_stokes()
        self._plot_bandwidth()

        # Draw the rectangle and circle specifiying the region of interest and the
        # bandwidth.
        self.plotter.set_rectangle("Irradiance", top, width, width)
        # Draw the bandwidth
        self.plotter.set_circle("Spectrum", (width//2, width//2), bw, color="red")

    def _load_data(self, dirname):
        # We now update the entry to contain the selected path
        self.entries.SetValue(path=dirname)

        # Finally, we load all images into the phase retriever
        try:
            self.beam_name = self.retriever.load_dataset(dirname, ftype=self.entries.GetValue("ext"))
        except:
            error_dialog = wx.MessageDialog(self, f"Selected directory does not "
                                                  f"contain polarimetric images.  "
                                                  f"{self.entries.GetValue('ext')}",
                                            style=wx.ICON_ERROR | wx.OK)
            error_dialog.ShowModal()

        # We show the important images through the plots
        self._show_dataset()

    def _show_dataset(self):
        # Irradiance plots with the rectangle indicating where exactly the window is
        # located.
        self.plotter.set_imshow("Irradiance", self.retriever.irradiance, cmap="gray")

    def _plot_irradiance(self):
        self.plotter.set_imshow("Cropped irradiance", self.retriever.cropped_irradiance, cmap="gray")

    def _plot_stokes(self):
        s0M = None
        for idx, stokes_image in enumerate(self.retriever.get_stokes()):
            s0M = s0M or stokes_image.max()
            self.plotter.set_imshow("Cropped Stokes", stokes_image/s0M,
                                    title=f"$S_{idx}$",
                                    cmap="seismic", shape=(2,2),num=idx+1,
                                    vmin=-1, vmax=1)

    def _plot_bandwidth(self):
        a_ft_log = np.log10(self.retriever.a_ft)
        self.plotter.set_imshow("Spectrum", a_ft_log, cmap="viridis")

    def update_results(self, Ex, Ey, Ez):

        self.plotter.set_imshow("Results", abs(Ex), title="$|E_x|$",
                                shape=(3, 2), num=1, cmap="gray")
        self.plotter.set_imshow("Results", np.angle(Ex), title="$\phi_x$",
                                shape=(3, 2), num=2, cmap="hsv",
                                vmin=-np.pi, vmax=np.pi)
        self.plotter.set_imshow("Results", abs(Ey), title="$|E_y|$",
                                shape=(3, 2), num=3, cmap="gray")
        self.plotter.set_imshow("Results", np.angle(Ey), title="$\phi_y$",
                                shape=(3, 2), num=4, cmap="hsv",
                                vmin=-np.pi, vmax=np.pi)
        self.plotter.set_imshow("Results", abs(Ez), title="$|E_z|$",
                                shape=(3, 2), num=5, cmap="gray")
        self.plotter.set_imshow("Results", np.angle(Ez), title="$\phi_z$",
                                shape=(3, 2), num=6, cmap="hsv",
                                vmin=-np.pi, vmax=np.pi)


if __name__ == "__main__":
    app = wx.App()
    gui = wxGUI(None, "Phase retriever")
    gui.Show()

    app.MainLoop()
