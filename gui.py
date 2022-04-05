#!/usr/bin/python3
"""
GUI for the calculation of the phase retreival with polarimetric images.

@author = Marcos Pérez Aviñoa
"""
import numpy as np
import json
from scipy.fft import fft2, ifft2, fftshift, ifftshift
import tkinter as tk
import tkinter.ttk as ttk
from tkinter.filedialog import askdirectory, asksaveasfilename, askopenfilename
from tkinter.messagebox import showinfo, showerror
import imageio
import multiprocessing as mp
import os
"""
fft2 = np.fft.fft2
ifft2 = np.fft.ifft2
fftshift = np.fft.fftshift
ifftshift = np.fft.ifftshift
"""

# Functions and widgets
from helper.file_selector import get_polarimetric_names_kavan, get_polarimetric_names
from helper.video_processing import propaga_video
from helper.multipass_retrieval import multi   # Multipass phase retrieval function!
from helper.plotsnotebook import PlotsNotebook
from helper.beamnotebook import BeamNotebook
from helper.menubar import Menubar
from helper.focalprop import FocalPropagator
from helper.exportwindow import ExportWindow

class PhaseRetrieverGUI:
    def __init__(self, parent, bg):
        self.parent = parent
        # Finished recovering?
        self.recovered_phases = False
        # Set window name
        self.parent.title("Phase Retriever")
        # Focal propagator
        self.propagator = FocalPropagator()
        
        # Create a menu
        filecascade = {
                "Load dataset":(self.loadset, "i"), 
                "Load configuration":(self.loadconfig, "Ctrl+O"),
                "Save configuration":(self.saveconfig, "Ctrl+S"),
                "Export images and video":(self.export, "Ctrl+E"),
                "Exit":(self.quit, "q")}
        options = {"File":filecascade}
        self.menubar = Menubar(parent, bg, options)
        self.parent.config(menu=self.menubar)

        # Add the beam configuration entries
        self.beam_notebook = BeamNotebook(parent, borderwidth=0, relief="raised")
        self.beam_notebook.bind_update("explorer", self.propagate_z)
        self.beam_notebook.pack(side=tk.LEFT, anchor=tk.N+tk.W, fill="y")
        if not self.recovered_phases:
            self.beam_notebook.set_state("explorer", "disable")

        # Add the notebook with subplots
        self.subplot_notebook = PlotsNotebook(parent, bg, bind=self.plotclick)
        self.subplot_notebook.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)

        # Bindings
        self.parent.bind("q", self.quit)
        self.parent.bind("i", self.loadset)
        self.parent.bind("<Return>", self.begin_phase_retrieval)
        self.parent.bind("<Control-o>", self.loadconfig)
        self.parent.bind("<Control-s>", self.saveconfig)
        self.parent.bind("<Control-e>", self.export)
        self.beam_notebook.set_callback("config", "begin", self.begin_phase_retrieval)
        self.parent.protocol("WM_DELETE_WINDOW", self.quit)

        self.processes = None
        self.zetes = None

    def loadset(self, event=None):
        # Get directory name
        newdir = askdirectory(mustexist=True)

        # Update everything if successful
        if newdir:
            self.set_directory = newdir
            self.update_data()

    def loadconfig(self, event=None):
        # Get the file name
        fname = askopenfilename()
        if fname:
            try:
                with open(fname, "r") as f:
                    data = json.load(f)
            except:
                showerror("Error", f"File {fname} does not contain configuration data!")
                return
        else:
            return
        # Once the data is loaded, update all configs!
        self.set_directory = data["current path"]
        for key in data:
            # Si les entrades no hi son, passem
            try:
                self.beam_notebook.update_element("config", key, data[key])
            except:
                showerror("Error", f"File {fname} does not contain configuration data!")
                return
        self.update_data()

    def saveconfig(self, event=None):
        # Get the file name
        fname = asksaveasfilename()
        if fname:
            if not ("json" in fname):
                fname += ".json"
            # Get all entries
            data = self.beam_notebook.get("config")
            with open(fname, "w") as f:
                json.dump(data, f, indent=4) 

    def update_data(self, event=None):
        # Set the configuration entry name
        self.beam_notebook.update_element("config", "current path", self.set_directory)

        # Load all image names
        # TODO: Add selector for fname kind
        self.names_dict = get_polarimetric_names_kavan(self.set_directory)
        if not self.names_dict:
            self.names_dict = get_polarimetric_names(self.set_directory,
                    ftype="png")
        self.load_plots()

    def load_plots(self, event=None):
        self.zetes = list(self.names_dict.keys())
        self.zetes.sort()
        self.I = []
        n_pol = 6
        for i in range(n_pol):
            im = imageio.imread(self.names_dict[self.zetes[0]][i])
            if len(im.shape)>2:
                im = im[:, :, 1]
            self.I.append(im)
        ny, nx = self.I[0].shape
        center = (nx//2, ny//2)
        radius = 25

        # Recenter X and Y images
        self.recenter_xy()

        # Reference image
        self.im_ref = self.I[0]+self.I[2]

        # Act. entries
        self.beam_notebook.update_element("config", "radius", radius)
        self.beam_notebook.update_element("config", "beam center", f"{center[0]}, {center[1]}")
        self.beam_notebook.update_element("config", "phase origin", f"{center[0]}, {center[1]}")

        self.data = self.beam_notebook.get("config")
        self.n = int(self.data["rectangle"])//2
        self.r = int(self.data["radius"])

        self.rect = [nx//2-self.n, ny//2-self.n, nx//2+self.n, ny//2+self.n]    # Assign rectangle borders
        # Load image per se
        self.subplot_notebook.plot_image(self.im_ref, self.n, 0, "beam center")

        # Update ROS
        self.update_ROS()

        # Update autocorrelation plot
        self.update_autocorr()

        # Update phase plot
        self.update_phase()

        # Draw all rects
        self.redraw_patches()
    
    def recenter_xy(self):
        imx = self.I[0]
        imy = self.I[2]
        ny, nx = imx.shape
        ftx = fftshift(fft2(ifftshift(imx)))
        fty = fftshift(fft2(ifftshift(imy)))
        # Correlation
        fcorr = np.conj(ftx)*fty
        corr = fftshift(ifft2(ifftshift(fcorr)))
        # Maxima
        loc = np.unravel_index(np.argmax(abs(corr)), corr.shape)

        # Displace Y with respect to X
        dy = -loc[0]+ny//2
        dx = -loc[1]+nx//2
        imy_rolled = np.roll(imx, (dy, dx), axis=(0, 1))
        self.I[1] = imy_rolled

    def update_ROS(self, event=None):
        x0, y0, x1, y1 = self.rect
        self.ROS = [I[y0:y1, x0:x1] for I in self.I]

    def update_autocorr(self, event=None):
        """Calculate the spectrum of the autocorrelation of the ROS."""
        x0, y0, x1, y1 = self.rect
        otf = fftshift(fft2(self.im_ref[y0:y1, x0:x1]))
        self.subplot_notebook.plot_image(np.log(abs(otf)), self.r, 0, "Autocorrelation")

    def update_phase(self, event=None):
        x0, y0, x1, y1 = self.rect
        self.delta = np.arctan2(self.ROS[4]-self.ROS[5], self.ROS[2]-self.ROS[3])
        self.subplot_notebook.plot_image(self.delta, self.n*.1, 0, "phase")

    def plotclick(self, event=None):
        """Get the possible changes in the ROS, radius or phase origin"""
        new_rect = self.subplot_notebook.plots["beam center"].rect
        new_r = self.subplot_notebook.plots["Autocorrelation"].r
        new_phase = self.subplot_notebook.plots["phase"].position

        # Transform into ints
        new_rect = [int(x) for x in new_rect]
        # Update ROS if necessary
        if new_rect != self.rect:
            self.rect = new_rect
            self.update_ROS()
            self.update_autocorr()
            self.update_phase()

        self.beam_notebook.update_element("config", "beam center", f"{int(new_rect[0])}, {int(new_rect[1])}")
        self.beam_notebook.update_element("config", "phase origin", f"{int(new_phase[0])}, {int(new_phase[1])}")
        self.beam_notebook.update_element("config", "radius", f"{int(new_r)}")

    def redraw_patches(self, event=None):
        """Redraw all patches in plots"""
        # Get the data coordinates
        center = self.data["beam center"]
        center = center.split(",")
        center = [int(x) for x in center]
        self.radius = int(self.data["radius"])
        self.n = int(self.data["rectangle"])//2
        phase = self.data["phase origin"]
        phase = phase.split(",")
        self.phase = [int(x) for x in phase]

        self.subplot_notebook.plots["beam center"].draw_rectangle(center, self.n*2, self.n*2)
        self.subplot_notebook.plots["Autocorrelation"].draw_circle((self.n, self.n), 
                self.r)
        self.subplot_notebook.plots["phase"].draw_circle(self.phase, 
                self.n*.1)

    def begin_phase_retrieval(self, event=None):
        """Begin the phase retrieval process by spawning two different python processes, one for each
        polarization component."""
        # Blocking the second page of the notebook
        self.beam_notebook.set_state("explorer", "disable")
        if not self.zetes:
            showerror(title="Error",
                    message="Dataset not yet loaded!")
            return
        x0, y0, x1, y1 = self.rect
        # Get the important data
        self.data = self.beam_notebook.get("config")
        self.lamb = float(self.data["wavelength"])
        self.r = float(self.data["radius"])*.5
        phase = self.data["phase origin"]
        niter = int(self.data["niter"])
        m = abs(float(self.data["magnification"]))
        phase = phase.split(",")
        self.phase = [int(x) for x in phase]
        self.p = float(self.data["pitch"])/m    # Effective pixel size!

        # Create the amplitudes
        self.Ax = []
        self.Ay = []
        for z in self.zetes:
            noms = [self.names_dict[z][i] for i in range(6)]
            Ix = imageio.imread(noms[0])[y0:y1, x0:x1]
            Iy = imageio.imread(noms[2])[y0:y1, x0:x1]
            self.Ax.append(np.sqrt(Ix))
            self.Ay.append(np.sqrt(Iy))
            
        # Create the free space transfer function
        y, x = np.mgrid[-self.n:self.n, -self.n:self.n]
        self.circ = x*x+y*y < self.r**2
        umax = .5/self.p
        self.y = y/self.n*umax
        self.x = x/self.n*umax
        rho2 = self.x*self.x+self.y*self.y
        wz = np.sqrt(np.complex_(1/self.lamb**2-rho2))  # mm^-1, spatial frequency in the z direction
        # Check if all images are equally spaced. Work only with equally spaced images.
        old_delta = self.zetes[1]-self.zetes[0]
        max_i = 1000 
        for i in range(len(self.zetes)-1):
            new_delta = self.zetes[i+1]-self.zetes[i]
            if new_delta != old_delta:
                max_i = i
                break
        z = old_delta*self.names_dict[0]["scale"]

        H = np.exp(2j*np.pi*z*wz)*self.circ
        H[:] = fftshift(H)
        phi_0 = np.zeros((self.n*2, self.n*2))
        self.wz = wz    # FIXME: Dirty hack

        # Create MSE lists to hold all values
        self.mse = [[], []]

        # Spawn processess with queues
        self.queues = [mp.Queue(), mp.Queue()]
        p1, c1 = mp.Pipe()
        p2, c2 = mp.Pipe()
        self.reals = [mp.Array("d", range(0, int((self.n*2)**2))),
                mp.Array("d", range(0, int((self.n*2)**2)))]
        self.imags = [mp.Array("d", range(0, int((self.n*2)**2))),
                mp.Array("d", range(0, int((self.n*2)**2)))]
        self.processes = \
                [mp.Process(target=multi, args=(H, niter, phi_0, *(self.Ax[:max_i])), 
                    kwargs={"queue":self.queues[0], "real":self.reals[0], 
                        "imag":self.imags[0]}),
                 mp.Process(target=multi, args=(H, niter, phi_0, *(self.Ay[:max_i])), 
                    kwargs={"queue":self.queues[1], "real":self.reals[1],
                        "imag":self.imags[1]})]
        # Start each process
        for process in self.processes:
            process.start()

        # Begin monitorization of each process
        self.running = True
        self.monitor_processes()

    def monitor_processes(self, event=None):
        if self.running:
            alive = False
            for i, process in enumerate(self.processes):
                #FIXME: això pot no acabar mai...
                full = True
                while full:
                    try:
                        data = self.queues[i].get_nowait()
                        self.mse[i].append(data)
                    except:
                        full = False
                # Check if alive
                alive = alive or process.is_alive()

            # Update XY mse plot
            self.subplot_notebook.plots["MSE"].plot(0, self.mse[0])
            self.subplot_notebook.plots["MSE"].plot(1, self.mse[1])
            # If both processes ded, end them
            self.running = alive and self.running
            # Check again after 20ms or so
            self.parent.after(20, self.monitor_processes)
        else:
            for i, process in enumerate(self.processes):
                process.join()
            # We successfully recovered the phases
            self.recovered_phases = True
            self.beam_notebook.set_state("explorer", "enable")
            # Retrieve the phases
            self.exphi_x = (np.asarray(self.reals[0])+1j*np.asarray(self.imags[0]))
            self.exphi_x = self.exphi_x.reshape((2*self.n, 2*self.n))
            self.exphi_y = np.asarray(self.reals[1])+1j*np.asarray(self.imags[1])
            self.exphi_y = self.exphi_y.reshape((2*self.n, 2*self.n))

            self.save_results()

            # Irradiance propagator
            self.propagator.set_fields(self.Ax[0]*self.exphi_x,
                                       self.Ay[0]*self.exphi_y,
                                       self.wz)
            I = self.propagator.propagate_to(0)
            self.subplot_notebook.swap_array(I, self.n, 0, "explorer", vmin=0,
                vmax=1, cmap="gray")

    def save_results(self, event=None):
        # Create save path if not existant
        result_path = self.data["current path"]+"_retrieved"
        self.result_path = result_path
        try:
            os.mkdir(result_path)
        except:
            pass

        # Save the amplitudes
        path_save = os.path.join(result_path, "amplitudes.npz")
        np.savez(path_save, Ax=self.Ax[0], Ay=self.Ay[0])
        ny, nx = self.Ax[0].shape
        n = min(ny, nx)

        # Construct the phases with the proper phase difference
        phi_origin = self.data["phase origin"]
        phi_origin = phi_origin.split(",")
        phi_origin = [min(n, int(x)) for x in phi_origin]
        # Adjusting the phases. I take phase_origin to have exactly the
        # phase value 0. Then, to the y component I add the value self.delta
        # at phase_origin to create (simulate) the experimental phase difference.
        # TODO: Check if there could be a better method for doing this.
        """
        dx = np.angle(self.exphi_x)
        dy = np.angle(self.exphi_y)
        dx[:] = dx-dx[phi_origin[1], phi_origin[0]]
        dy[:] = dy-dy[phi_origin[1], phi_origin[0]]
        dy += self.delta[phi_origin[1], phi_origin[0]]
        
        # Save the phases
        path_save = os.path.join(result_path, "phases.npz")
        np.savez(path_save, phi_x=np.exp(1j*dx), phi_y=np.exp(1j*dy))

        Ux = self.Ax[0]*np.exp(1j*dx)
        Uy = self.Ay[0]*np.exp(1j*dy)
        """
        dx = self.exphi_x/(abs(self.exphi_x)+1e-16)
        dy = self.exphi_y/(abs(self.exphi_y)+1e-16)
        #phi_origin = np.unravel_index(np.argmax(self.Ay[0]), self.Ay[0].shape)
        dx[:] = dx/dx[phi_origin[1], phi_origin[0]]
        dy[:] = dy/dy[phi_origin[1], phi_origin[0]]
        dy *= np.exp(1j*self.delta[phi_origin[1], phi_origin[0]])

        self.dx = dx
        self.dy = dy
        # Save the phases
        path_save = os.path.join(result_path, "phases.npz")
        np.savez(path_save, phi_x=dx, phi_y=dy, ros=self.r)

    def propagate_z(self, z):
        z_w = z*self.lamb
        I = self.propagator.propagate_to(z_w)
        # Plot the result...
        self.subplot_notebook.swap_array(I, self.n, 0, "explorer", vmin=0,
                vmax=1, cmap="gray")

    def export(self, *args):
        # Crea una finestra de diàleg on es demani el nombre d'imatges
        try:
            Ux = (self.Ax[0]*self.dx)
            Uy = (self.Ay[0]*self.dy)

            self.config = (Ux, Uy, self.y, self.x, self.circ, self.result_path)

        except:
            showerror("Error", "Cannot export images and/or video currently.") 
            return

        win = ExportWindow(self.config, self.lamb, propaga_video)

        """
        try:
            showinfo(title="Recording images and video", 
                    message="Recording images and video, be patient please...")
            propaga_video(Ux, Uy, self.y, self.x, self.circ, 
                    result_path, delta_z=delta_z, 
                    nim=n, Izmax=None, lamb=self.lamb)
            showinfo(title="Finished recording", 
                    message="Recording successful!")
        except:
            showinfo(title="Video recording error",
                    message="Video could not be recorded properly.")
        """

    def quit(self, event=None):
        self.parent.quit()
        self.parent.destroy()
        if self.processes:
            for process in self.processes:
                process.join()

def delta_z(nom_pol):
    """Calculate the correlation between the X and Y components of a beam."""
    I = []
    for nom in nom_pol:
        # IMPORTANT: Convert to floats or signed ints before proceeding
        I.append(imageio.imread(nom).astype(np.float_))
    delta = np.arctan2(I[4]-I[5], I[2]-I[3])
    return delta

if __name__ == "__main__":
    import platform
    root = tk.Tk()
    style = ttk.Style()
    if platform.system() == "Linux":
        style.theme_use("clam")
    bg = style.lookup("TFrame", "background")
    root["background"] = bg
    gui = PhaseRetrieverGUI(root, bg)
    root.mainloop()
