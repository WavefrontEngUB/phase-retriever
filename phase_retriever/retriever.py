import numpy as np
from scipy.fft import fft2, ifft2, fftshift, ifftshift
import multiprocessing as mp
import imageio

from .algorithm import multi
from .misc.radial import get_function_radius
from .misc.file_selector import get_polarimetric_names
from .misc.central_region import find_rect_region
from .misc.stokes import get_stokes_parameters

def bound_rect_to_im(shape, rect):
    """Return correct rect coordinates, bound to the physical limits given by shape."""
    ny, nx = shape
    top, bottom = rect
    x0, y0 = top
    x1, y1 = bottom
    width = abs(x0-x1)
    height = abs(y0-y1)
    if x0 < 0:
        x0 = 0
        x1 = width
    elif x1 >= nx:
        x1 = nx
        x0 = nx-width
    if y0 < 0:
        y0 = 0
        y1 = height
    elif y1 >= nx:
        y1 = nx
        y0 = nx-height

    return (x0, y0), (x1, y1)

def lowpass_filter(bw, *amps):
    ny, nx = amps[0].shape
    y, x = np.mgrid[-ny//2:ny//2, -nx//2:nx//2]
    mask = x*x + y*y < bw*bw
    filtered = []
    for A in amps:
        a_ft = fftshift(fft2(ifftshift(A)))
        a_ft *= mask
        a_filt = fftshift(ifft2(ifftshift(a_ft)))
        filtered.append(a_filt)
    return filtered

class SinglePhaseRetriever():
    # TODO: Crea una classe que encapsuli completament el mètode de recuperació de fase
    options = {
            "pixel_size":None,  # MUST BE SCALED ACCORDING TO THE WAVELENGTH
            "dim"       :256,
            "rect"      :None,
            "n_max"     :200,
            "eps"       :0.01,
            "bandwidth" :None,
            "origin"    :None,
            "lamb"      :None,
            "path"      :None
            }
    irradiance = None
    images = {}
    cropped = {}
    cropped_irradiance = None
    a_ft = None
    mse = [[], []]
    def __init__(self, n_max=200):
        self.options["n_max"] = n_max          # Maximum number of iterations

    def __getitem__(self, key):
        return self.options[key]

    def __setitem__(self, key, value):
        # TODO: Check types correctly
        self.config(**{key:value})

    def load_dataset(self, path=None):
        self.irradiance = None
        self.images = {}
        # If the user does not input a path
        if not path:
            # If there is no path already inputted
            if not self["path"]:
                raise ValueError("Dataset path must be specified")
            else:
                path = self["path"]
        else:
            self.options["path"] = path
        self.polarimetric_sets = get_polarimetric_names(path)
        if not self.polarimetric_sets:
            raise ValueError(f"Cannot load polarimetric images from {path}")

        # Load all images into memory
        for z in self.polarimetric_sets:
            self.images[z] = {}
            for polarization in self.polarimetric_sets[z]:
                if type(polarization) != int:
                    continue
                path = self.polarimetric_sets[z][polarization]
                image = imageio.imread(path)
                self.images[z][polarization] = image.astype(np.float64)

        # Compute irradiance
        self._compute_irradiance()

    def _compute_irradiance(self):
        # Compute only the irradiance in the initial plane
        self.irradiance = 0
        if not self.images:
            raise ValueError("Dataset not yet specified/loaded.")
        # We only use one of the planes to compute the irradiance
        zetes = list(self.images.keys())
        z = zetes[0]    # We don't care which one...
        images = self.images[z]
        for polarization in images:
            if type(polarization) != int:
                continue
            self.irradiance += images[polarization]

        self.irradiance /= 3

    def _crop_images(self, top, bottom):
        if not self.images:
            raise ValueError("Images not yet loaded")

        y0, x0 = top
        y1, x1 = bottom
        first = True
        for z in self.images:
            self.cropped[z] = {}
            if first:
                self.cropped_irradiance = 0
            for polarization in self.images[z]:
                if type(polarization) != int:
                    continue
                image = self.images[z][polarization]
                cropped = image[y0:y1, x0:x1]
                self.cropped[z][polarization] = cropped
                if first:
                    # We also compute the cropped irradiance
                    self.cropped_irradiance += cropped
            first = False
        # And that's THA'

    def center_window(self):
        """Center the window of size dim X dim on the region with the most energy content."""
        # We do it based on the total irradiance.
        if not self.images:
            self.load_dataset()
        try:
            _ = self.irradiance.shape
        except:
            # Irradiance not yet computed
            self._compute_irradiance()
        top, bottom = find_rect_region(self.irradiance, self["dim"])

        # Now, we crop all images to the region specified by the top, bottom pair of coords.
        self["rect"] = top, bottom
        self._crop_images(top, bottom)
        return top, bottom

    def select_phase_origin(self):
        """Automatically select the point of highest intensity as the phase origin of the
        phase retrieval process."""
        if not self.cropped:
            self.center_window()

        # Find the location of the maximum intensity
        yloc, xloc = np.where(self.cropped_irradiance == self.cropped_irradiance.max())
        loc = yloc[0], xloc[0]
        self["origin"] = loc

    def _compute_spectrum(self):
        if not self.cropped:
            self._crop_images(*self["rect"])
        ft = fftshift(fft2(ifftshift(self.cropped_irradiance)))
        self.a_ft = a_ft = np.real(np.conj(ft)*ft)

    def compute_bandwidth(self, tol=1e-4):
        if not self.cropped:
            self._crop_images(*self["rect"])
        # Compute the Fourier Transform of the cropped irradiance to get its bandwidth
        self._compute_spectrum()
        r = get_function_radius(self.a_ft, tol=tol)/2
        if not r:
            raise ValueError("Could not estimate the Bandwidth of the beam")
        self.options["bandwidth"] = r
        return self.a_ft

    def retrieve(self, args=(), monitor=True):
        """Phase retrieval process. Using the configured parameters, begin the phase retrieval process."""
        self.mse = [[], []] # Delete all possible values of the last mse
        if not self.options["pixel_size"]:
            raise ValueError("Pixel size not specified")
        if not self.options["bandwidth"]:
            self.compute_bandwidth()
        if not self.options["origin"]:
            self.select_phase_origin()
        lamb = self.options["lamb"]
        p_size = self.options["pixel_size"]/lamb
        bw = self.options["bandwidth"]
        # First, we construct the field amplitudes
        self.A_x = A_x = []
        self.A_y = A_y = []
        for z in self.cropped:
            I_x = self.cropped[z][2]
            I_y = self.cropped[z][0]
            # Filtering the irradiances to remove high frequency noise fluctuations
            A_xfilt = np.real(np.sqrt(lowpass_filter(bw*2, I_x)[0]))
            A_yfilt = np.real(np.sqrt(lowpass_filter(bw*2, I_y)[0]))
            A_x.append(A_xfilt)
            A_y.append(A_yfilt)
        # Then, we need to compute the free space transfer function H
        n = self.options["dim"]
        ny, nx = np.mgrid[-n//2:n//2, -n//2:n//2]
        bandwidth_mask = (ny*ny+nx*nx < bw*bw)
        umax = .5/p_size
        x = nx/nx.max()*umax
        y = ny/ny.max()*umax
        rho2 = x*x+y*y
        gamma = np.zeros((n, n), dtype=np.float_)
        np.sqrt(1-rho2, out=gamma, where=bandwidth_mask)
        zetes = list(self.images.keys())
        dz = (zetes[1]-zetes[0])/lamb
        H = np.exp(2j*np.pi*gamma*dz)
        # Get the bandwidth of the beam we are computing and remove all values of H lying outside this region.
        H[:] = fftshift(H*bandwidth_mask)
        # Finally, we create an initial guess for the phase of both components
        #phi_0 = np.zeros((n, n))
        phi_0 = np.random.rand(n, n)

        # We set up the multiprocessing environment. Just two processes, as we have two phases to recover
        self.queues = [mp.Queue(), mp.Queue()]
        p1, c1 = mp.Pipe()
        p2, c2 = mp.Pipe()
        # As queues only work with base types, we need to separate real and imaginary parts of the result
        self.reals = [mp.Array("d", range(0, int(n**2))), mp.Array("d", range(0, int(n**2)))]
        self.imags = [mp.Array("d", range(0, int(n**2))), mp.Array("d", range(0, int(n**2)))]
        # List with each of the processes, to keep track of them
        self.processes = \
                [mp.Process(target=multi, args=(H, self.options["n_max"], phi_0, *A_x),
                    kwargs={"queue":self.queues[0], "real":self.reals[0], "imag":self.imags[0]}),
                 mp.Process(target=multi, args=(H, self.options["n_max"], phi_0, *A_y),
                    kwargs={"queue":self.queues[1], "real":self.reals[1], "imag":self.imags[1]})]
        # Begin monitoring
        if monitor:
            self.monitor_process(*args)
        return A_x, A_y

    def update_function(self, *args):
        pass

    def monitor_process(self, *args):
        # TODO: Aconsegueix-ne les fases ajustades
        for p in self.processes:
            p.start()
            p.join(timeout=0)
        alive = any([p.is_alive() for p in self.processes])
        while alive:
            for i, p in enumerate(self.processes):
                full = True
                while full:
                    try:
                        data = self.queues[i].get_nowait()
                        self.mse[i].append(data)
                    except:
                        full = False
            alive = any([p.is_alive() for p in self.processes])
            # Update through an update function if necessary
            self.update_function(*args)
    
    def get_phases(self):
        """Convert the multiprocessing arrays into the 2D phase distributions."""
        dim = self.options["dim"]
        exphi_x = (np.asarray(self.reals[0])+1j*np.asarray(self.imags[0])).reshape((dim, dim))
        exphi_y = (np.asarray(self.reals[1])+1j*np.asarray(self.imags[1])).reshape((dim, dim))
        # Now, impose the phase difference as obtained experimentally through the Stokes parameters
        stokes = self.get_stokes()
        delta = np.arctan2(stokes[3], stokes[2])
        # The phase origin will correspond to the value of the phase where the maximum of irradiance lies
        origin = self.options["origin"]
        delta_0 = delta[origin[0], origin[1]]
        e_delta_0 = np.exp(1j*delta_0)

        exphi_x /= exphi_x[origin[0], origin[1]]
        exphi_y /= exphi_y[origin[0], origin[1]]
        exphi_y *= e_delta_0
        return exphi_x, exphi_y

    def get_stokes(self):
        irradiances = [self.cropped[0][pol] for pol in range(6)]
        return get_stokes_parameters(irradiances)

    def config(self, **options):
        #def config(self, pixel_size=None, dim=256, n_max=200, eps=0.01, radius=None, origin=None):
        for option in options:
            # If the option is in the list, we change it...
            if option in self.options:
                self.options[option] = options[option]
                if option == "path":
                    self.load_dataset(options[option])
                elif option == "rect":
                    rect = options[option]
                    try:
                        shape = self.irradiance.shape
                    except:
                        raise ValueError("Dataset must be loaded before defining a window!")
                    top, bottom = bound_rect_to_im(shape, rect)
                    self.options[option] = [top, bottom]
                    # Finally, recompute the cropped images!
                    self._crop_images(top, bottom)
            # Else, we raise an exception
            else:
                raise KeyError(f"Option {option} does not exist.")

class PhaseRetriever(SinglePhaseRetriever):
    # TODO: Deriva un recuperador de fase que utilitzi multiprocessing per a recuperar dues
    # fases a la vegada.
    def __init__(sef, *args, **kwargs):
        super().__init__(*args, **kwargs)
