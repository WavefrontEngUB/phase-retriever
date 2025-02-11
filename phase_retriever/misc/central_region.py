import numpy as np
from scipy.fft import fft2, ifft2, fftshift, ifftshift

def find_rect_region(array: np.ndarray , dim: int):
    """Find the place where a rectangle of size dim X dim best encapsulates the
    region with most energy inside array."""
    try:
        ny, nx = array.shape
    except:
        raise ValueError("Input array must be 2D")
    # Create an array with a centered rectangle
    rect = np.zeros((ny, nx), dtype=np.complex128)
    rect[(ny-dim//2)//2:(ny+dim//2)//2,
         (nx-dim//2)//2:(nx+dim//2)//2] = 1
    loc = cross_correlation(array, rect)
    return center2rect(loc, dim, nx)


def cross_correlation(array, reff):
    # Transform both arrays and multiply
    ft_array = fftshift(fft2(ifftshift(array)))
    ft_rect = fftshift(fft2(ifftshift(reff)))
    ft_convo = ft_rect * ft_array
    # Inverse transform and find its maximum value
    convo = fftshift(ifft2(ifftshift(ft_convo)))
    aconvo = np.real(np.conj(convo) * convo)
    yloc, xloc = np.where(aconvo == aconvo.max())
    loc = (yloc[0], xloc[0])
    return loc

def cross_correlation2(array, reff):
    # Transform both arrays and multiply
    ft_array = fftshift(fft2(ifftshift(array)))
    ft_reff = fftshift(fft2(ifftshift(reff)))
    ft_convo =  ft_array * np.conj(ft_reff)
    # Inverse transform and find its maximum value
    convo = (ifft2(ifftshift(ft_convo)))
    aconvo = np.real(np.conj(convo) * convo)

    yloc, xloc = np.where(aconvo == aconvo.max())
    loc = (-yloc[0], -xloc[0])
    return loc



def center2rect(loc, win_size, nx):
    # With the center of the rectangle known, we return its left topmost coordinates
    # alongside its right bottommost (?) coordinates.
    x0 = loc[1] - win_size // 2
    x1 = loc[1] + win_size // 2
    if x0 < 0:
        x0 = 0
        x1 = win_size
    elif x1 >= nx:
        x1 = nx
        x0 = nx - win_size
    y0 = loc[0] - win_size // 2
    y1 = loc[0] + win_size // 2
    if y0 < 0:
        y0 = 0
        y1 = win_size
    elif y1 >= nx:
        y1 = nx
        y0 = nx - win_size
    return (y0, x0), (y1, x1)


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    n = 1024
    dim = 256
    sigma = 16

    ny, nx = np.mgrid[-n//2:n//2, -n//2:n//2]
    rho2 = nx*nx+ny*ny
    rho = np.sqrt(rho2)
    func = rho*rho/sigma*np.exp(-rho2*.5/(sigma*sigma))
    plt.imshow(func); plt.show()
    
    print(find_rect_region(func, dim))
