import numpy as np

def get_stokes_parameters(I):
    """Get the stokes parameters from the irradiances I."""
    S0 = 0
    for i in range(6):
        S0 += I[i]
    S0 /= 3
    # FIXME: Check whether this defs. are right. 0 - Y, 90 - X.
    S1 = I[2]-I[0]   # horizontal - vertical
    S2 = I[3]-I[1]   # P_45 - P_135
    S3 = I[5]-I[4]   # Dextro - Levo

    return S0, S1, S2, S3
