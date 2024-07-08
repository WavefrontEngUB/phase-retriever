#!/usr/bin/python3
import numpy as np
import imageio
from scipy.fft import fft2, ifft2, fftshift
from file_selector import get_polarimetric_names

class Recenterer:
    def __init__(self, path, ref=None):
        self.ref = reference
        self.path = path

        self.polarimetric_sets, beam_name = get_polarimetric_names(path)
        self.keys = self.polarimetric_sets

    def select_reference(self, ref_number, bandwidth=.22):
        # First, we load the polarimetric image that will work as our reference
        try:
            reference_path = self.polarimetric_sets[0][ref_number]
            self.ref_number = ref_number
        except:
            raise ValueError(f"Reference number {ref_number} does not exist.")
        ref = imageio.imread(reference_path)
        self.ak = fft2(ref)
        ny, nx = self.ref.shape

        # Construeixo també el filtre de freqüències per a determinar la posició promig de l'energia...
        nny, nnx = np.mgrid[-ny//2:ny//2, -nx//2:nx//2]
        y = nny/(ny/2)*.5
        x = nnx/(nx/2)*.5

        self.mask = (x*x+y*y) < (bandwidth**2)
        self.mask[:] = fftshift(self.mask)

    def recenter(self, image):
        imk = fft2(image)
        ny, nx = image.shape
        corr = fftshift(ifft2(imk*np.conj(self.ak)*self.mask))
        # Cerco la posició del màxim d'energia
        energy = np.real(np.conj(corr)*corr)
        pos = np.unravel_index(np.argmax(energy), image.shape)
        pos = np.asarray(pos, dtype=np.int_)
        pos[0] = ny//2-pos[0]
        pos[1] = nx//2-pos[1]
        print(f"\tDelta x: {pos[1]},\tDelta y = {pos[0]}")

        # Recentro finalment...
        im_rec = np.roll(image, pos, axis=(0, 1))
        return im_rec

    def recenter_series(self):
        for polset in self.polarimetric_sets:
            for i in self.polarimetric_sets[polset]:
                imname = self.polarimetric_sets[polset][i]
                # Do nothing if we are looking at the reference image
                if i == self.ref:
                    continue
                image = imageio.imread(imname)
                recentered = self.recenter(image)
                # Overwrite old images
                # TODO: Test code. In theory this does not destroy the images, as they
                # receive just a cyclical permutation and can always be restored to their
                # original positions.
                imageio.imsave(imname)
        return images

if __name__ == "__main__":
    main()
