#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FILE SELECTOR FOR POLARIMETRIC IMAGES
    A polarimetric image picker to return a filename-agnostic
set of properly corrected polarimetric images.
"""
import os
import numpy as np
import sys
import regex as re

WAVELENGTH_um = 0.514  # FIXME: wavelength in microns is hardcoded !!!!

def get_polarimetric_names(folder, pol_keys={0:"a0", 1:"a45", 2:"a90",
    3:"a135", 4:"aLev", 5:"aDex", 6:"aIrr"}, ftype="png"):
    """Return a set of dictionaries containing the set of polarimetric images
    for each family of measurements. Assumes a filename of the form

        {beam type}_{z location}_{polarimetric image}.{file type}

        Currently, accepts any prefix (inculing underscores) for the beam type,
        and the order of {z_location} and {polarimetric image} is not relevant.

        {z_location} must be of the form z{value}{units}, where {units} can be
        um, mm, nm, lam (microns), or empty (by default it is microns).

    (David's naming convention)
    """
    filenames = os.listdir(folder)
    filenames.sort()
    polarimetric_sets = {}
    pol_idx = None  # just an initialization
    z_idx = None  # just an initialization
    beam_name = ''
    for fname in filenames:
        # Try to get the fname and ftype. If not divisible, get out
        try:
            image_name, f_type = fname.split(".")
        except:
            continue
        # Recognize the filetype and bail out if not the correct one
        if f_type != ftype:
            continue
        # Retrieve the necessary information. If not possible, bail out
        try:
            fields = image_name.split("_")
        except:
            continue

        if fields[-1] == "retrieved":
            continue  # It probably will be an already retrieved file

        if len(fields) < 3:
            continue  # Not a valid filename!

        beam_name = fields[0]

        # Get the index for the analyzer field
        if pol_idx is None:  # just the first time
            for idx, field in enumerate(fields):
                if field in pol_keys.values():
                    pol_idx = idx
                    break

        # Get the index for the z field
        if z_idx is None:  # just the first time
            for idx, field in enumerate(fields):
                if field.startswith("z"):
                    z_idx = idx
                    break
        complete_fname = f"{folder}/{fname}"

        # Check if the dict for the distance already exists
        z, z_units = get_z_suffix(fields[z_idx])
        z_int = int(z)  # TODO: consider to replace int with str
        if z_int not in polarimetric_sets:  # if not, create it
            polarimetric_sets[z_int] = {}

        # let's fill the dictionary
        if fields[pol_idx] == pol_keys[0]:
            polarimetric_sets[z_int][0] = complete_fname
            polarimetric_sets[z_int]["f"] = z

        elif fields[pol_idx] == pol_keys[1]:
            polarimetric_sets[z_int][1] = complete_fname
            
        elif fields[pol_idx] == pol_keys[2]:
            polarimetric_sets[z_int][2] = complete_fname

        elif fields[pol_idx] == pol_keys[3]:
            polarimetric_sets[z_int][3] = complete_fname

        elif fields[pol_idx] == pol_keys[4]:
            polarimetric_sets[z_int][4] = complete_fname
            
        elif fields[pol_idx] == pol_keys[5]:
            polarimetric_sets[z_int][5] = complete_fname

        elif fields[pol_idx] == pol_keys[6]:
            polarimetric_sets[z_int]["Irr"] = complete_fname

        polarimetric_sets[z_int]["scale"] = z_units
    return polarimetric_sets, beam_name

def get_polarimetric_npz(folder, pol_keys={0:"a0", 1:"a45", 2:"a90",
    3:"a135", 4:"aLev", 5:"aDex"}):
    """Construct the dictionary that the program expects. This method
    allows for a more precise plane determination and is overall more flexible."""
    polarimetric_sets = {}

    fnames = os.listdir(folder)
    # names = []
    # for name in fnames:
    #     if name.endswith(".npz"):
    #         names.append(name)

    beam_name = None

    for name in [n for n in fnames if n.endswith(".npz")]:
        beam_name = name.split("_")[0]
        data = np.load(os.path.join(folder, name), allow_pickle=True)
        z = data["z"]
        scale = data["scale"]
        polarimetric_sets[int(z)] = {}
        polarimetric_sets[int(z)]["scale"] = scale
        for i in range(6):
            polarimetric_sets[int(z)][i] = data[pol_keys[i]]
    return polarimetric_sets, beam_name

def get_z_suffix(z_field):
    """Return the z value and its units."""
    z_unit_options = ["um", "mm", "nm", "lam", ""]
    match = re.search(f"^z([0-9]+)({'|'.join(z_unit_options)})$", z_field)
    if match is None:
        raise ValueError(f"Invalid z field: {z_field}")
    value = match.group(1)
    units = match.group(2)
    scale = (1e3 if units == "mm" else
             1 if units == "um" else
             1e-3 if units == "nm" else
             1/WAVELENGTH_um if units == "lam" else   # FIXME: wavelength in microns is hardcoded !!!!
             1)  # Default to um
    return float(value), scale


def get_polarimetric_names_kavan(folder, ftype="TIFF", pol_keys={0:"LX", 1:"L45",
    2:"LY", 3:"L135", 4:"Q45", 5:"Q135"}):
    """Get the polarimetric image names according to Kavan's naming convention."""
    filenames = os.listdir(folder)
    filenames.sort()
    polarimetric_sets = {}
    for fname in filenames:
        # Try to get the fname and ftype. If not divisible, get out
        try:
            image_name, f_type = fname.split(".")
        except:
            continue

        # Recognize the filetype and bail out if not the correct one
        if f_type != ftype:
            continue
        # Retrieve the necessary information. If not possible, bail out
        try:
            fields = []
            image_info, z = image_name.split("Z")
            fields.append(image_info[:2])
            fields.append(image_info[2:])
            fields.append(z[-4:-2])
            fields.append(z[:-4])
        except:
            continue
        if len(fields) < 4:
            continue # Not a valid filename!

        beam_name = fields[0]

        # Check if the dict for the distance already exists
        z = int(fields[-1])
        complete_fname = f"{folder}/{fname}"
        if z not in polarimetric_sets:
            polarimetric_sets[z] = {}
            polarimetric_sets[z]["scale"] = 1 if fields[2] == "mm" else 1e-3
        if fields[1] == pol_keys[0]:
            polarimetric_sets[z][0] = complete_fname
            polarimetric_sets[z]["f"] = float(0)

        elif fields[1] == pol_keys[1]:
            polarimetric_sets[z][1] = complete_fname
            
        elif fields[1] == pol_keys[2]:
            polarimetric_sets[z][2] = complete_fname

        elif fields[1] == pol_keys[3]:
            polarimetric_sets[z][3] = complete_fname

        elif fields[1] == pol_keys[4]:
            polarimetric_sets[z][4] = complete_fname
            
        elif fields[1] == pol_keys[5]:
            polarimetric_sets[z][5] = complete_fname
    return polarimetric_sets, beam_name
    
if __name__ == "__main__":
    folder = "."
    pol_sets, beam_name = get_polarimetric_npz(folder)
    print(beam_name)
    print(pol_sets[0])
