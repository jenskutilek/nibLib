#!/bin/sh

PYTHON=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11
PLUGIN=NibSimulator.glyphsReporter
RESOURCES=Contents/Resources

# Make sure the target folder exists
mkdir -p ./dist

cp -R $PLUGIN ./dist/

# Install dependencies
$PYTHON -m pip install -t "./dist/$PLUGIN/$RESOURCES" .
