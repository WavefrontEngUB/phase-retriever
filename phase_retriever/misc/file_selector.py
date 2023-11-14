#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FILE SELECTOR FOR POLARIMETRIC IMAGES
    A polarimetric image picker to return a filename-agnostic
set of properly corrected polarimetric images.
"""
import os
import sys

def get_polarimetric_names(folder, pol_keys={0:"a0", 1:"a45", 2:"a90",
    3:"a135", 4:"aLev", 5:"aDex"}, ftype="png"):
    """Return a set of dictionaries containing the set of polarimetric images
    for each family of measurements. Assumes a filename of the form

        {beam type}_{z location}_{polarimetric image}.{file type}

    (David's naming convention)
    """
    filenames = os.listdir(folder)
    filenames.sort()
    polarimetric_sets = {}
    pol_idx = None  # just an initialization
    z_idx = None  # just an initialization
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

        if len(fields) < 3:
            continue  # Not a valid filename!

        # Get the index for the analyzer field
        if pol_idx is None:
            for idx, field in enumerate(fields):
                if field in pol_keys.values():
                    pol_idx = idx
                    break

        # Get the index for the z field
        if z_idx is None:
            for idx, field in enumerate(fields):
                if field.startswith("z"):
                    z_idx = idx
                    break

        # Check if the dict for the distance already exists
        z = int(fields[z_idx][1:])
        complete_fname = f"{folder}/{fname}"
        if z not in polarimetric_sets:
            polarimetric_sets[z] = {}
        if fields[pol_idx] == pol_keys[0]:
            polarimetric_sets[z][0] = complete_fname
            polarimetric_sets[z]["f"] = float(fields[z_idx][1:])

        elif fields[pol_idx] == pol_keys[1]:
            polarimetric_sets[z][1] = complete_fname
            
        elif fields[pol_idx] == pol_keys[2]:
            polarimetric_sets[z][2] = complete_fname

        elif fields[pol_idx] == pol_keys[3]:
            polarimetric_sets[z][3] = complete_fname

        elif fields[pol_idx] == pol_keys[4]:
            polarimetric_sets[z][4] = complete_fname
            
        elif fields[pol_idx] == pol_keys[5]:
            polarimetric_sets[z][5] = complete_fname
        polarimetric_sets[z]["scale"] = 1e-3
    return polarimetric_sets

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
    return polarimetric_sets
    
if __name__ == "__main__":
    folder = "NA_0.5/GR"
    pol_sets = get_polarimetric_names_kavan(folder)
    print(pol_sets[0])
