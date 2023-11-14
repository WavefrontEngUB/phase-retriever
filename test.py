from phase_retriever import PhaseRetriever
from scipy.fft import fft2, ifft2, fftshift, ifftshift
import numpy as np
import matplotlib.pyplot as plt
OK = "\033[0;32mOK\033[0;0m"
FAIL = "\033[91mFAIL\033[0;0m"

def get_Ez(Ex, Ey, pixel_size, lamb):
    ny, nx = Ex.shape
    y, x = np.mgrid[-ny//2:ny//2, -nx//2:nx//2]
    # Cosinus directors
    umax = .5/pixel_size*lamb
    alpha = x/x.max()*umax
    beta = y/y.max()*umax
    gamma = np.zeros((ny, nx), dtype=np.float64)
    rho2 = alpha*alpha+beta*beta
    np.sqrt(1-rho2, where=rho2 < 1, out=gamma)

    # Càlcul del camp per se
    ft_Ex = fftshift(fft2(ifftshift(Ex)))
    ft_Ey = fftshift(fft2(ifftshift(Ey)))
    ft_Ez = alpha*ft_Ex+beta*ft_Ey
    ft_Ez[gamma>0] /= gamma[gamma>0]

    Ez = fftshift(ifft2(ifftshift(ft_Ez)))
    return Ez

def test_basics():
    success = True
    retriever = PhaseRetriever()
    pixel_size = 0.0469
    lamb = 0.52
    M = 1
    p_eff = pixel_size/M/lamb

    # Load dataset
    print("Dataset load... ", end="")
    try:
        retriever.load_dataset("sims")
        print(OK)
    except:
        print(FAIL)

    print("Pixel size set... ", end="")
    try:
        retriever.config(pixel_size=pixel_size)
        retriever.config(lamb=lamb)
        if retriever.options["pixel_size"] != pixel_size:
            raise ValueError()
        print(OK)
    except:
        print(FAIL, f"Expected {0.1} and got{retriever.config[pixel_size]}")

    print("Wavelength set... ", end="")
    try:
        retriever.config(lamb=lamb)
        if retriever.options["pixel_size"] != pixel_size:
            raise ValueError()
        print(OK)
    except:
        print(FAIL, f"Expected {0.1} and got{retriever.config[pixel_size]}")

    print("Window centering... ", end="")
    try:
        retriever.center_window()
        print(OK)
    except:
        print(FAIL)

    print("Phase origin selection... ", end="")
    try:
        retriever.select_phase_origin()
        print(OK)
    except:
        print(FAIL)

    print("Bandiwdth determination... ", end="")
    try:
        retriever.compute_bandwidth(tol=4e-6)
        print(OK)
    except:
        print(FAIL)
    for option in retriever.options:
        print(option, retriever.options[option])

    Ax, Ay = retriever.retrieve()
    print(len(retriever.mse[0]))

    ephi_x, ephi_y = retriever.get_phases()

    Ez = get_Ez(Ax[0]*ephi_x, Ay[0]*ephi_y, pixel_size, lamb)

    data = np.load("sims_retrieved/phases.npz")
    data_A = np.load("sims_retrieved/amplitudes.npz")
    Ez_gui = get_Ez(data["phi_x"]*data_A["Ax"], data["phi_y"]*data_A["Ay"], pixel_size, lamb)
    cmap = "twilight_shifted"
    fig, ax = plt.subplots(2, 3, constrained_layout=True)
    ax[0, 1].imshow(np.angle(ephi_x), cmap=cmap, interpolation="nearest")
    ax[0, 2].imshow(np.angle(data["phi_x"]), cmap=cmap, interpolation="nearest")
    ax[1, 1].imshow(np.angle(ephi_y), cmap=cmap, interpolation="nearest")
    ax[1, 2].imshow(np.angle(data["phi_y"]), cmap=cmap, interpolation="nearest")

    ax[0, 0].imshow(Ax[0], cmap="gray")
    ax[1, 0].imshow(Ay[0], cmap="gray")

    ax[0, 1].set_title("This program")
    ax[0, 2].set_title("GUI result")

    fig2, ax2 = plt.subplots(1, 2, constrained_layout=True)
    ax2[0].imshow(np.real(np.conj(Ez_gui)*Ez_gui), cmap="gray")
    ax2[1].imshow(np.real(np.conj(Ez)*Ez), cmap="gray")
    ax2[0].set_title("E_z GUI")
    ax2[1].set_title("E_z this program")

    fig3, ax3 = plt.subplots(1, 2, constrained_layout=True)
    msx, msy = retriever.mse
    ax3[0].plot(msx)
    ax3[1].plot(msy)

    plt.show()

    return success

if __name__ == "__main__":
    test_basics()
