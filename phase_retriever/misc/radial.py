import numpy as np

def get_function_radius(array, tol=1e-4):
    """
    Get a first estimation of the radius of the function defined in array.
    To do so, we assume functions with radial symmetry and check whether
    there exist some value smaller than V = array.max()*tol. If it
    exists, we return the distance from that point to the origin. If not,
    the function returns None.
    """
    vmax = array.max()*tol
    # FIXME: We just do a quick check by collapsing to a single dimension the array...
    try:
        ny, nx = array.shape
    except:
        raise ValueError("Input array must be 2D.")

    if ny > nx:
        sg_array = np.mean(array, axis=0)
        r0 = ny//2
    else:
        sg_array = np.mean(array, axis=-1)
        r0 = nx//2

    mask = sg_array > vmax
    radius = np.argwhere(mask)[0]
    
    if radius:
        return abs(radius[0]-r0)
    else:
        print("No radius found")
        return 0

if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle
    n = 512
    ny, nx = np.mgrid[-n//2:n//2, -n//2:n//2]
    phi = np.arctan2(ny, nx)

    sigma = 32
    m = 8
    fun = np.exp(-(ny*ny+nx*nx)*.5/sigma**2)*np.sin(5*phi)
    fun *= fun

    r = get_function_radius(fun)
    print(f"Expected: True  === Got: {True if r else False}")
    fig, ax = plt.subplots()
    plt.imshow(fun, cmap="gray")
    circ = Circle((n//2, n//2), r, alpha=0.2)
    ax.add_patch(circ)

    sigma = 256
    fun = np.exp(-(ny*ny+nx*nx)*.5/sigma**2)

    r = get_function_radius(fun)
    print(f"Expected: False === Got: {True if r else False}")

    plt.show()
