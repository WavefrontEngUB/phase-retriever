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
    rect = np.zeros((ny, nx), dtype=np.complex_)
    rect[(ny-dim//2)//2:(ny+dim//2)//2,
         (nx-dim//2)//2:(nx+dim//2)//2] = 1
    # Transform both arrays and multiply
    ft_array = fftshift(fft2(ifftshift(array)))
    ft_rect =  fftshift(fft2(ifftshift(rect)))
    ft_convo = ft_rect*ft_array
    # Inverse transform and find its maximum value
    convo = fftshift(ifft2(ifftshift(ft_convo)))
    aconvo = np.real(np.conj(convo)*convo)
    yloc, xloc = np.where(aconvo==aconvo.max())
    loc = (yloc[0], xloc[0])

    # With the center of the rectangle known, we return its left topmost coordinates
    # alongside its right bottommost (?) coordinates.
    x0 = loc[1]-dim//2
    x1 = loc[1]+dim//2
    if x0 < 0:
        x0 = 0
        x1 = dim
    elif x1 >= nx:
        x1 = nx
        x0 = nx-dim
    y0 = loc[0]-dim//2
    y1 = loc[0]+dim//2
    if y0 < 0:
        y0 = 0
        y1 = dim
    elif y1 >= nx:
        y1 = nx
        y0 = nx-dim

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
