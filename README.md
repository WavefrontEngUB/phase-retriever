# Phase retriever
Phase retrieval GUI to fully characterize highly focused beams via the Fineup algorithm

A full description of the method can be found at the next publication:

> ## Characterization of highly focused vector fields using phase retrieval: a practical guide
>
> ***Applied Optics***, Vol. 64, Issue 4, pp. 938-943 (2025)
> 
> <sup>DOI: [**10.1364/AO.544562**](https://doi.org/10.1364/AO.544562) ; Received: **14 Oct 2024** ; Accepted: 12 Dec 2024 ; Posted: 28 Jan 2025</sup>
>
> **David Maluenda Niubó<sup>1,2</sup>, Marcos Pérez-Aviñoa<sup>1</sup>, Rosario Martínez-Herrero<sup>3</sup>, and Artur Carnicer<sup>1</sup>**
>
> *<sup>1</sup>Universitat de Barcelona (UB), Facultat de Física, Departament de Física aplicada, Martí i Franquès 1, 08028, Barcelona, Spain.*
>
> *<sup>2</sup>Institut de Nanociència i Nanotecnologia de la Universitat de Barcelona (IN2UB), 08028 Barcelona, Spain.*
>
> *<sup>3</sup>Universidad Complutense de Madrid (UCM), Departamento de Óptica, Ciudad Universitaria, 28040, Madrid, Spain.*
>
> **Abstract**: A precise knowledge of the polarization state of light is crucial in technologies that involve the generation and application of structured light fields. The implementation of efficient methods aimed at determining and characterizing polarization states and, more importantly, at any spatial location at a low expense is thus mandatory. Here, we introduce a new characterization method, which relies on a rather convenient description of electric fields without neglecting their three-dimensional nature. This method is indeed particularly suitable for highly focused fields, which exhibit important polarization contributions along their propagation direction in the neighborhood of the focal region, i.e., contributions out of the planes transverse to the optical axis, conventionally used to specify the polarization state of these fields. As it is shown, the method allows us to extract information about the three field components at relatively low computational and experimental costs. Furthermore, it also allows to characterize the polarization state of the field in a rather simple manner. To check the feasibility and reliability of the method, we have determined both analytically and experimentally the local polarization states for a series of benchmark input fields with it, finding an excellent agreement between theory and experiment.

## Installation and run

* Create a new environ (optional)

     - Using conda:
        ```
        conda create -n phase_ret_env python pip
        conda activate phase_ret_env
        ```
     - Or, **alternatively**, using virtualenv:
        ```
        mkdir my_phase_retriever_dir  # optional
        cd my_phase_retriever_dir     # optional
        python -m venv phase_retriever_env
        .\phase_retriever_env\Scripts\activate  # If Windows
        source phase_retriever_env/bin/activate phase_retriever_env  # If linux
        ```

* Install via pip+GitHub

    ```
    pip install https://github.com/WavefrontEngUB/phase-retriever/archive/refs/heads/main.zip
    ```

    It can take a while to build the wxPython wheel.

    If some error is triggered during the installation, 
    please check the Troubleshooting section below.
     

* Finally, to run the program, just launch:

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
images recorded at two planes perpendical to the optical axis and separated some        
distance nearby the focus. It also calculates the electric field longitudinal component.

usage: python -m phase_retriever [path=<path>|get_test_data=<path>|demo|test] [-h|--help]
                                                                                         
Options:                                                                                 
  path:           Opens the program with the dataset in the specified path.              
  get_test_data:  Copies the test dataset on the current directory                       
                  or in the specified optional <path>.                            
  demo=N:         Launches the program with a test dataset already loaded.
                  N: 1 or 'empty' -> Simulated data ; 2 -> Experimental data.
                  *It can be combined with get_test_data.*
  test:           Runs the unit test suite.

  -h, --help:     Shows this help message.

```

#### Data

The phase retrieval algorithm requires 12 polarimetric images, six for two z-planes.
In addition, the total irradiance image at these two planes can be added in order to 
automatically align the polarimetric images.

You can get the test dataset by running the following command

    python -m phase_retriever get_test_data

It will create a folder named `phase_retriever_dataset` in the current directory
with two subdirectories: `simulated` and `experimental`. Both contain examples of
the polarimetric images.

The image filenames are in the format `beamName_z<z-plane>_a<polarization>.png`,
where `<z-plane>` is the z-position of the plane in micrometers 
(notice that absolute positions are not required, just the relative distances between planes).
The `<polarization>` is related to the polarization kind of the analyzer, and it can be 
`0`, `45`, `90`, `135`, `Dex`, `Lev`; for the total irradiance images the `Irr` 
suffix is used.

The `phase_retriever_dataset` looks like this and it is what is expected:
```
└───phase_retriever_dataset                
    ├───experimental       # Some experimental data to play with
    │   ├───20221026.json                  # [Optional] Config file (to set specific default parameters)
    │   ├───20221026_retrieved.npz         # [Not requiered] Already retrieved file (just for testing)
    │   ├───20221026_s2_pRad_a0_z0.png     # Vertical polarization, first plane
    │   ├───20221026_s2_pRad_a0_z2.png     # Vertical polarization, second plane (2 microns behind)
    │   ├───20221026_s2_pRad_a135_z0.png   # Antidiagonal polarization, first plane
    │   ├───20221026_s2_pRad_a135_z2.png   # Antidiagonal polarization, second plane
    │   ├───20221026_s2_pRad_a45_z0.png    # Diagonal polarization, first plane
    │   ├───20221026_s2_pRad_a45_z2.png    # Diagonal polarization, second plane
    │   ├───20221026_s2_pRad_a90_z0.png    # Horizontal polarization, first plane  
    │   ├───20221026_s2_pRad_a90_z2.png    # Horizontal polarization, second plane
    │   ├───20221026_s2_pRad_aDex_z0.png   # Circular Right polarization, first plane
    │   ├───20221026_s2_pRad_aDex_z2.png   # Circular Right polarization, second plane
    │   ├───20221026_s2_pRad_aIrr_z0.png   # [Optional] Total irradiance, first plane
    │   ├───20221026_s2_pRad_aIrr_z2.png   # [Optional] Total irradiance, second plane
    │   ├───20221026_s2_pRad_aLev_z0.png   # Circular Left polarization, first plane
    │   └───20221026_s2_pRad_aLev_z2.png   # Circular Left polarization, second plane
    │
    └───simulated       # Some simulated data to play with  (same structure)
        ├───testRad.json
        ├───testRad_retrieved.npz
        ├───testRad_z0_a0.png
        │      ...
        └───testRad_z2_aLev.png
```

Since all different images are taken in different time slots and
they probably are taken using different analyzers
(just a polarizer, a quarter waveplate plus a polarizer, nothing), and
any other reasons (like laser fluctuations, etc.), the images can be
slightly under or overexposed in comparison with the others.
To avoid this issue that can affect the Stokes parameters calculation,
the program includes a feature to mitigate it.
It is able to recognize an auxiliary spotlight
from a second beam directly drove from the laser,
without passing through the analysers, even skipping the microscope stage.
Check the paper for more details about this feature [missing cite].


#### GUI explanation via demos

Run

    python -m phase_retriever demo=1

to see a demonstration of the program under simulated data.

or 

    python -m phase_retriever demo=2

to see a demonstration of the program under experimental data.

The GUI is divided into two panels: the config panel (left) and the main panel (right).

Once the GUI is opened, the first step is to load the images. If you are running a demo 
or a valid path is passed in the command argument, data will be automatically loaded. 
If not, click on `Search directory` button on the config panel and select the 
folder with the polarimetric images.
Notice that the images might not be shown in the folder dialog (Windows issue), 
but the program should find them there.
Then, the total irradiance calculated using the polarimetric images is 
shown in the main panel on the `Irradiance (full size)` tab, while the ROI of the Stokes 
images are shown in the `Cropped Stokes`.

You can set the specific parameters of your data on the config panel.
The default ones are appropriate for the test dataset.

Two rectangles will be overlaid on the total irradiance image.
The green one shows the region of interest (ROI) where all calculation are done, 
and the red one shows the region where the auxiliary beam is located.
You can fine adjust the main and auxiliary beam ROIs by modifying the parameters 
on the config panel. Also, you can swap that ROIs just by clicking on the 
**`Swap beams`** button. Alternatively, you can remove the auxiliary beam's ROI 
just by setting the Auxiliary size to 0.
(Find more details about why auxiliary beam is interesting for in 
the data section above or in the paper [missing cite])

Polarimetric images can be missaligned due to the analyzers rotation or any other reason.
To correct this, click on **`Align images`**. 
The program will find the cross correlation between every polarimetric image 
with the experimental total irradiance image.
Therefore, this option is only available if the 
experimental total irradiance images are included in the dataset.

Click on **`Check bandwidth`** to find the appropriated bandwidth, 
if not manually set before, and to check if that bandwidth is correct.
Then, the `Spectrum` tab is created and actived now, 
where the bandwidth is overlaid in yellow on the spectrum image.

Click on **`Begin retrieval`** to start the retrieval process.
Now, the `MSE` tab is created to plot the progress (it gets stuck at the beginning of the process).
Finally, the `Results` tab is created and filled with the three complex components 
of the field.

Finally, you can **`Export results`** in a `.npz`  NumPy file where
the three complex field components are under keys `Ex`, `Ey` and `Ez`
with `dtype=np.complex128` and `shape=(mainROI,mainROI)`.


In addition, you can `Save` the configuration parameters and
`Load` a previous configuration.
Where the configuration is stored in a JSON file with the parameters.
Find examples within the test datasets.
When a JSON file is in a dataset, the program will load it automatically
with the images.


#### Tests

Run

    python -m phase_retriever test

to run the unit test suite.

At the end, you can compare the retrieved field with the one stored in the test dataset, 
considered as the ground truth.

## Troubleshooting...


#### ...while installaling

We have detected some troubles with wyPython on Linux distributions (and also on MacOs X). It is usually fixed just by installing the next prerequisites before installing this `phase-retriever` module.

Be sure that the target environment is activated before installing the prerequisites.

    pip install wheel
    sudo apt update
    sudo apt-get install build-essential libgtk-3-dev python3-tk  # gcc g++
    sudo apt-get install upgrade

Then, you can install `phase-retriever` in the current environment as described in the first section.

#### ...in data management

If polarimetric images are not well aligned after pressing button `Align images`, an alternative has to be found. A good but tedious option is to manually align the images prior to loading them in the program.


#### ...while running

If results deviate from your expected outcomes or clearly show artifacts, it is likely due to an incorrect bandwidth setting. Therefore, manually adjust the bandwidth in the configuration pane, ensuring that the shaded area aligns with the signal and avoids noisy frequencies, in the Spectrum tab.
