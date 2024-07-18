# Phase retriever
A Python GUI for the implementation of the phase retrieval algorithm, based on 
Fineup's backpropagation. 

## Installation and run

* Create a new environ (optional)

    ```
    conda create -n phase_ret_env python pip
    conda activate phase_ret_env
    ```
    Alternatively, you can use virtualenv, if desired.


* Install via pip+GitHub

    ```
    pip install https://github.com/WavefrontEngUB/phase-retriever/archive/refs/heads/main.zip
    ```

    It can take a while to build the wxPython wheel.

    If some error is triggered during the installation, please check the Troubleshooting section below.
     
* Finally, to run the program, use:

    ```
    python -m phase_retriever
    ```
    Enjoy!

## Usage

Since this program includes a GUI, it is not required to add any arguments to the command line.
However, there are some options that can be used to download the test dataset, 
launch the program with a preloaded test dataset or run the test suite.

If the program is run with the -help flag, it provides basic help: 
```
$ python -m phase_retriever -help

Description: Phase retriever is a GUI powered software to retrieve the phase of 
a highly focused electromagnetic field. The program requires the six polarimetric 
images recorded at two planes perpendical to the optical axis and separated some distance nearby the focus.
It also calculates the electric field longitudinal component. 

usage: python -m phase_retriever [test|demo|download_data=<path>] [-h|-help]

Options:
  download_data:  Downloads the test dataset on the current directory or 
                  in the specified in the optional <path>.
  demo:           Launches the program with the preloaded test dataset.  
                  *It can be combined with download_data.*
  test:           Runs the unit test suite.

  -h, -help:      Show this help message.

```

#### Data

The phase retrieval algorithm requires 12 polarimetric images, six for two z-planes.

You can get the test dataset by running the following command
    

    python -m phase_retriever download_data

It will create a folder named `test_dataset` in the current directory with the images.
The image filenames are in the format `beamName_z<z-plane>_a<polarization>.png`, 
where `<z-plane>` is the z-position of the plane in micrometers
(notice that absolute positions are not required, just the relative distances between planes).
The `<polarization>` is related to the polarization of the analyzer, and it can be 
`0`, `45`, `90`, `135`, `Dex`, `Lev`.

The test dataset looks like this
```
└───phase_retriever_dataset
        testRad.json            # Config file (to be able to recall the default parameters)
        testRad_retrieved.npz   # Already retrieved file (for testing)
        testRad_z0_a0.png       # Vertical polarization, first plane
        testRad_z0_a135.png     # Antidiagonal polarization, first plane
        testRad_z0_a45.png      # Diagonal polarization, first plane
        testRad_z0_a90.png      # Horizontal polarization, first plane
        testRad_z0_aDex.png     # Circular Right polarization, first plane
        testRad_z0_aLev.png     # Circular Left polarization, first plane
        testRad_z2_a0.png       # Vertical polarization, second plane (2 microns behind)
        testRad_z2_a135.png     # Antidiagonal polarization, second plane
        testRad_z2_a45.png      # Diagonal polarization, second plane
        testRad_z2_a90.png      # Horizontal polarization, second plane
        testRad_z2_aDex.png     # Circular Right polarization, second plane
        testRad_z2_aLev.png     # Circular Left polarization, second plane

```


#### GUI explanation via demo

Run

    python -m phase_retriever demo

to see a demonstration of the program.

The GUI is divided into two panels: the config panel (left) and the main panel (right).

Once the GUI is opened, the first step is to load the images. Click on `Search directory`
button on the config panel and select the folder with the polarimetric images.
Notice that the images might not be shown in the folder dialog (Windows issue),  but the program should find they are there.
Then, the total irradiance should be shown in the main panel.

You can set the specific parameters of your data on the config panel.
The default ones are appropriate for the test dataset.

Click on **`Autoadjust`** to find the appropriated bandwidth.
Then, three more tabs should be created in the main panel: cropped irradiance, 
Cropped Stokes and Spectrum. This last one is active now, but you can explore the rest.
The bandwidth is overlaid in yellow on the spectrum image.

Click on **`Begin retrieval`** to start the retrieval process.
Now, the `MSE` tab is created to plot the progress (it gets stuck at the beginning of the process).
Finally, the `Results` tab is created and filled with the three complex components 
of the field.

You can `Save` the configuration parameters, `Load` a previous configuration, and 
**`Export`** the results in the `File` menu.

The configuration is stored in a JSON file with the parameters.
Find in the test dataset folder an example of the test dataset.

The export file is a `.npz`  NumPy file with the three complex field components,
as `Ex`, `Ey` and `Ez` with `dtype=np.complex128`.


#### Tests

Run

    python -m phase_retriever test

to run the test suite.

At the end, you can compare the retrieved field with the one stored in the test dataset, 
considered as the ground truth.

## Troubleshooting

We have detected some troubles with wyPython on Linux distributions (and also on MacOs X). It is usually fixed just by installing the next prerequisites before installing this `phase-retriever` module.

Be sure that the target environment is activated before installing the prerequisites.

    pip install wheel
    sudo apt update
    sudo apt-get install build-essential libgtk-3-dev python3-tk  # gcc g++
    sudo apt-get install upgrade

Then, you can install `phase-retriever` in the current environment as described in the first section.
