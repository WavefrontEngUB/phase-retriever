#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import matplotlib.pyplot as plt
fft2 = np.fft.fft2
ifft2 = np.fft.ifft2
fftshift = np.fft.fftshift

def multi(H, niter, phi0, *As, verbose=False, queue=None, real=None, imag=None):
    """Multipass phase retrieval. Estimates the phase that best approximates
    the experimental moduli obtained in propagation. The method assumes
    plane wave spectrum propagation, with its benefits and limitations.
    Moreover, we assume that the planes where the moduli are equidistant.
    
    Parameters:
        - H: Free space transfer function between two planes.
        - niter: Number of iterations for the algorithm
        - phi0: Initial guess for the phase
        - *As: Moduli of the complex amplitudes taken each at a distance z
        from each other. The minimum number for the algorithm to work is 2.
        - verbose: Print status of the phase retrieval at each iteration.
    Output:
        - phi: Estimation of the phase that best approximates the specified
        propagation.
        - MSE: Mean squared errors at each iteration
        - alpha: Values of the acceleration parameters at each iteration
    """
    ny, nx = As[0].shape
    xk = np.zeros((ny, nx), dtype=np.complex_)
    yk = np.zeros_like(xk)
    g_k1 = np.zeros_like(xk)
    g_k2 = np.zeros_like(xk)
    hk = np.zeros_like(xk)
    H_back = np.conj(H)**(len(As)-1)   # Back propagation from the final plane
    alphes = np.zeros(niter)
    mses = np.zeros(niter)
    Ui = np.zeros(As[0].shape, dtype=np.complex_)

    k = 1/np.sum(As[0]**2)
    yk[:] = np.exp(1j*phi0)
    for i in range(niter):

        g_k2[:] = g_k1[:]
        g_k1[:] = yk    # Saving yk for next step
        hk[:] = xk
        # --- Calculation of psi(yk)
        # Forward
        for Ai in As[:-1]:
            Ui[:] = Ai*yk
            Ui[:] = ifft2(fft2(Ui)*H)
            yk[:] = Ui/(abs(Ui)+1e-16)  # Recover only the complex phase

        # Backward
        Ui[:] = As[-1]*yk
        Ui[:] = fft2(Ui)
        Ui[:] = ifft2(Ui*H_back)
        yk[:] = Ui/(abs(Ui)+1e-16)

        # --- 

        g_k1[:] = yk-g_k1   # g_k1 = psi(y_k)-y_k
        xk[:] = yk[:]
        hk[:] = xk-hk
        # Calculating the acceleration factor
        alpha = np.sum(np.conj(g_k1)*g_k2)/(np.sum(np.conj(g_k2)*g_k2)+1e-16)
        #alpha = np.sqrt(np.sum(g_k1*g_k1)/(np.sum(g_k2*g_k2)+1e-16))
        alpha = min(max(0, np.real(alpha)), 1)   # 0 < alpha < 1
        alphes[i] = alpha
        # Acceleration method, new point estimation
        yk[:] = xk+alpha*hk

        mse = np.sum((abs(Ui)-As[0])**2)*k
        mses[i] = mse
        if verbose:
            print(f"alpha = {alpha:8.3g}\tMSE = {mse:8.4g}")
        if queue:
            queue.put(mse)
    if queue:
        n = nx*ny
        rk = xk.real.flatten()
        ik = xk.imag.flatten()
        for i in range(n):
            real[i] = rk[i]
            imag[i] = ik[i]
    if not queue:
        return xk, mses, alphes
