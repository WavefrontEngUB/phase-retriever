import numpy as np
from scipy.fft import fftshift, ifftshift, fft2, ifft2, set_workers
import multiprocessing as mp

sfft2 = lambda field: fftshift(fft2(ifftshift(field)))
sifft2 = lambda spectr: ifftshift(ifft2(fftshift(spectr)))

workers = mp.cpu_count()

class FocalPropagator():
    properties = {
            "Ex"            : None, 
            "Ey"            : None,
            "Ez"            : None,
            "pixel_size"    : None,
            }

    def __init__(self, Ex=None, Ey=None, wz=None):

        if (isinstance(Ex, np.ndarray) and isinstance(Ey, np.ndarray)):
            self.set_fields(Ex, Ey, wz)

    def __setitem__(self, item, value):
        if item == "Ex" or item == "Ey" or item == "Ez":
            if not isinstance(value, np.ndarray):
                raise ValueError(f"{item} must be ndarray")
        elif item == "pixel_size":
            if (type(value) is not float) and (type(value) is not int):
                raise ValueError(f"{item} must be float")
        self.properties[item] = value

    def __getitem__(self, item):
        return self.properties[item]

    def propagate_to(self, z):
        if (isinstance(self.Ex, np.ndarray) and isinstance(self.Ey, np.ndarray)
                and isinstance(self.Ez, np.ndarray)):
            phase = 2j*np.pi*z*self.wz
            if z < 0:
                mask = np.real(phase) < 0
                phase[mask] = -phase[mask]
            H = np.exp(phase)
            with set_workers(6):
                Ex = sifft2(H*self.Ax)
                Ey = sifft2(H*self.Ay)
                Ez = sifft2(H*self.Az)
            I = np.real(np.conj(Ex)*Ex)+\
                np.real(np.conj(Ey)*Ey)
            I[:] /= self.Imax
            return I

    def propagate_field_to(self, z):
        if (isinstance(self["Ex"], np.ndarray) and isinstance(self["Ey"], np.ndarray)
                and isinstance(self["Ez"], np.ndarray)):
            phase = 2j*np.pi*z*self.wz
            if z < 0:
                mask = np.real(phase) < 0
                phase[mask] = -phase[mask]
            H = np.exp(phase)

            with set_workers(6):
                Ex = sifft2(H*self.Ax)
                Ey = sifft2(H*self.Ay)
                Ez = sifft2(H*self.Az)
            return Ex, Ey, Ez
        else:
            raise Exception("Field not ready to be propagated")

    def set_fields(self, Ex, Ey, wz=None):
        self.Ex, self.Ey = Ex, Ey
        with set_workers(4):
            self.Ax = sfft2(Ex)
            self.Ay = sfft2(Ey)

        self.wz = np.copy(wz) if wz else self.wz
        self.wz[:] = fftshift(wz)
        I = np.real(np.conj(self.Ex)*self.Ex)+\
            np.real(np.conj(self.Ey)*self.Ey)
        # Maximum intensity so as to normalize the output values
        self.Imax = I.max()

    def create_gamma(self):
        # p_size in terms of wavelength
        p_size = self["pixel_size"]
        Ex, Ey = self["Ex"], self["Ey"]

        if p_size is None:
            raise ValueError("p_size must be specified")
        if not isinstance(Ex, np.ndarray) and not isinstance(Ey, np.ndarray):
            raise ValueError("Ex, Ey must be specified")
        ny, nx = Ex.shape
        y, x = np.mgrid[-ny//2:ny//2, -nx//2:nx//2]
        umax = .5 / p_size
        alpha = x/x.max()*umax
        beta = -y/y.max()*umax
        
        theta2 = alpha*alpha + beta*beta
        self.wz = np.zeros((ny, nx), dtype=np.float64)
        np.sqrt(1-theta2, where=theta2 < 1, out=self.wz)

        self.Az = (alpha * self.Ax + beta * self.Ay)
        self.Az[self.wz > 0] /= (self.wz[self.wz > 0] + 1e-16)
        self['Ez'] = sifft2(self.Az)

    def create_spectra(self):
        Ex, Ey = self["Ex"], self["Ey"]
        if not isinstance(Ex, np.ndarray) and not isinstance(Ey, np.ndarray):
            raise ValueError("Ex, Ey must be specified")
        # Compute irradiance
        I = np.real(np.conj(Ex)*Ex)+\
            np.real(np.conj(Ey)*Ey)
        # Maximum intensity so as to normalize the output values
        self.Imax = I.max()

        # Compute the spectra
        with set_workers(4):
            self.Ax = sfft2(Ex)
            self.Ay = sfft2(Ey)

