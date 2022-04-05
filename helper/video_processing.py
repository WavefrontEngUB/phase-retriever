#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import numpy as np
import imageio
import subprocess
from scipy.fft import fft2, ifft2, fftshift, set_workers
import matplotlib.pyplot as plt
import os

def propaga_video(Ux, Uy, y, x, circ, carpeta, nim=100, delta_z=40,
        Izmax=None, lamb=520e-6, queue=None, video=False, fps=8):
    """Propagate the complex amplitudes a distance delta_z by takin
    nim steps. REQUIRES ffmpeg to properly save the videos.
    """
    zetes = np.linspace(0, delta_z, nim)*lamb
    x = fftshift(x)
    y = fftshift(y)
    circ = fftshift(circ)
    rho2 = x*x+y*y
    Asx = fft2(Ux)*circ
    Asy = fft2(Uy)*circ
    maxIz = np.zeros(nim)
    maxIt = np.zeros(nim)
    # We assume non paraxiality, therefore we need to determine wz = kz/2pi
    over_l = 1/lamb
    wz = np.sqrt(np.complex_(1/lamb/lamb-rho2))
    # Writers for the videos
    if video:
        it_writer = imageio.get_writer(os.path.join(carpeta, "v_intensity.mp4"), fps=fps)
        iz_writer = imageio.get_writer(os.path.join(carpeta, "v_long.mp4"), fps=fps)
        phi_x_writer = imageio.get_writer(os.path.join(carpeta, "v_phase_x.mp4"), fps=fps)
        phi_y_writer = imageio.get_writer(os.path.join(carpeta, "v_phase_y.mp4"), fps=fps)
    print("Generating images...")
    for i, z in enumerate(zetes):
        H = np.exp(2j*np.pi*z*wz)
        with set_workers(4):
            Uzx = ifft2(H*Asx)
            Uzy = ifft2(H*Asy)
            Uzz = ifft2((Asx*x + Asy*y)*H/wz)

        # Irradiances and phases
        Iz = np.real(np.conj(Uzx)*Uzx)+np.real(np.conj(Uzy)*Uzy)
        Izz = np.real(np.conj(Uzz)*Uzz)
        It = Iz+Izz # Intensitat total
        phi_x = np.uint8(np.angle(Uzx)%2*np.pi*255/(2*np.pi))
        phi_y = np.uint8(np.angle(Uzy)%2*np.pi*255/(2*np.pi))

        # Gravem els vídeos
        if video:
            it_writer.append_data(It)
            iz_writer.append_data(Iz)
            phi_x_writer.append(phi_x)
            phi_x_writer.append(phi_y)
        # Desem imatges
        maxIz[i] = Izz.max()    # Desa-ho TAL QUAL!!!
        maxIt[i] = It.max()
        imageio.imsave(f"{carpeta}/{i:03}.png", np.uint16(It))
        imageio.imsave(f"{carpeta}/phi_x_{i:03}.png", 
                phi_x)
        imageio.imsave(f"{carpeta}/phi_y_{i:03}.png", 
                phi_y)
        if not Izmax:
            imageio.imsave(f"{carpeta}/long_{i:03}.png", 
                    np.uint16(Izz))
        else:
            imageio.imsave(f"{carpeta}/long_{i:03}.png", 
                    np.uint16(Izz))

        # Finalment, actualitzem la cua si n'hi hagués
        if queue:
            queue.put_nowait(i)
    np.savetxt(f"{carpeta}/z_max.txt", maxIz)
    np.savetxt(f"{carpeta}/t_max.txt", maxIt)

    if video:
        it_writer.close()
        iz_writer.close()
        phi_x_writer.close()
        phi_x_writer.close()
    # Grava el video
    """
    print("Saving intensity...")
    subprocess.call([
        "ffmpeg", "-y", "-framerate", "8", "-i", f"{carpeta}/%03d.png", "-c:v", "libx264rgb",
        f"{carpeta}/v_intensity.mp4"])
    print("Saving longitudinal component...")
    subprocess.call([
        "ffmpeg", "-y", "-framerate", "8", "-i", f"{carpeta}/long_%03d.png", "-c:v", "libx264rgb",
        f"{carpeta}/v_long.mp4"])
    print("Saving phase...")
    subprocess.call([
        "ffmpeg", "-y", "-framerate", "8", "-i", f"{carpeta}/phi_x_%03d.png", "-c:v", "libx264rgb",
        f"{carpeta}/v_phase_x.mp4"])
    subprocess.call([
        "ffmpeg", "-y", "-framerate", "8", "-i", f"{carpeta}/phi_y_%03d.png", "-c:v", "libx264rgb",
        f"{carpeta}/v_phase_y.mp4"])
    """
