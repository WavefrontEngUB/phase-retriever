import numpy as np
from scipy.fft import fftshift, ifftshift, fft2, ifft2, set_workers
import multiprocessing as mp
workers = mp.cpu_count()

class FocalPropagator():
    def __init__(self, Ex=None, Ey=None, wz=None):

        if (isinstance(Ex, np.ndarray) and isinstance(Ey, np.ndarray)):
            self.set_fields(Ex, Ey, wz)

    def propagate_to(self, z):
        if (isinstance(self.Ex, np.ndarray) and isinstance(self.Ey, np.ndarray)):
            phase = 2j*np.pi*z*self.wz
            if z < 0:
                mask = np.real(phase) < 0
                phase[mask] = -phase[mask]
            H = np.exp(phase)
            with set_workers(4):
                Ex = ifft2(H*self.Ax)
                Ey = ifft2(H*self.Ay)
            I = np.real(np.conj(Ex)*Ex)+\
                np.real(np.conj(Ey)*Ey)
            I[:] /= self.Imax
            return I

    def set_fields(self, Ex, Ey, wz):
        self.Ex, self.Ey = Ex, Ey
        with set_workers(4):
            self.Ax = fft2(Ex)
            self.Ay = fft2(Ey)
        self.wz = np.copy(wz)
        self.wz[:] = fftshift(wz)
        I = np.real(np.conj(self.Ex)*self.Ex)+\
            np.real(np.conj(self.Ey)*self.Ey)
        # Maximum intensity so as to normalize the output values
        self.Imax = I.max()
