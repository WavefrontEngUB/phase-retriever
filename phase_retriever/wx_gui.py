import os.path
import sys
from glob import glob

import wx
from wx.lib.agw.floatspin import EVT_FLOATSPIN
from wx.propgrid import EVT_PG_CHANGED
import numpy as np
import json
import multiprocessing as mp

from phase_retriever.constants import MSE_THRESHOLD
from .gui.error_dialog import MyExceptionHook
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
        ylim = max([max(self.mse[i]) if self.mse[i] else 1 for i in range(2)])
        for i, ax in enumerate(axes):
            line = ax.lines[0]
            line.set_data(range(len(self.mse[i])), self.mse[i])
            ax.relim()
            ax.set_xlim(0, self.options.get("n_iter", 100))
            ax.set_ylim(MSE_THRESHOLD, ylim)
            ax.autoscale_view()
            ax.set_title(f"MSE for {['X', 'Y'][i]} component")
        plot.canvas.draw()

class wxGUI(wx.Frame):
    def __init__(self, parent, title, search_dir=''):
        super().__init__(parent, title=title, size=(1024, 768))

        self.init()
        self.Centre()

        sys.excepthook = MyExceptionHook

        self.init_data()

        self.propagator = FocalPropagator()

        self.dirname = search_dir
        if search_dir:
            self._load_data(silent=True)

        # self.Maximize(True) if sys.platform == "Linux" else None

    def init_data(self, hard=True):
        self.hasStokes = False if hard else self.hasStokes
        self.hasSpectrum = False if hard else self.hasSpectrum
        self.finished = False
        self.beam_name = None if hard else self.beam_name
        self.retriever = GUIRetriever()

        # Disable some buttons
        self.entries.GetButton("center").Disable()
        self.entries.GetButton("swap").Disable()
        self.entries.GetButton("autoadjust").Disable()
        self.entries.GetButton("begin").Disable()
        self.entries.GetButton("export").Disable()

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
        self.entries.GetButton("center").Bind(wx.EVT_BUTTON, self.OnCenter)
        self.entries.GetButton("swap").Bind(wx.EVT_BUTTON, self.OnSwap)
        self.entries.GetButton("autoadjust").Bind(wx.EVT_BUTTON, self.OnAutoadjust)
        self.entries.GetButton("begin").Bind(wx.EVT_BUTTON, self.OnRetrieve)
        self.entries.GetButton("export").Bind(wx.EVT_BUTTON, self.OnExport)

        # FIXME: Notebook
        notebook.AddPage(entries, "Configuration")
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

        self.updated_old_entries()

    # --- MAIN-PANEL OnEvent methods ---
    def OnSpecChange(self, event):
        """Change properties of the retriever as they are modified in the pgrid entry
        panel."""

        key = event.GetPropertyName()
        new_value = event.GetValue()
        values = self.entries.GetValues()

        basic_keys = ("lamb", "n_iter")  # Those that must be updated in the retriever and done.
        post_keys = ("roi", "z_exp")  # Those that can be modified also when retrieve is finished.

        if (self.finished and key not in post_keys + ("path", )  # Path is checked separatelly
                and not self._ensures_reload(hard=False)):
            self.entries.SetValue(**{key: self.old_entries[key]})
            return

        if key in basic_keys:
            self.retriever[key] = new_value

        elif key == "path":
            if self.dirname != new_value and self._ensures_reload(hard=True):
                self.dirname = new_value
                self._load_data()
            else:
                self.entries.SetValue(path=self.dirname)

        elif key == "bandwidth":
            if new_value > 0:
                self.retriever[key] = bw = new_value
                self.retriever._compute_spectrum()
                self.hasSpectrum = True
                width = values["window_size"]
                self._plot_bandwidth()
                self.plotter.set_circle("Spectrum", (width//2, width//2), 2*bw,
                                        color="red")
                # self.entries.GetButton("search").Disable()
                self.entries.GetButton("begin").Enable()

        elif key == "window_size":
            width = new_value
            if width != self.retriever["dim"]:
                self.retriever["dim"] = width
                rect_center = values["window_center"]
                top = [int(i) - width // 2 for i in rect_center]
                self.plotter.set_rectangle("Irradiance (full size)", top, width, width)

        elif key == "window_center":
            rect_center = new_value
            if rect_center != self.retriever["rect"]:
                width = values["window_size"]
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
                self.plotter.set_rectangle("Irradiance (full size)", top, width, width)
                self._plot_stokes()

        elif key == "window_sizeR":
            widthR = new_value
            if self.retriever["rectR"] is None:
                return
            dimRR = self.retriever["rectR"][1][0] - self.retriever["rectR"][0][0]
            if widthR != dimRR:
                rect_centerR = values["window_centerR"]
                topR = [int(i) - widthR // 2 for i in rect_centerR]
                bottomR = [int(i) + widthR // 2 for i in rect_centerR]
                self.retriever["rectR"] = [topR, bottomR]
                self.plotter.set_rectangle("Irradiance (full size)", topR, widthR, widthR,
                                           color="red")
                self._reconfig()

            if widthR == 0:
                self.entries.GetButton("swap").Disable()
            else:
                self.entries.GetButton("swap").Enable()

        elif key == "window_centerR":
            rect_centerR = new_value
            widthR = values["window_sizeR"]
            if rect_centerR != self.retriever["rectR"]:

                topR = [int(i) - widthR // 2 for i in rect_centerR]
                bottomR = [int(i) + widthR // 2 for i in rect_centerR]
                self.retriever["rectR"] = [topR, bottomR]
                # The retriever will tell us if the rect coordinates are the correct ones
                topR, bottomR = self.retriever["rectR"]
                widthR = self.retriever["rectR"][1][0] - self.retriever["rectR"][0][0]
                centerR = [str(int(i) + widthR // 2) for i in topR]
                # Set the correct values in the entry widget
                self.entries.SetValue(window_centerR=centerR)
                # Finally, set the rectangle visible on screen
                self.plotter.set_rectangle("Irradiance (full size)", topR, widthR, widthR,
                                           color="red")
                self._plot_stokes()

        elif key == 'roi' or key == 'z_exp':
            self.roi = values['roi']
            # self._plot_irradiance()
            self._plot_stokes()
            self.update_results()  # values['z_exp']

        self.updated_old_entries()

    def OnLoadClick(self, event):
        self.button_waiting("search")
        if not self._ensures_reload():
            return

        dialog = wx.DirDialog(self,
                              "Choose input directory  (files might not be shown)",
                              os.getcwd(), wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        # Run the window and check if it successfully finishes
        res = dialog.ShowModal()
        if res == wx.ID_OK:
            # Retain a reference of the user selected path
            self.dirname = dialog.GetPath()
        elif res == wx.ID_CANCEL:
            dialog.Destroy()
            return
        dialog.Destroy()
        self._load_data()
        self.button_ready("search")

    def OnCenter(self, event):
        self.button_waiting("center")
        # Align the polarimetric images
        if self.retriever.images[0].get("Irr", None) is not None:
            self.retriever.align_polarimetric_images()

        # Replot everything
        self.hasStokes = True
        self._reconfig()
        self._show_dataset()

        self.button_ready("center")

        # self.entries.GetButton("swap").Enable()
        # self.plotter.select_page("Cropped Stokes")

    def OnSwap(self, event):
        self.button_waiting("swap")
        values = self.entries.GetValues()

        topR, bottomR = values["window_center"]
        top, bottom = values["window_centerR"]

        self.entries.SetValue(window_center=(top, bottom), window_centerR=(topR, bottomR))
        self.updated_old_entries()

        if self.retriever.images[0].get("Irr", None) is not None:
            self.retriever.align_polarimetric_images()
        self._reconfig()
        self.button_ready("swap")

    def OnAutoadjust(self, event):
        self.button_waiting("autoadjust")
        # Adjust the phase origin
        self.retriever.select_phase_origin()
        phase_origin = self.retriever.options["origin"]
        self.entries.SetValue(phase_origin=[str(x) for x in phase_origin])
        self.updated_old_entries()

        if self.entries.GetValues()["bandwidth"] == 0:
            # If not set yet, let's estimate a bandwidth
            self.retriever.compute_bandwidth()

            bw = self.retriever.options["bandwidth"]

            # Set the autoadjusted values to the entry panel
            self.entries.SetValue(bandwidth=bw)
            self.updated_old_entries()

        else:  # If it's already set, lets just show it
            self.retriever._compute_spectrum()

        # Replot everything
        self.hasStokes = True
        self.hasSpectrum = True
        self._reconfig()

        self.plotter.select_page("Spectrum")

        # Enable the begin button and disable the Search button
        self.entries.GetButton("begin").Enable()
        # self.entries.GetButton("search").Disable()
        self.button_ready("autoadjust")

    def OnRetrieve(self, event):
        self.button_waiting("begin")
        self.entries.GetButton("center").Disable()
        self.entries.GetButton("swap").Disable()
        self.entries.GetButton("autoadjust").Disable()
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

        # First, we need to clear all possible lines
        for i, ax in enumerate(axes):
            ax.clear()
            ax.plot([], [])
            ax.set_title(f"MSE {['X', 'Y'][i]} component (loading...)")
            ax.set_xlim(0, self.entries.GetValue("n_iter", 100))
            ax.set_ylim(MSE_THRESHOLD, 0.15)
            ax.set_xlabel("Iterations")
            ax.set_ylabel("MSE")

        # Then, we call the retriever to commence the process
        self.retriever.config(mode="vectorial")  # self.entries.GetValue("mode")
        self.retriever.config(pixel_size=self.entries.GetValue("pixel_size"))
        self.retriever.retrieve(args=(plot,), monitor=False)
        wx.CallLater(delta_t, self.retriever.monitor_process, plot)
        wx.CallLater(delta_t, self.OnCheckCompletion)
        wx.CallLater(delta_t*2, self.plotter.select_page, "MSE")


    def OnCheckCompletion(self, event=None):
        if self.retriever.finished:
            self.OnFinished()
        else:
            wx.CallLater(delta_t, self.OnCheckCompletion)

    def OnFinished(self):
        """Plot results once the phase retriever is finished"""
        self.finished = True
        Ex, Ey = self.retriever.get_trans_fields()
        # Ez = np.zeros_like(Ex)
        # self.update_results(Ex, Ey, Ez)

        # TODO: Prepare the propagator to explore the phase retrieval results...
        configs = self.entries.GetValues()
        pixel_size = configs["pixel_size"]/configs["lamb"]
        self.propagator["Ex"] = Ex
        self.propagator["Ey"] = Ey
        self.propagator["pixel_size"] = pixel_size
        self.propagator.create_spectra()
        self.propagator.create_gamma()
        self.update_results(z=0)
        self.plotter.set_colorbar("Results", share=(3, 5, 1))
        self.plotter.select_page("Results")
        self.button_ready("begin", enable_ignore=True)
        self.entries.GetButton("begin").Disable()
        self.entries.GetButton("export").Enable()

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
        self.update_results(z=z)

    # --- FILE-MENU OnEvent methods ---
    def OnDump(self, event):
        """Dump current configuration on a json file, to be loaded later."""
        configs = self.entries.GetValues()
        # Open a dialog to ask where to save it
        with wx.FileDialog(self, "Save configuration", wildcard="*.json",
                           defaultFile=self.beam_name + ".json",
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

        self._load_config(json_path=path, change_path=True)
        self._load_data()
        self._reconfig()

    def OnExport(self, event):
        self.button_waiting("export")
        try:
            Ex, Ey, Ez = self.propagator.propagate_field_to(0)
            data = {"Ex":Ex, "Ey":Ey, "Ez": Ez}
            basename = self.beam_name + "_retrieved.npz"

            with wx.FileDialog(self, "Save recovered data",
                               self.dirname, basename,
                               style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                               wildcard="*.npz") as save_dialog:
                if save_dialog.ShowModal() == wx.ID_CANCEL:
                    self.button_ready("export")
                    return
                path = save_dialog.GetPath()
                if not path.endswith(".npz"):
                    path += ".npz"
                np.savez(path, **data)
        except:
            dialog = wx.MessageDialog(self, "Could not export any recovered data",
                    style=wx.OK | wx.CENTRE | wx.ICON_ERROR)
            dialog.ShowModal()
        self.button_ready("export")

    def OnQuit(self, event):
        self.Close()

    # --- Utils ---
    def _reconfig(self):
        # First, we need to get all the configurations from the entries
        values = self.entries.GetValues()
        rect_center = values["window_center"]
        width = values["window_size"]
        top = [int(i)-width//2 for i in rect_center]
        bottom = [int(i)+width//2 for i in rect_center]
        rect_centerR = values["window_centerR"]
        widthR = values["window_sizeR"]
        topR = [int(i)-widthR//2 for i in rect_centerR]
        bottomR = [int(i)+widthR//2 for i in rect_centerR]
        bw = values["bandwidth"]*2
        # Change configurations on the retriever
        self.retriever.config(path=values["path"], lamb=values["lamb"],
                              rect=(top, bottom), bandwidth=bw/2, dim=width,
                              pixel_size=values["pixel_size"], n_iter=values["n_iter"])

        # Plot the relevant information...
        self.roi = values["roi"]
        # self._plot_irradiance()
        self._plot_stokes()

        # Draw the rectangles and circle specifiying the region of interest
        self.plotter.set_rectangle("Irradiance (full size)", top, width, width)
        self.plotter.set_rectangle("Irradiance (full size)", topR, widthR, widthR, color="red")

        # Draw the bandwidth if so
        if self.hasSpectrum:
            self.retriever._compute_spectrum()
            self._plot_bandwidth()
            self.plotter.set_circle("Spectrum", (width//2, width//2), bw, color="red")

    def _ensures_reload(self, hard=True):
        sayYes = True
        if self.beam_name and any([self.hasStokes, self.hasSpectrum, self.finished]):
            msg = ("New data will be loaded, then all previous configuration and "
                   "retrieval will be lost." if hard else "If config. parameters "
                   "change, the current retrieval will be lost.")
            msg += "\n\nConsider to Export results, before. Continue?"
            with wx.MessageDialog(self, caption="Warning!", message=msg,
                                  style=wx.YES_NO | wx.ICON_EXCLAMATION) as dialog:
                sayYes = dialog.ShowModal() == wx.ID_YES

            if sayYes:
                # from scratch
                self.plotter.clean()
                del self.retriever
                self.init_data(hard)
                self._load_data(load_json=False) if not hard else None
                self._reconfig() if not hard else None

        return sayYes

    def _load_config(self, json_path, change_path):
        with open(json_path, "r") as f:
            loaded_configs = json.load(f)
        if change_path:
            self.dirname = loaded_configs["path"]
        else:
            _ = loaded_configs.pop("path", None)
        self.entries.SetValue(**loaded_configs)
        self.updated_old_entries()

    def _load_data(self, silent=False, load_json=True):
        # We now update the entry to contain the selected path
        self.entries.SetValue(path=self.dirname)
        self.updated_old_entries()

        # Trying to load a configuration
        json_candidates = glob(os.path.join(self.dirname, "*.json"))
        if load_json and json_candidates:
            (print(f"More than one config.json found. Taking the first...")
             if len(json_candidates) > 1 else None)
            self._load_config(json_candidates[0], change_path=False)

        # Finally, we load all images into the phase retriever
        try:
            assert os.path.isdir(self.dirname), Exception(f"{self.dirname} is not a directory")
            self.beam_name = self.retriever.load_dataset(self.dirname, ftype=self.entries.GetValue("ext"))

            # We show the important images through the plots
            self._show_dataset()
            # We find the beam-windows with the size given by the entries.
            self.find_beams()
            if self.retriever.images[0].get("Irr", None) is not None:
                self.entries.GetButton("center").Enable()
            self.entries.GetButton("autoadjust").Enable()
        except Exception as e:
            if not silent:
                error_dialog = wx.MessageDialog(self, f"Error loading data in  "
                                                      f"{self.entries.GetValue('ext').upper()} "
                                                      f"format\n\n{e}",
                                                style=wx.ICON_ERROR | wx.OK)
                error_dialog.ShowModal()

    def _show_dataset(self):
        # Irradiance plots with the rectangle indicating where exactly the window is
        # located.
        self.plotter.set_imshow("Irradiance (full size)", self.retriever.irradiance,
                                cmap="gray")

    def find_beams(self):
        configs = self.entries.GetValues()
        window_size = configs["window_size"]
        window_sizeR = configs["window_sizeR"]
        self.retriever.config(dim=window_size)
        top, bottom = self.retriever.center_window()
        rect_center = top[0] + window_size // 2, top[1] + window_size // 2
        topR, bottomR = self.retriever.center_window(ref_beam_size=window_sizeR)
        if topR is None:
            topR = [0, 0]
        rect_centerR = topR[0] + window_sizeR // 2, topR[1] + window_sizeR // 2

        self.entries.SetValue(window_center=[str(x) for x in rect_center],
                              window_centerR=[str(x) for x in rect_centerR])
        self.updated_old_entries()

        self.hasStokes = True  # if center_window success, stokes are ready
        self._reconfig()
        self.entries.GetButton("swap").Enable()

    # def _plot_irradiance(self):
    #     self.plotter.set_imshow("Cropped irradiance", self.retriever.cropped_irradiance,
    #                             cmap="gray", roi=self.roi)

    def _plot_stokes(self):
        if not self.hasStokes:
            return
        s0M = None
        isnew = []
        for idx, stokes_image in enumerate(self.retriever.get_stokes()):
            s0M = s0M or stokes_image.max()
            isnew.append(self.plotter.set_imshow("Cropped Stokes", stokes_image/s0M,
                                                 title=f"$S_{idx}$",
                                                 cmap="seismic", shape=(2,2),num=idx+1,
                                                 vmin=-1, vmax=1, roi=self.roi))
        if any(isnew):
            self.plotter.set_colorbar("Cropped Stokes", share=(0, 1, 2, 3))

    def _plot_bandwidth(self):
        if not self.hasSpectrum:
            return
        a_ft_log = np.log10(self.retriever.a_ft)
        self.plotter.set_imshow("Spectrum", a_ft_log, cmap="viridis")

    def update_results(self, z=0):
        if not self.finished:
            return
        Ex, Ey, Ez = self.propagator.propagate_field_to(z)
        cmap_ph = "hsv"
        self.plotter.set_imshow("Results", abs(Ex), title="$|E_x|$",
                                shape=(3, 2), num=1, cmap="gray", roi=self.roi,
                                pixel_size=self.entries.GetValue("pixel_size"))
        self.plotter.set_imshow("Results", np.angle(Ex), title=r"$\phi_x$",
                                shape=(3, 2), num=2, cmap=cmap_ph,
                                vmin=-np.pi, vmax=np.pi, roi=self.roi,
                                pixel_size=self.entries.GetValue("pixel_size"))
        self.plotter.set_imshow("Results", abs(Ey), title="$|E_y|$",
                                shape=(3, 2), num=3, cmap="gray", roi=self.roi,
                                pixel_size=self.entries.GetValue("pixel_size"))
        self.plotter.set_imshow("Results", np.angle(Ey), title=r"$\phi_y$",
                                shape=(3, 2), num=4, cmap=cmap_ph,
                                vmin=-np.pi, vmax=np.pi, roi=self.roi,
                                pixel_size=self.entries.GetValue("pixel_size"))
        self.plotter.set_imshow("Results", abs(Ez)**2, title="$|E_z|$",
                                shape=(3, 2), num=5, cmap="gray", roi=self.roi,
                                pixel_size=self.entries.GetValue("pixel_size"))
        self.plotter.set_imshow("Results", np.angle(Ez), title=r"$\phi_z$",
                                shape=(3, 2), num=6, cmap=cmap_ph,
                                vmin=-np.pi, vmax=np.pi, roi=self.roi,
                                pixel_size=self.entries.GetValue("pixel_size"))

    def updated_old_entries(self):
        self.old_entries = {k: v for k, v in self.entries.GetValues().items()}

    def button_waiting(self, name):
        button = self.entries.GetButton(name)
        if button:
            button.Disable()
            button.SetLabel(f"{button.GetLabel()} (loading...)")

    def button_ready(self, name, enable_ignore=False):
        button = self.entries.GetButton(name)
        if button:
            button.Enable() if not enable_ignore else None
            button.SetLabel(button.GetLabel().replace(" (loading...)", ""))


if __name__ == "__main__":
    app = wx.App()
    gui = wxGUI(None, "Phase retriever")
    gui.Show()

    app.MainLoop()
