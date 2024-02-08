# nibLib

Nib simulation library for font editors (well, Glyphs and RoboFont at the moment).

## Available nib shapes

* Rectangle
* Oval
* Superellipse

## Screenshots

<img src="images/rectangle-rgb.png" width="800" height="400" alt="">

<img src="images/superellipse.png" width="800" height="400" alt="">

## Installation

### Glyphs

#### User Installation

Use the provided `NibSimulator.glyphsReporter.zip` from the [latest release](https://github.com/jenskutilek/nibLib/releases). Unzip, then double-click the `NibSimulator.glyphsReporter` file to install it into Glyphs.

#### Developer Installation

You need to install the required Python modules, as the `NibSimulator.glyphsReporter` in the repository does not contain them:

1. Clone or download the git repository
2. In the repository, use the pip command corresponding to your major and minor Python
   version that you use in Glyphs to install nibLib and its dependencies, e.g. if you
   have Python 3.11.8:

```bash
pip3.11 install --user .
```

Or install them into the Glyphs scripts folder:

```bash
pip3.11 install -t ~/Library/Application\ Support/Glyphs\ 3/Scripts/site-packages .
```

### RoboFont

Danger: The RoboFont version used to work, but I haven't tested it myself recently after
changing lots of stuff in the code.

Put the folder `nibLib` from `lib` somewhere RoboFont can import Python modules from,
e.g. `~/Library/Application Support/RoboFont/external_packages`.

You also need to install the required package `beziers`, and some more packages that 
RoboFont already provides: `defconAppKit`, `fontPens`, and `fontTools`.

Open the script `NibLibRF.py` in RoboFont’s macro panel and run it. NibLib will use any
path in the bottom-most layer as a guide path.

## Known bugs

* This is a development version, everything may be broken.
* The "Ellipse" nib is broken, but you can use the Superellipse with a superness setting
  of 2.0 instead.
