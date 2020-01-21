# nibLib

Nib simulation library for font editors (well, RoboFont at the moment).

## Available nib shapes

* Rectangle
* Oval
* Superellipse

## Screenshots

<img src="images/rectangle-rgb.png" width="800" height="400" alt="">

<img src="images/superellipse.png" width="800" height="400" alt="">

## Installation

### RoboFont

Put the folder `nibLib` from `lib` somewhere RoboFont can import Python modules from, e.g. `~/Library/Application Support/RoboFont/external_packages`.

Open the script `NibLibRF.py` in RoboFont’s macro panel and run it. NibLib will use any path in the bottom-most layer as a guide path.

## Known bugs

* This is a development version, everything may be broken.
* Only the rectangular nib will trace outlines using lines and curves, the other modes currently only produce line segments.
