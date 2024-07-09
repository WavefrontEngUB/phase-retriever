# Phase retriever
A python GUI for the implementation of a phase retrieval algorithm, based on 
Fineup's backpropagation algorithm. 

## Installation and run

* Create a new environ (optional)

    ```
    conda create -n phase_ret_env python pip
    conda activate phase_ret_env
    ```
    alternativelly, you can use virtualenv if desired.


* Install via pip+github

    ```
    pip install https://github.com/WavefrontEngUB/phase-retriever/archive/refs/heads/main.zip
    ```
     
* Run it just by

    ```
    python -m phase_retriever

    and enjoy.

## Usage

Since this program is a GUI, it is not needed to add any argument to the command line.
However, there are some options that can be used to download the test dataset, 
run the test suite or launch the program with the test dataset already loaded.

Find below the help message
```
$ python -m phase_retriever -help

Description: Phase retriever is a GUI powered software to retrieve the fase of 
a highly focused electromagnetic field, by taking as input two recording 
planes separated some distance nearby the focus. It also reconstruct the 
longitudinal component. To do so, it is necessary to provide polarimetric 
images of both z-planes.

usage: python -m phase_retriever [test|demo|download_data=<path>] [-h|-help]

Options:
  download_data:  Downloads the test dataset on the current directory or 
                  in the specified in the optional <path>.
  demo:           Launches the program with a test dataset already loaded. 
                  *It can be combined with download_data.*
  test:           Run the test suite.

  -h, -help:      Show this help message.

```

### Data

The phase retrieval algorithm requires 12 polarimetric images, six for two z-planes.

You can get the test dataset by running the following command
    

    python -m phase_retriever download_data

it will create a folder named `test_dataset` in the current directory with the images.
The image names are in the format `beamName_z<z-plane>_a<polarization>.png`, 
where `<z-plane>` is the z-position of the plane in microns
(notice that absolute positions are not required, just relative between planes).
The `<polarization>` is the polarization analyzer and it can be 
`0`, `45`, `90`, `135`, `Dex`, `Lev`.

The test dataset looks like this
```
└───phase_retriever_dataset
        testRad_retrieved.npz
        testRad_z0_a0.png
        testRad_z0_a135.png
        testRad_z0_a45.png
        testRad_z0_a90.png
        testRad_z0_aDex.png
        testRad_z0_aLev.png
        testRad_z2_a0.png
        testRad_z2_a135.png
        testRad_z2_a45.png
        testRad_z2_a90.png
        testRad_z2_aDex.png
        testRad_z2_aLev.png

```


### GUI

Run

    python -m phase_retriever demo

to see a demonstration of the program.

The GUI is divided in two panels, the config panel (left) and the main panel (right).

Once the GUI is opened, first step is to load the images. Click on `Search directory`
button on the config panel and select the folder with the polarimetric images.
Notice that the images might not been shown in the folder dialog (Windows issue), 
but the program should find they there.
Then, the total irradiance should be shown in the main panel.

You can set the specific parameters of your data on the config panel.
The default ones are correct for the test dataset.

Click on `Autoadjust` to find the appropriated bandwidth.
Then, three more tab should be created in the main panel: Cropped irradiance, 
Cropped Stokes and Spectrum. This last one is active now, but you can explore the rest.
The bandwidth is overlaid in yellow on the spectrum to check that it is appropriated.

Click on `Begin retrieval` to start the retrieval process.
Now, the `MSE` tab is created to plot the progress (it gets a bit stuck at the beginning).
Finally, the `Results` tab is created and filled with the three complex components 
of the field.

You can `Save` the configuration parameters, `Load` a previos configuration and 
**`Export`** the results in the `File` menu.

The configuration file is a JSON file with the parameters.
Find in the test dataset folder an example for the test dataset.

The export file is a `.npz`  Numpy file with the three complex field components,
as `Ex`, `Ey` and `Ez` with `dtype=np.complex128`.


### Tests

Run

    python -m phase_retriever test

to run the test suite.

At the end, you can compare the retrieved field with the one stored in the test dataset.
