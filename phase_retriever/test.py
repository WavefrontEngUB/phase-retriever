import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.fft import fft2, ifft2, fftshift, ifftshift

from phase_retriever import PhaseRetriever
from phase_retriever.misc.focalprop import FocalPropagator

OK = "\033[0;32mOK\033[0;0m"
FAIL = "\033[91mFAIL\033[0;0m"

def test_basics():
    n_errors = 0

    retriever = PhaseRetriever()
    pixel_size = 0.043
    lamb = 0.52

    # Load dataset
    print("Dataset load... ", end="")
    module_dir = os.path.dirname(__file__)
    test_data = os.path.join(module_dir, 'test_dataset')
    try:
        _ = retriever.load_dataset(test_data)
        print(OK)
    except:
        print(FAIL)
        n_errors += 1

    print("Pixel size set... ", end="")
    try:
        retriever.config(pixel_size=pixel_size)
        gotten = retriever.options["pixel_size"]
        assert gotten == pixel_size
        print(OK)
    except:
        print(FAIL, f"Expected {pixel_size} and got {gotten}")
        n_errors += 1

    print("Wavelength set... ", end="")

    try:
        retriever.config(lamb=lamb)
        gotten = retriever.options["lamb"]
        assert gotten == lamb
        print(OK)
    except:
        print(FAIL, f"Expected {lamb} and got {gotten}")
        n_errors += 1

    print("Window centering... ", end="")
    try:
        retriever.center_window()
        print(OK)
    except:
        print(FAIL)
        n_errors += 1

    print("Phase origin selection... ", end="")
    try:
        retriever.select_phase_origin()
        print(OK)
    except:
        print(FAIL)
        n_errors += 1

    print("Bandiwdth determination... ", end="")
    try:
        retriever.compute_bandwidth()
        print(OK)
    except:
        print(FAIL)
        n_errors += 1

    print("  All loaded options:  ")
    for option in retriever.options:
        print(option, retriever.options[option])

    Ax, Ay = retriever.retrieve()
    print("Number of iterations done:", len(retriever.mse[0]))

    propagator = FocalPropagator()
    Ex, Ey = retriever.get_trans_fields()
    propagator["Ex"] = Ex
    propagator["Ey"] = Ey
    propagator["pixel_size"] = pixel_size
    propagator.create_spectra()
    propagator.create_gamma()
    Ex, Ey, Ez = propagator.propagate_field_to(0)

    ground_t = np.load(os.path.join(test_data, "Sim_retrieved.npz"))
    Ex_gt, Ey_gt, Ez_gt = ground_t["Ex"], ground_t["Ey"], ground_t["Ez"]


    fig0, ax0 = plt.subplots(1, 2, constrained_layout=True)
    msx, msy = retriever.mse
    ax0[0].plot(msx)
    ax0[1].plot(msy)

    cmap = "twilight_shifted"
    fig, ax = plt.subplots(3, 4, constrained_layout=True)
    ax[0, 0].set_title("This test")
    ax[0, 1].set_title("Ground truth")
    ax[0, 2].set_title("This test")
    ax[0, 3].set_title("Ground truth")
    ax[0, 0].imshow(Ax[0], cmap="gray")
    ax[0, 1].imshow(np.abs(Ex_gt), cmap="gray")
    ax[1, 0].imshow(Ay[0], cmap="gray")
    ax[1, 1].imshow(np.abs(Ey_gt), cmap="gray")
    ax[2, 0].imshow(np.abs(Ez), cmap="gray")
    ax[2, 1].imshow(np.abs(Ez_gt), cmap="gray")
    ax[0, 2].imshow(np.angle(Ex), cmap=cmap, interpolation="nearest")
    ax[0, 3].imshow(np.angle(Ex_gt), cmap=cmap, interpolation="nearest")
    ax[1, 2].imshow(np.angle(Ey), cmap=cmap, interpolation="nearest")
    ax[1, 3].imshow(np.angle(Ey_gt), cmap=cmap, interpolation="nearest")
    ax[2, 2].imshow(np.angle(Ez), cmap=cmap, interpolation="nearest")
    ax[2, 3].imshow(np.angle(Ez_gt), cmap=cmap, interpolation="nearest")

    print(f"Errors found: {n_errors}")
    print("Compare results... ")

    plt.show()

    return n_errors

if __name__ == "__main__":
    test_basics()
