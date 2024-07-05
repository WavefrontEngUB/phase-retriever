import numpy as np
from scipy.fft import fft2, ifft2, fftshift, ifftshift
import multiprocessing as mp
import imageio

from .algorithm import multi
from .misc.radial import get_function_radius
from .misc.file_selector import get_polarimetric_names, get_polarimetric_npz
from .misc.central_region import find_rect_region
from .misc.stokes import get_stokes_parameters


fft = lambda field: fftshift(fft2(ifftshift(field)))
ifft = lambda spectr: ifftshift(ifft2(fftshift(spectr)))

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
        a_ft = fft(A)
        a_ft *= mask
        a_filt = ifft(a_ft)
        filtered.append(a_filt)
    return filtered

class SinglePhaseRetriever():
    # TODO: Crea una classe que encapsuli completament el metode de recuperacio de fase
    def __init__(self, n_max=200, mode='vectorial'):
        self.options = {"pixel_size": None,  # MUST BE SCALED ACCORDING TO THE WAVELENGTH
                        "dim": 256,
                        "rect": None,
                        "n_max": n_max,
                        "eps": 0.01,
                        "bandwidth": None,
                        "origin": None,
                        "lamb": None,
                        "path": None,
                        "ext": "png",  # Extension of the images (it can also be npy)
                        "mode": None   # vectorial or scalar
                        }
        self.irradiance = None
        self.images = {}
        self.cropped = {}
        self.cropped_irradiance = None
        self.a_ft = None
        self.mse = [[], []]

        self.options["n_max"] = n_max          # Maximum number of iterations
        self.options["mode"] = mode            # vectorial or scalar

        self.alpha = None
        self.beta = None
        self.gamma = None
        self.fields = {}  # Dictionary with the retrieved complex fields (Ex, Ey, Ez)

    def get(self, key):
        return self.options[key]

    def __getitem__(self, key):
        return self.options[key]

    def __setitem__(self, key, value):
        # TODO: Check types correctly
        self.config(**{key:value})

    def load_dataset(self, path=None, ftype="png"):
        self.irradiance = None
        self.images = {}
        # If the user does not input a path
        if not path:
            # If there is no path already inputted
            if not self.get("path"):
                raise ValueError("Dataset path must be specified")
            else:
                path = self.get("path")
        else:
            self.options["path"] = path
            self.options["ext"] = ftype

        self.polarimetric_sets = get_polarimetric_names(path, ftype=ftype)
        if not self.polarimetric_sets:
            raise ValueError(f"Cannot load polarimetric images from {path}")

        # Load all images into memory
        for z in self.polarimetric_sets:
            self.images[z] = {}
            for polarization in self.polarimetric_sets[z]:
                if type(polarization) != int:
                    continue
                path = self.polarimetric_sets[z][polarization]
                if ftype == "npy":
                    image = np.load(path)
                else:
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

    def get_images(self, z_idx=None, crop=True):
        imgs = self.images if not crop else self.cropped
        zetes = list(imgs.keys())
        z_idx = z_idx if z_idx is not None else 0
        return list(imgs[zetes[z_idx]].values())

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
        top, bottom = find_rect_region(self.irradiance, self.get("dim"))

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
            self._crop_images(*self.get("rect"))
        ft = fft(self.cropped_irradiance)
        self.a_ft = a_ft = np.real(np.conj(ft)*ft)

    def compute_bandwidth(self, tol=1e-4):
        if not self.cropped:
            self._crop_images(*self.get("rect"))
        # Compute the Fourier Transform of the cropped irradiance to get its bandwidth
        self._compute_spectrum()
        r = get_function_radius(self.a_ft, tol=tol)/2
        # if not r:
        #     raise ValueError("Could not estimate the Bandwidth of the beam")
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
            I_x = self.cropped[z][2] if self.options["mode"] == "vectorial" else None
            I_y = self.cropped[z][0]
            # Filtering the irradiances to remove high frequency noise fluctuations
            A_xfilt = np.real(np.sqrt(lowpass_filter(bw*2, I_x)[0])) if self.options["mode"] == "vectorial" else None
            A_yfilt = np.real(np.sqrt(lowpass_filter(bw*2, I_y)[0]))
            A_x.append(A_xfilt) #if self.options["mode"] == "vectorial" else None
            A_y.append(A_yfilt)
        # Then, we need to compute the free space transfer function H
        n = self.options["dim"]
        ny, nx = np.mgrid[-n//2:n//2, -n//2:n//2]
        bandwidth_mask = (ny*ny+nx*nx < bw*bw)
        umax = .5/p_size
        self.alpha = x = nx/nx.max()*umax
        self.beta = y = ny/ny.max()*umax
        rho2 = x*x+y*y
        gamma = np.zeros((n, n), dtype=np.float_)
        np.sqrt(1-rho2, out=gamma, where=bandwidth_mask)
        self.gamma = gamma
        zetes = list(self.images.keys())
        dz = (zetes[1]-zetes[0])/lamb
        H = np.exp(2j*np.pi*gamma*dz)
        # Get the bandwidth of the beam we are computing and remove all values of H lying outside this region.
        H[:] = fftshift(H*bandwidth_mask)
        # Finally, we create an initial guess for the phase of both components
        #phi_0 = np.zeros((n, n))
        phi_0 = np.random.rand(n, n)
        #phi_0 = np.arctan2(x, y)

        # We set up the multiprocessing environment. Just two processes, as we have two phases to recover
        self.queues = [mp.Queue(), mp.Queue()]
        p1, c1 = mp.Pipe()
        p2, c2 = mp.Pipe()
        # As queues only work with base types, we need to separate real and imaginary parts of the result
        self.reals = [mp.Array("d", range(0, int(n**2))), mp.Array("d", range(0, int(n**2)))]
        self.imags = [mp.Array("d", range(0, int(n**2))), mp.Array("d", range(0, int(n**2)))]
        # List with each of the processes, to keep track of them
        eps = self.get("eps")
        self.processes = \
                [mp.Process(target=multi, args=(H, self.options["n_max"], phi_0, *A_x),
                    kwargs={"queue": self.queues[0], "eps": eps,
                            "real": self.reals[0], "imag": self.imags[0]})
                 if self.options["mode"] == "vectorial" else None,
                 mp.Process(target=multi, args=(H, self.options["n_max"], phi_0, *A_y),
                    kwargs={"queue": self.queues[1], "eps": eps,
                            "real": self.reals[1], "imag": self.imags[1]})]
        # Begin monitoring
        if monitor:
            self.monitor_process(*args)

        return A_x, A_y

    def update_function(self, *args):
        pass

    def monitor_process(self, *args):
        # TODO: Aconsegueix-ne les fases ajustades
        for p in self.processes:
            if p is None:
                continue
            p.start()
            p.join(timeout=0)
        alive = any([p.is_alive() for p in self.processes if p is not None])
        while alive:
            for i, p in enumerate(self.processes):
                full = True
                while full:
                    try:
                        data = self.queues[i].get_nowait()
                        self.mse[i].append(data)
                    except:
                        full = False
            alive = any([p.is_alive() for p in self.processes if p is not None])
            # Update through an update function if necessary
            self.update_function(*args)
    
    def get_phases(self):
        """Convert the multiprocessing arrays into the 2D phase distributions."""
        dim = self.options["dim"]
        if self.options['mode'] == 'vectorial':
            exphi_x = (np.asarray(self.reals[0])+1j*np.asarray(self.imags[0])).reshape((dim, dim))
            exphi_y = (np.asarray(self.reals[1])+1j*np.asarray(self.imags[1])).reshape((dim, dim))
            # Now, impose the phase difference as obtained experimentally through the Stokes parameters
            stokes = self.get_stokes()
            delta = np.arctan2(stokes[3], stokes[2])
            # The phase origin will correspond to the value of the phase where the maximum of irradiance lies
            origin = self.options["origin"]
            delta_0 = delta[origin[0], origin[1]]
            e_delta_0 = np.exp(-1j*delta_0) # -1j Seems to be THE RIGHT WAY(TM) to do it

            exphi_x /= exphi_x[origin[0], origin[1]]
            exphi_y /= exphi_y[origin[0], origin[1]]
            exphi_y *= e_delta_0
            return exphi_x, exphi_y
        else:
            return ((np.asarray(self.reals[1])+1j*np.asarray(self.imags[1])).reshape((dim, dim)),
                    (np.asarray(self.reals[1])+1j*np.asarray(self.imags[1])).reshape((dim, dim)))

    def set_fields(self, zeroFill=True):
        """ Set the retrieved fileds in the object dictionary."""
        exphi_x, exphi_y = self.get_phases()  # if scalar, just the first (x) is not None
        if self.options["mode"] == "vectorial":
            ex = self.A_x[0] * np.exp(1j*exphi_x)
            ey = self.A_y[0] * np.exp(1j*exphi_y)
        else:
            ex = self.A_y[0] * np.exp(1j*exphi_x)
            ey = np.zeros_like(ex, dtype=np.complex_) if zeroFill else None

        self.fields.update(Ex=ex, Ey=ey)

        Ex_fft = fft(ex)
        Ey_fft = fft(ey)
        Ez_fft = (self.alpha * Ex_fft + self.beta * Ey_fft) / (self.gamma + 1e-16)

        self.fields.update(Ez=ifft(Ez_fft))


    def get_fields(self):
        """Return the complex field at a given distance z."""
        if not self.fields:
            raise ValueError("Field not retrieved, yet!")

        return self.fields['Ex'], self.fields['Ey'], self.fields['Ez']


            # Ey = self.fields['Ey']
            # Ez = self.fields['Ez']
    #
    #     else:
    #         Ex_fft = fft(self.fields['Ex'])
    #         Ey_fft = fft(self.fields['Ey'])
    #         Ez_fft = fft(self.fields['Ey'])
    #
    #         H = np.exp(-2j * np.pi * self.gamma * z)
    #         H[slef.alpha * slef.alpha + slef.beta * slef.beta >= 1] = 0
    #         Ex_fft *= H
    #         Ey_fft *= H
    #         Ez_fft *= H
    #         Ex = ifft(Ex_fft)
    #         Ey = ifft(Ey_fft)
    #         Ez = ifft(Ez_fft)
    #
    #     return Ex, Ey, Ez
    #
    #
    # def get_trans_fields(self, z=0):
    #     """Return the transversal components of the field. """
    #     Ex, Ey, _ = self.get_fields(z, zeroFill)
    #     return Ex, Ey
    #
    # def get_long_component(self, z=0):
    #     """Return the longitudinal component of the field. """
    #     _, _, Ez = self.get_fields(z, zeroFill)
    #     return Ez

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
                    self.load_dataset(options[option], ftype=self.options["ext"])
                elif option == "rect":
                    rect = options[option]
                    try:
                        shape = self.irradiance.shape
                    except:
                        raise ValueError("Dataset must be loaded before defining a window!")
                    top, bottom = rect # if rect is passed, nothing else is needed
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
